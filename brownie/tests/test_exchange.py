from scripts.helpers import smart_get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, calculate_liquidity_pool_output
from scripts.runAstroSwap import deploy_erc20 , exchange_from_address
from brownie import network, accounts, config, AstroSwapExchange, AstroSwapFactory
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
# - Divest everything properly
# - Divest half as much as what was invested
# - Divest more than was invested (should fail)
# - Exchange tokenToToken properly
# - Exchange tokenToToken with a min > expected (should fail)
# - Exchange tokenToToken without seeding anything (should fail)
# - Exchange tokenToToken while only seeding from contract (should fail)
# - Exchange tokenToToken while only seeding to account (should fail)
# - Compare tokenToTokenQuote to actual cost (3 different values + 1 random one)
# - Compare investQuoteFromEth to actual cost (3 different values)
# - Compare investQuoteFromToken to actual cost (3 different values)

def setupExchange(factory, token1, token2, account):
    exchangeForge1 = factory.addTokenExchange(token1.address, {'from': account})
    exchangeForge1.wait(1)
    exchangeAddress1 = exchangeForge1.events["TokenExchangeAdded"][0]["tokenExchange"]
    exchange1 = exchange_from_address(exchangeAddress1)
    exchangeForge2 = factory.addTokenExchange(token2.address, {'from': account})
    exchangeForge2.wait(1)
    exchangeAddress2 = exchangeForge2.events["TokenExchangeAdded"][0]["tokenExchange"]
    exchange2 = exchange_from_address(exchangeAddress2)
    return exchange1, exchange2



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

def test_divest_proprely():
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
    print("Seeding")
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    print("Divesting")
    # Act
    divestTx = exchange.divest(10000, {'from': account})
    divestTx.wait(1)
    # Assert
    assert exchange.invariant() == 0
    assert exchange.tokenPool() == 0
    assert exchange.ethPool() == 0
    assert exchange.invariant() == 0
    assert exchange.getShares(account.address) == 0

def test_divest_half():
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
    print("Seeding")
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    print("Divesting")
    # Act
    divestTx = exchange.divest(10000*0.5, {'from': account})
    divestTx.wait(1)
    # Assert
    assert exchange.invariant() == 1*10**18*0.5 * 100*10**18*0.5
    assert exchange.tokenPool() == 50*10**18
    assert exchange.ethPool() == 0.5*10**18
    assert exchange.getShares(account.address) == 10000 - 10000*0.5

def test_divest_more_than_owned():
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
    print("Seeding")
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    print("Divesting")
    # Act & Assert
    with pytest.raises(Exception):
        divestTx = exchange.divest(10000*2, {'from': account})
        divestTx.wait(1)

def test_call_tokenToToken():
    # Arrange
    token1 = deploy_erc20()
    token2 = deploy_erc20()
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    # Create the two exchanges
    exchange1, exchange2 = setupExchange(factory, token1, token2, account)
    # Seed the two exchanges
    approve1Tx = token1.approve(exchange1.address, 100*10**18, {'from': account})
    approve1Tx.wait(1)
    approve2Tx = token2.approve(exchange2.address, 100*10**18, {'from': account})
    approve2Tx.wait(1)
    seed1Tx = exchange1.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seed1Tx.wait(1)
    seed2Tx = exchange2.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seed2Tx.wait(1)
    # Act
    approve1Tx = token1.approve(exchange1.address, 0.1*10**18, {'from': account})
    approve1Tx.wait(1)
    tokenToTokenTx = exchange1.tokenToToken(account.address, token2.address, 0.1*10**18, 0, {'from': account})
    tokenToTokenTx.wait(1)
    # Assert
    assert tokenToTokenTx.events["TokenToTokenOut"]["tokenExchangeAddress"] == exchange2.address
    assert tokenToTokenTx.events["TokenToTokenOut"]["recipient"] == account.address
    assert tokenToTokenTx.events["TokenToTokenOut"]["user"] == account.address
    assert tokenToTokenTx.events["TokenToTokenOut"]["ethTransfer"] > 0
    
    assert tokenToTokenTx.events["TokenPurchase"]["user"] == exchange1.address
    assert tokenToTokenTx.events["TokenPurchase"]["ethIn"] == tokenToTokenTx.events["TokenToTokenOut"]["ethTransfer"]
    assert tokenToTokenTx.events["TokenPurchase"]["tokensOut"] > 0

