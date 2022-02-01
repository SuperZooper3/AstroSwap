from scripts.helpers import smart_get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, approve_transfer
from scripts.runAstroSwap import deploy_erc20
from brownie import network, accounts, config, MiniSwap, MockERC20
from brownie.network.contract import Contract

fee = 400

def deploy_mini_swap(fee):
    account = smart_get_account(1)
    print("account:", account)
    miniSwap = MiniSwap.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    print("MiniSwap@", miniSwap)
    return miniSwap

def get_miniswap_info(miniSwap = None):
    if miniSwap == None: miniSwap = MiniSwap[-1]
    print("Address:", miniSwap.address, "Fee:", miniSwap.feeRate(), "Exchange count:", miniSwap.exchangeCount())

def get_miniswap_exchange_info(token, miniSwap = None):
    if miniSwap == None: miniSwap = MiniSwap[-1]
    print("Address:", miniSwap.address, "Exchange:", miniSwap.exchanges(token))

def miniswap_seed(token, miniSwap = None):
    if miniSwap == None: miniSwap = MiniSwap[-1]
    account = smart_get_account(1)
    print("account:", account)
    approve_transfer(token, miniSwap.address, account, 100).wait(1)
    investTx = miniSwap.seedInvest(token, 100, {'from': account, 'value': 100})
    print("Created exchange", investTx.events)

def main():
    deploy_erc20()
    deploy_mini_swap(fee)
    get_miniswap_info()
    get_miniswap_exchange_info(MockERC20[0].address)
    create_miniswap_exchange(MockERC20[0].address)

