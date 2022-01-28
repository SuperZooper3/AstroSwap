from scripts.helpers import smart_get_account
from brownie import network, AstroSwapFactory

def deploy_factory(feeRate):
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(feeRate, {'from': account}, publish_source = config["networks"][network.show_active()].get("verify", False))
    print("AstroSwapFactory@", factory, "Using account", account, "with fee rate", feeRate)
    return factory

def main():
    feeRate = input("Fee rate denominator. EX: 400 is 0.25%: ")
    assert(feeRate > 1, "Fee rate must be greater than 1 (100% fees)")
    deploy_factory(feeRate)