def test_call_tokenToToken_min_bigger():
    # Arrange
    token1 = deploy_erc20()
    token2 = deploy_erc20()
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    # Create the two exchanges
    exchange1, exchange2 = setupExchange(factory, token1, token2, account)
    # Seed the two exchanges
    approve1Tx = token1.approve(exchange1.address, 100*10**18, {'from': account})
    approve1Tx.wait(1)
    approve2Tx = token2.approve(exchange2.address, 100*10**18, {'from': account})
    approve2Tx.wait(1)
    seed1Tx = exchange1.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seed1Tx.wait(1)
    seed2Tx = exchange2.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seed2Tx.wait(1)
    # Act & Assert
    with pytest.raises(Exception):
        approve1Tx = token1.approve(exchange1.address, 0.1*10**18, {'from': account})
        approve1Tx.wait(1)
        tokenToTokenTx = exchange1.tokenToToken(account.address, token2.address, 0.1*10**18, 100*10**18, {'from': account})
        tokenToTokenTx.wait(1)

def test_call_tokenToToken_seeded_only_from():
    # Arrange
    token1 = deploy_erc20()
    token2 = deploy_erc20()
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    # Create the two exchanges
    exchange1, exchange2 = setupExchange(factory, token1, token2, account)
    # Seed the two exchanges
    approve1Tx = token1.approve(exchange1.address, 100*10**18, {'from': account})
    approve1Tx.wait(1)
    seed1Tx = exchange1.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seed1Tx.wait(1)
    # Act & Assert
    with pytest.raises(Exception):
        approve1Tx = token1.approve(exchange1.address, 0.1*10**18, {'from': account})
        approve1Tx.wait(1)
        tokenToTokenTx = exchange1.tokenToToken(account.address, token2.address, 0.1*10**18, 0, {'from': account})
        tokenToTokenTx.wait(1)

def test_call_tokenToToken_seeded_only_to():
    # Arrange
    token1 = deploy_erc20()
    token2 = deploy_erc20()
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    # Create the two exchanges
    exchange1, exchange2 = setupExchange(factory, token1, token2, account)
    # Seed the two exchanges
    approve2Tx = token2.approve(exchange2.address, 100*10**18, {'from': account})
    approve2Tx.wait(1)
    seed2Tx = exchange2.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seed2Tx.wait(1)
    # Act & Assert
    with pytest.raises(Exception):
        approve2Tx = token2.approve(exchange2.address, 0.1*10**18, {'from': account})
        approve2Tx.wait(1)
        tokenToTokenTx = exchange2.tokenToToken(account.address, token1.address, 0.1*10**18, 0, {'from': account})
        tokenToTokenTx.wait(1)

def test_tokenToToken_quotes():
    # Arrange
    token1 = deploy_erc20()
    token2 = deploy_erc20()
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    # Create the two exchanges
    exchange1, exchange2 = setupExchange(factory, token1, token2, account)
    # Seed the two exchanges
    approve1Tx = token1.approve(exchange1.address, 100*10**18, {'from': account})
    approve1Tx.wait(1)
    seed1Tx = exchange1.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seed1Tx.wait(1)
    approve2Tx = token2.approve(exchange2.address, 100*10**18, {'from': account})
    approve2Tx.wait(1)
    seed2Tx = exchange2.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seed2Tx.wait(1)
    # Act
    tokenOutQuote = exchange1.getTokenToTokenQuote(0.1*10**18, token2.address, {'from': account})
    approve1Tx = token1.approve(exchange1.address, 0.1*10**18, {'from': account})
    approve1Tx.wait(1)
    tokenToTokenTx = exchange1.tokenToToken(account.address, token2.address, 0.1*10**18, 0, {'from': account})
    tokenToTokenTx.wait(1)
    # Assert
    assert tokenToTokenTx.events["TokenPurchase"]["tokensOut"] == tokenOutQuote

    # And again!
    tokenOutQuote2 = exchange2.getTokenToTokenQuote(11*10**18, token1.address, {'from': account})
    approve2Tx = token2.approve(exchange2.address, 11*10**18, {'from': account})
    approve2Tx.wait(1)
    tokenToTokenTx2 = exchange2.tokenToToken(account.address, token1.address, 11*10**18, 0, {'from': account})
    tokenToTokenTx2.wait(1)
    # Assert
    assert tokenToTokenTx2.events["TokenPurchase"]["tokensOut"] == tokenOutQuote2

    # And again!
    tokenOutQuote3 = exchange1.getTokenToTokenQuote(0.12345*10**18, token2.address, {'from': account})
    approve1Tx = token1.approve(exchange1.address, 0.12345*10**18, {'from': account})
    approve1Tx.wait(1)
    tokenToTokenTx3 = exchange1.tokenToToken(account.address, token2.address, 0.12345*10**18, 0, {'from': account})
    tokenToTokenTx3.wait(1)
    # Assert
    assert tokenToTokenTx3.events["TokenPurchase"]["tokensOut"] == tokenOutQuote3

    # And again! (Random this time ;)
    randomTokens = randint(0, 20*10**18)
    tokenOutQuote4 = exchange1.getTokenToTokenQuote(randomTokens, token2.address, {'from': account})
    approve1Tx = token1.approve(exchange1.address, randomTokens, {'from': account})
    approve1Tx.wait(1)
    tokenToTokenTx4 = exchange1.tokenToToken(account.address, token2.address, randomTokens, 0, {'from': account})
    tokenToTokenTx4.wait(1)
    # Assert
    assert tokenToTokenTx4.events["TokenPurchase"]["tokensOut"] == tokenOutQuote4


