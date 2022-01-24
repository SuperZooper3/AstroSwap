from scripts.helpers import smart_get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from scripts.runAstroSwap import deploy_erc20 
from brownie import network, accounts, config, AstroSwapExchange, MockERC20
import pytest

# All the exchange tests
# - Deploy an exchange contract
# - Seed invest properly
# - Seed invest just tokens (should fail)
# - Seed invest just ETH (should fail)
# - Seed invest nothing (not going to fail since it's just dumb to do)
# - Seed invest without authorising the ERC20 transfer (should fail)
# - Invest properly
# - Invest just ETH throught not authorising (should fail)
# - Invest nothing (should fail)
# - Invest half as much as what was seeded
# - Invest 2x as much as what was seeded
# - Invest a random amount 
# - Invest while only authroising half of the ERC20 transfer (should fail)
# - Try calling ethToTokenPrivate (should fail)
# - Try calling tokenToEthPrivate (should fail)
# - Call ethToToken with a 0 min
# - Call ethToToken with min > expected (should fail)
# - Call ethToToken with min < expected
# - Try calling ethToToken without seeding (should fail)
# - Call tokenToEth with a 0 min
# - Call tokenToEth with min > expected (should fail)
# - Call tokenToEth with min < expected
# - Try calling tokenToEth without seeding (should fail)

fee = 400

def test_exchange_deploy():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    # Act
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    print("AstroSwapExchage@", exchange)
    # Assert
    assert AstroSwapExchange[-1] != "0x0000000000000000000000000000000000000000"

def test_exchange_seed_invest_properly():
    # Going with an seed rate of 100 tokens for 1 ETH
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 100*10**18, {'from': account})
    approveTx.wait(1)
    # Act
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    # Assert
    assert seedTx.events["Investment"]["sharesPurchased"] == 10000
    print(exchange.ethPool())
    assert exchange.ethPool() == 1*10**18
    assert exchange.tokenPool() == 100*10**18
    assert exchange.totalShares() == 10000
    assert exchange.invariant() == exchange.ethPool() * exchange.tokenPool()

def test_exchange_seed_invest_just_tokens():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 100*10**18, {'from': account})
    approveTx.wait(1)
    # Act & Assert
    with pytest.raises(Exception):
        seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 0})
        seedTx.wait(1)
    
def test_exchange_seed_invest_just_eth():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    # Act & Assert
    with pytest.raises(Exception):
        seedTx = exchange.seedInvest(0, {'from': account, 'value': 1*10**18})
        seedTx.wait(1)

def test_exchange_seed_invest_nothing():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    # Act & Assert
    with pytest.raises(Exception):
        seedTx = exchange.seedInvest(0, {'from': account, 'value': 0})
        seedTx.wait(1)

def test_exchange_seed_invest_without_authorising_erc20_transfer():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    # Act & Assert
    with pytest.raises(Exception):
        seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
        seedTx.wait(1)

def test_exchange_invest_properly():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 200*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    # Act
    investTx = exchange.invest({'from': account, 'value': 1*10**18})
    investTx.wait(1)
    # Assert
    assert investTx.events["Investment"]["sharesPurchased"] == 10000
    assert exchange.ethPool() == 2*10**18
    assert exchange.tokenPool() == 200*10**18
    assert exchange.totalShares() == 20000
    assert exchange.invariant() == exchange.ethPool() * exchange.tokenPool()

def test_exchange_invest_just_eth():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 100*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    # Act & Assert
    with pytest.raises(Exception): # Fails because we only authorize transfer of tokens for the seeding
        investTx = exchange.invest({'from': account, 'value': 1*10**18})
        investTx.wait(1)

def test_exchange_invest_nothing():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 200*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    # Act
    investTx = exchange.invest({'from': account, 'value': 0})
    investTx.wait(1)
    # Assert
    assert investTx.events["Investment"]["sharesPurchased"] == 0
        

def test_exchange_invest_half():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 150*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    # Act
    investTx = exchange.invest({'from': account, 'value': 0.5*10**18})
    investTx.wait(1)
    # Assert
    print(investTx.events)
    assert investTx.events["Investment"]["sharesPurchased"] == 5000
    assert exchange.ethPool() == 1.5*10**18
    assert exchange.tokenPool() == 150*10**18
    assert exchange.totalShares() == 15000
    assert exchange.invariant() == exchange.ethPool() * exchange.tokenPool()

def test_exchange_invest_two_x():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 300*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    # Act
    investTx = exchange.invest({'from': account, 'value': 2*10**18})
    investTx.wait(1)
    # Assert
    assert investTx.events["Investment"]["sharesPurchased"] == 20000
    assert exchange.ethPool() == 3*10**18
    assert exchange.tokenPool() == 300*10**18
    assert exchange.totalShares() == 30000
    assert exchange.invariant() == exchange.ethPool() * exchange.tokenPool()