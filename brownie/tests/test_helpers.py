from scripts.helpers import *

def test_calculate_liquidity_pool_output():
    ethPool1 = 10
    omgPool1 = 500
    invariant = 5000
    assert invariant == ethPool1 * omgPool1
    fee = 400
    amount = 1
    # Going through the math
    # Fee will be 1/400 of the amount, rounded down so here 0
    # The new pool will be 10 - 0 + 1 = 11
    # The new omgPool will be 5000 / 11 = 455 (+1, floored)
    # What will be paid out is 500 - 455 = 45
    assert calculate_liquidity_pool_output(ethPool1, omgPool1, amount, fee) == 45

    # Bit of a more crazy example
    ethPool2 = 1000
    omgPool2 = 100000
    invariant = 100000000
    assert invariant == ethPool2 * omgPool2
    fee = 10
    amount = 30
    # Fee is 30/10 = 3
    # Temp pool is 1000 - 3 + 30 = 1027
    # New omgPool is 100000000 / 1027 = 97371 (+ 1)
    # What will be paid out is 100000 - 97371 = 2629
    assert calculate_liquidity_pool_output(ethPool2, omgPool2, amount, fee) == 2629
