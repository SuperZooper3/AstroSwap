from scripts.helpers import smart_get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from brownie import network, accounts, config, AstroSwapExchange, MockERC20
from brownie.network.contract import Contract

fee = 400

tokenCounter = 0
tokens = []

def exchange_from_address(address):
    exchangeAbi = AstroSwapExchange.abi
    return Contract.from_abi("AstroSwapExchange", address, exchangeAbi)

def deploy_erc20():
    global tokenCounter
    account = smart_get_account(1)
    print("account:", account)
    erc20 = MockERC20.deploy(
        str(tokenCounter),
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    print("ERC20@", erc20)
    tokenCounter += 1
    tokens.append(erc20)
    return erc20

def deploy_exchage_contract(tokenAddress):
    account = smart_get_account(1)
    print("account:", account)
    exchange = AstroSwapExchange.deploy(
        tokenAddress,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    print("AstroSwapExchage@", exchange)
    return exchange

def get_exchange_info(exchange = None):
    if exchange == None: exchange = AstroSwapExchange[-1]
    print("Address:", exchange.address, "Token:", exchange.token() ,"Fee:", exchange.feeAmmount(), "ETH/ERC20:", exchange.ethPool(), "/", exchange.tokenPool(), "Invariant:", exchange.invariant())

def seed_invest(eth, token, exchange = None):
    if exchange == None: exchange = AstroSwapExchange[-1]
    account = smart_get_account(1)
    # Allow the contract to transfer 100 of our tokens
    approveTx = tokens[0].approve(exchange.address, token, {'from': account})
    approveTx.wait(1)
    print("account:", account)
    investTx = exchange.seedInvest(token, {'from': account, 'value': eth})
    investTx.wait(1)
    print("Seeded invest", investTx.events)

def buy_tokens(eth, min_tokens=0):
    exchange = AstroSwapExchange[-1]
    account = smart_get_account(1)
    buyTx = exchange.ethToToken(account.address, min_tokens, {'from': account, 'value': eth})
    buyTx.wait(1)
    print("Bought tokens", buyTx.events)

def buy_eth(token, min_eth=0):
    exchange = AstroSwapExchange[-1]
    account = smart_get_account(1)
    # Need to authorise the transfer of tokens
    approveTx = tokens[0].approve(exchange.address, token, {'from': account})
    approveTx.wait(1)
    buyTx = exchange.tokenToEth(account.address,token, min_eth, {'from': account})
    buyTx.wait(1)
    print("Bought eth", buyTx.events)

def main():
    deploy_erc20()
    deploy_exchage_contract(tokens[0].address)
    get_exchange_info()
    seed_invest(1000, 50000)
    get_exchange_info()
    buy_tokens(10000)
    get_exchange_info()