from scripts.helpers import smart_get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, approve_transfer
from brownie import network, accounts, config, AstroSwapExchange, AstroSwapFactory
from brownie.network.contract import Contract
from scripts.runAstroSwap import deploy_erc20, seed_invest, exchange_from_address

fee = 400

def deploy_factory_contract():
    account = smart_get_account(1)
    print("account:", account)
    factory = AstroSwapFactory.deploy(
        fee, 
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    print("AstroSwapFactory@", factory)
    return factory

def deploy_new_exchange(factoryAddress, tokenAddress):
    account = smart_get_account(1)
    print("account:", account)
    forgeTx = factoryAddress.addTokenExchange(tokenAddress, {'from': account})
    forgeTx.wait(1)
    print(forgeTx.events["TokenExchangeAdded"][0])
    tokenExchangeAddress = forgeTx.events["TokenExchangeAdded"][0]["tokenExchange"]
    print("TokenExchangeAddress:", tokenExchangeAddress)
    return tokenExchangeAddress

def get_factory_info(factory = None):
    if factory == None: factory = AstroSwapFactory[-1]
    print("Address:", factory.address, "Exchange count:", factory.exchangeCount())

def tokenToToken(token1, token2, amount, factoryAddress):
    account = smart_get_account(1)
    print("account:", account)
    token1Exchange = factoryAddress.convertTokenToExchange(token1)
    exchange1 = exchange_from_address(token1Exchange)
    token1ToToken2Tx = exchange1.tokenToToken(account, token2, amount, 0, {'from': account})
    token1ToToken2Tx.wait(1)
    print("TTT Events:", token1ToToken2Tx.events)

def tokenToTokenQuote(token1, token2, amount, factoryAddress):
    account = smart_get_account(1)
    print("account:", account)
    token1Exchange = factoryAddress.convertTokenToExchange(token1)
    print("token1Exchange:", token1Exchange)
    exchange1 = exchange_from_address(token1Exchange)
    print("exchange1:", exchange1)
    quote = exchange1.getTokenToTokenQuote(amount, token2)
    print("TTT Quote:", quote)
    return quote

def main():
    erc20 = deploy_erc20()
    factory = deploy_factory_contract()
    tokenExchangeAddress = deploy_new_exchange(factory, erc20)
    erc20_2 = deploy_erc20()
    tokenExchangeAddress_2 = deploy_new_exchange(factory, erc20_2)
    approve_transfer(erc20.address, tokenExchangeAddress, smart_get_account(1), 100)
    approve_transfer(erc20_2.address, tokenExchangeAddress_2, smart_get_account(1), 100)
    seed_invest(100, 100, exchange=exchange_from_address(tokenExchangeAddress))
    seed_invest(100, 100, exchange=exchange_from_address(tokenExchangeAddress_2))
    print("Seed investments complete")
    approve_transfer(erc20, tokenExchangeAddress, smart_get_account(1), 20)
    tokenToTokenQuote(erc20, erc20_2, 20, factory)
    tokenToToken(erc20, erc20_2, 20, factory)
