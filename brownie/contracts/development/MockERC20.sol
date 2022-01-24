// contracts/MockERC20.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor(string memory name) ERC20(name, name) {
        _mint(msg.sender, 1_000_000_000_000_000_000_000_000);
    }
}