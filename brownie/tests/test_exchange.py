from scripts.helpers import smart_get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from scripts.runAstroSwap import deploy_erc20 
from brownie import network, accounts, config, AstroSwapExchange, MockERC20
import pytest

# All the exchange tests
# - Deploy an exchange contract
# - Seed invest properly
# - Seed invest just tokens (should fail)
# - Seed invest just ETH (should fail)
# - Seed invest nothing (should fail)
# - Seed invest without authorising the ERC20 transfer (should fail)
# - Invest properly
# - Invest just tokens (should fail)
# - Invest just ETH (should fail)
# - Invest nothing (should fail)
# - Invest as much as has been seeded
# - Invest half as much as what was seeded
# - Invest 2x as much as what was seeded
# - Invest a random amount 
# - Invest without authorising any ERC20 transfer (should fail)
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



