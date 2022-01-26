from scripts.helpers import smart_get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from brownie import network, accounts, config, AstroSwapExchange, AstroSwapFactory, MockERC20
from scripts.runAstroSwap import deploy_erc20

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

def main():
    erc20 = deploy_erc20()
    factory = deploy_factory_contract()
    tokenExchangeAddress = deploy_new_exchange(factory, erc20)
    get_factory_info()
    print("TTE:", factory.convertTokenToExchange(erc20.address))
    print("ETT:", factory.convertExchangeToToken(tokenExchangeAddress))