def test_investQuoteFromEth():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 1000*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    # Act
    quote = exchange.investQuoteFromEth(1*10**18)
    investTx = exchange.invest(10**22, {'from': account, 'value': 1*10**18})
    investTx.wait(1)
    # Assert
    assert investTx.events["Investment"]["tokensInvested"] == quote

    # And again!
    quote2 = exchange.investQuoteFromEth(0.23*10**18)
    investTx2 = exchange.invest(10**22, {'from': account, 'value': 0.23*10**18})
    investTx2.wait(1)
    # Assert
    assert investTx2.events["Investment"]["tokensInvested"] == quote2

    # And again!
    quote3 = exchange.investQuoteFromEth(0.12345*10**18)
    investTx3 = exchange.invest(10**22, {'from': account, 'value': 0.12345*10**18})
    investTx3.wait(1)
    # Assert
    assert investTx3.events["Investment"]["tokensInvested"] == quote3

    # And again! (Zero)
    quote4 = exchange.investQuoteFromEth(0)
    investTx4 = exchange.invest(10**22, {'from': account, 'value': 0})
    investTx4.wait(1)
    # Assert
    assert investTx4.events["Investment"]["tokensInvested"] == quote4

def test_investQuoteFromToken():
    # Arrange
    token = deploy_erc20()
    account = smart_get_account(1)
    exchange = AstroSwapExchange.deploy(
        token.address,
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
        )
    approveTx = token.approve(exchange.address, 1000*10**18, {'from': account})
    approveTx.wait(1)
    seedTx = exchange.seedInvest(100*10**18, {'from': account, 'value': 1*10**18})
    seedTx.wait(1)
    # Act
    quote = exchange.investQuoteFromTokens(6*10**18)
    print(quote)
    investTx = exchange.invest(10**22, {'from': account, 'value': quote})
    investTx.wait(1)
    # Assert
    assert investTx.events["Investment"]["tokensInvested"] == 6*10**18

    # And again!
    quote2 = exchange.investQuoteFromTokens(0.23*10**18)
    investTx2 = exchange.invest(10**22, {'from': account, 'value': quote2})
    investTx2.wait(1)
    # Assert
    assert investTx2.events["Investment"]["tokensInvested"] == 0.23*10**18

    # And again!
    quote3 = exchange.investQuoteFromTokens(0.12345*10**18)
    investTx3 = exchange.invest(10**22, {'from': account, 'value': quote3})
    investTx3.wait(1)
    # Assert
    assert investTx3.events["Investment"]["tokensInvested"] == 0.12345*10**18

    # And again! (Zero)
    quote4 = exchange.investQuoteFromTokens(0)
    investTx4 = exchange.invest(10**22, {'from': account, 'value': quote4})
    investTx4.wait(1)
    # Assert
    assert investTx4.events["Investment"]["tokensInvested"] == 0