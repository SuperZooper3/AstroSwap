from brownie import network, accounts, config, Contract
from brownie.network import contract
from math import floor

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development","ganache-local"]
FORKED = ["mainnet-fork","mainnet-fork-dev"]

def get_account(index = 0, id = None): # Automaticaly gets a good account
    if id != None:
        return accounts.load(id)
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS or network.show_active() in FORKED:
        return accounts[index]
    return accounts.load("test1")

def smart_get_account(index):
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[index]
    return accounts.load("test"+str(index+1))
    
def calculate_liquidity_pool_output(fromPool, toPool, amount, fee):
    invariant = fromPool * toPool
    feesTaken = floor(amount / fee)
    print(feesTaken, amount / fee)
    newPool = fromPool - feesTaken + amount
    newToPool = floor(invariant / newPool + 1)
    print(newPool, newToPool)
    paid = toPool - newToPool
    return paid

