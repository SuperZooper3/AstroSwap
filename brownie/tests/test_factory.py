from eth_typing import Address
from scripts.helpers import smart_get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, calculate_liquidity_pool_output
from scripts.runAstroSwap import deploy_erc20 , get_exchange_info
from scripts.runAstroFactory import get_factory_info, deploy_new_exchange
from brownie import network, accounts, config, AstroSwapExchange, AstroSwapFactory, MockERC20
import pytest
from random import randint

# All the factory tests
# - Deploy a factory contract properly
# - Add a token exchange through the factory
# - Add a token with a zero address (should fail)
# - Try add a token exchange that allready exists (should fail)
# - Convert from token to exchange when the exchange is deployed
# - Convert from exchange to token when the exchange is deployed
# - Convert from token to exchange when the exchange is not deployed (should fail)
# - Convert from exchange to token when the exchange is not deployed (should fail)
# - Deploy a random amount of exchanges, make sure the count is right
# - Make sure count is correct for 0 exchanges

fee = 400

def test_factory_deploy():
    # Arrange
    account = smart_get_account(1)
    # Act
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    # Assert
    assert factory.address != None

def test_factory_add_exchange():
    # Arrange
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    erc20 = deploy_erc20()
    # Act
    forgeTx = factory.addTokenExchange(erc20.address, {'from': account})
    forgeTx.wait(1)
    # Assert
    assert forgeTx.events["TokenExchangeAdded"][0]["tokenExchange"] != "0x0000000000000000000000000000000000000000"

def test_factory_add_exchange_zero_address():
    # Arrange
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    # Act & Assert
    with pytest.raises(Exception):
        factory.addTokenExchange("0x0000000000000000000000000000000000000000", {'from': account})

def test_factory_add_exchange_allready_added():
    # Arrange
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    erc20 = deploy_erc20()
    # Act
    forgeTx = factory.addTokenExchange(erc20.address, {'from': account})
    forgeTx.wait(1)
    # Assert
    with pytest.raises(Exception):
        forgeTx = factory.addTokenExchange(erc20.address, {'from': account})

def test_factory_convert_token_to_exchange():
    # Arrange
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    erc20 = deploy_erc20()
    # Act
    forgeTx = factory.addTokenExchange(erc20.address, {'from': account})
    forgeTx.wait(1)
    tokenExchangeAddress = forgeTx.events["TokenExchangeAdded"][0]["tokenExchange"]
    # Assert
    assert factory.convertTokenToExchange(erc20.address) == tokenExchangeAddress

def test_factory_convert_exchange_to_token():
    # Arrange
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    erc20 = deploy_erc20()
    # Act
    forgeTx = factory.addTokenExchange(erc20.address, {'from': account})
    forgeTx.wait(1)
    tokenExchangeAddress = forgeTx.events["TokenExchangeAdded"][0]["tokenExchange"]
    # Assert
    assert factory.convertExchangeToToken(tokenExchangeAddress) == erc20.address

def test_factory_convert_token_to_exchange_no_exchange():
    # Arrange
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    erc20 = deploy_erc20()
    # Act & Assert
    with pytest.raises(Exception):
        factory.convertTokenToExchange(erc20.address)

def test_factory_convert_exchange_to_token_no_exchange():
    # Arrange
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    erc20 = deploy_erc20()
    # Act & Assert
    with pytest.raises(Exception):
        factory.convertExchangeToToken(erc20.address)

def test_factory_count_random():
    # Arrange
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    # Act
    value = randint(1, 10)
    for i in range(value):
        erc20 = deploy_erc20()
        forgeTx = factory.addTokenExchange(erc20.address, {'from': account})
        forgeTx.wait(1)
    count = factory.getExchangeCount()
    # Assert
    assert count == value

def test_factory_count_zero():
    # Arrange
    account = smart_get_account(1)
    factory = AstroSwapFactory.deploy(
        fee,
        {'from': account},
        publish_source = config["networks"][network.show_active()].get("verify", False)
    )
    # Act
    count = factory.getExchangeCount()
    # Assert
    assert count == 0