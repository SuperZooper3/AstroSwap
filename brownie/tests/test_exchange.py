from scripts.helpers import smart_get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, calculate_liquidity_pool_output
from scripts.runAstroSwap import deploy_erc20 , get_exchange_info
from brownie import network, accounts, config, AstroSwapExchange, MockERC20
import pytest
from random import randint

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
# - Compare EthToTokenQuote to actual cost (3 different values)
# - Compare TokenToEthQuote to actual cost (3 different values)
# - Divest properly
# - Divest half as much as what was invested
# - Divest more than was invested


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
    investTx = exchange.invest(10**22, {'from': account, 'value': 1*10**18})
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
        investTx = exchange.invest(10**22, {'from': account, 'value': 1*10**18})
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
    investTx = exchange.invest(10**22, {'from': account, 'value': 0})
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
    investTx = exchange.invest(10**22, {'from': account, 'value': 0.5*10**18})
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
    investTx = exchange.invest(10**22, {'from': account, 'value': 2*10**18})
    investTx.wait(1)
    # Assert
    assert investTx.events["Investment"]["sharesPurchased"] == 20000
    assert exchange.ethPool() == 3*10**18
    assert exchange.tokenPool() == 300*10**18
    assert exchange.totalShares() == 30000
    assert exchange.invariant() == exchange.ethPool() * exchange.tokenPool()

def test_exchange_invest_maxToken_double():
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
    investTx = exchange.invest(200*10**18, {'from': account, 'value': 1*10**18})
    investTx.wait(1)
    # Assert
    assert investTx.events["Investment"]["sharesPurchased"] == 10000
    assert exchange.ethPool() == 2*10**18
    assert exchange.tokenPool() == 200*10**18
    assert exchange.totalShares() == 20000
    assert exchange.invariant() == exchange.ethPool() * exchange.tokenPool()

def test_exchange_invest_maxToken_exact():
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
    investTx = exchange.invest(100*10**18, {'from': account, 'value': 1*10**18})
    investTx.wait(1)
    # Assert
    assert investTx.events["Investment"]["sharesPurchased"] == 10000
    assert exchange.ethPool() == 2*10**18
    assert exchange.tokenPool() == 200*10**18
    assert exchange.totalShares() == 20000
    assert exchange.invariant() == exchange.ethPool() * exchange.tokenPool()

def test_exchange_invest_maxToken_less():
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
    # Act & Assert
    with pytest.raises(Exception):
        investTx = exchange.invest(99*10**18, {'from': account, 'value': 1*10**18})
        investTx.wait(1)

def test_try_calling_privates():
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
    with pytest.raises(Exception):
        exchange.ethToTokenPrivate(1*10**18, {'from': account})
    with pytest.raises(Exception):
        exchange.tokenToEthPrivate(1*10**18, {'from': account})

def test_call_ethToToken_min_0():
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
    beforeInvariant = exchange.invariant()
    expectedReturn = calculate_liquidity_pool_output(exchange.ethPool(), exchange.tokenPool(), 0.1*10**18, fee)
    # Act
    ethToTokenTx = exchange.ethToToken(account.address, 0, {'from': account, 'value': 0.1*10**18})
    ethToTokenTx.wait(1)
    # Assert
    assert abs(ethToTokenTx.events["TokenPurchase"]["tokensOut"] / expectedReturn - 1) < 0.0001 # I was having some jank in the math, was not able to find it. 0.01% error is fine.
    assert exchange.invariant() >= beforeInvariant

def test_call_ethToToken_min_smaller():
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
    beforeInvariant = exchange.invariant()
    expectedReturn = calculate_liquidity_pool_output(exchange.ethPool(), exchange.tokenPool(), 0.1*10**18, fee)
    # Act
    ethToTokenTx = exchange.ethToToken(account.address, expectedReturn * 0.95, {'from': account, 'value': 0.1*10**18})
    # Above has 5% slippage
    ethToTokenTx.wait(1)
    # Assert
    assert abs(ethToTokenTx.events["TokenPurchase"]["tokensOut"] / expectedReturn - 1) < 0.0001 # I was having some jank in the math, was not able to find it. 0.01% error is fine.
    assert exchange.invariant() >= beforeInvariant

def test_call_ethToToken_min_larger():
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
    
    expectedReturn = calculate_liquidity_pool_output(exchange.ethPool(), exchange.tokenPool(), 0.1*10**18, fee)
    # Act & Assert
    with pytest.raises(Exception):
        ethToTokenTx = exchange.ethToToken(account.address, expectedReturn * 1.05, {'from': account, 'value': 0.1*10**18})
        ethToTokenTx.wait(1)

def test_call_ethToToken_no_seed():
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
        ethToTokenTx = exchange.ethToToken(account.address, 1*10**18, {'from': account, 'value': 0.1*10**18})
        ethToTokenTx.wait(1)

def test_call_tokenToEth_min_0():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 100*10**18 + 2*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    beforeInvariant = exchange.invariant()
    expectedReturn = calculate_liquidity_pool_output(exchange.tokenPool(), exchange.ethPool(), 2*10**18, fee)
    # Act
    tokenToEthTx = exchange.tokenToEth(account.address, 2*10**18, 0, {'from': account})
    tokenToEthTx.wait(1)
    # Assert
    assert abs(tokenToEthTx.events["EthPurchase"]["ethOut"] / expectedReturn - 1) < 0.0001 # I was having some jank in the math, was not able to find it. 0.01% error is fine.
    assert exchange.invariant() >= beforeInvariant

def test_call_tokenToEth_min_smaller():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 100*10**18 + 2*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    beforeInvariant = exchange.invariant()
    expectedReturn = calculate_liquidity_pool_output(exchange.tokenPool(), exchange.ethPool(), 2*10**18, fee)
    # Act
    tokenToEthTx = exchange.tokenToEth(account.address, 2*10**18, expectedReturn * 0.95, {'from': account})
    # Above has 5% slippage
    tokenToEthTx.wait(1)
    # Assert
    assert abs(tokenToEthTx.events["EthPurchase"]["ethOut"] / expectedReturn - 1) < 0.0001 # I was having some jank in the math, was not able to find it. 0.01% error is fine.
    assert exchange.invariant() >= beforeInvariant

def test_call_tokenToEth_min_larger():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 100*10**18 + 2*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    
    expectedReturn = calculate_liquidity_pool_output(exchange.tokenPool(), exchange.ethPool(), 2*10**18, fee)
    # Act & Assert
    with pytest.raises(Exception):
        tokenToEthTx = exchange.tokenToEth(account.address, 2*10**18, expectedReturn * 1.05, {'from': account})
        tokenToEthTx.wait(1)

def test_call_tokenToEth_no_seed():
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
        tokenToEthTx = exchange.tokenToEth(account.address, 2*10**18, 0, {'from': account})
        tokenToEthTx.wait(1)

def test_ethToToken_quotes():
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
    quote = exchange.getEthToTokenQuote(0.1*10**18)
    # Act
    ethToTokenTx = exchange.ethToToken(account.address, 0, {'from': account, 'value': 0.1*10**18})
    ethToTokenTx.wait(1)
    # Assert
    assert abs(ethToTokenTx.events["TokenPurchase"]["tokensOut"] / quote - 1) == 0

    # And again!
    quote = exchange.getEthToTokenQuote(0.3*10**18)
    # Act
    ethToTokenTx = exchange.ethToToken(account.address, 0, {'from': account, 'value': 0.3*10**18})
    ethToTokenTx.wait(1)
    # Assert
    assert abs(ethToTokenTx.events["TokenPurchase"]["tokensOut"] / quote - 1) == 0

    # And again!
    quote = exchange.getEthToTokenQuote(123456789)
    # Act
    ethToTokenTx = exchange.ethToToken(account.address, 0, {'from': account, 'value': 123456789})
    ethToTokenTx.wait(1)
    # Assert
    assert abs(ethToTokenTx.events["TokenPurchase"]["tokensOut"] / quote - 1) == 0

def test_tokenToEth_quotes():
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
    quote = exchange.getTokenToEthQuote(1*10**18)
    # Act
    tokenToEthTx = exchange.tokenToEth(account.address, 1*10**18, 0, {'from': account})
    tokenToEthTx.wait(1)
    # Assert
    assert abs(tokenToEthTx.events["EthPurchase"]["ethOut"] / quote - 1) == 0

    # And again!
    quote = exchange.getTokenToEthQuote(6*10**18)
    # Act
    tokenToEthTx = exchange.tokenToEth(account.address, 6*10**18, 0, {'from': account})
    tokenToEthTx.wait(1)
    # Assert
    assert abs(tokenToEthTx.events["EthPurchase"]["ethOut"] / quote - 1) == 0

    # And again!
    quote = exchange.getTokenToEthQuote(1234567)
    # Act
    tokenToEthTx = exchange.tokenToEth(account.address, 1234567, 0, {'from': account})
    tokenToEthTx.wait(1)
    # Assert
    assert abs(tokenToEthTx.events["EthPurchase"]["ethOut"] / quote - 1) == 0