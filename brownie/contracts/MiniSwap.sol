// contracts/AstroSwapFactory.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
// The goal of this contract is to create a multi-token exchange that allows pools to be made without creating other contracts.

contract MiniSwap {
    uint256 public feeRate;
    uint256 public exchangeCount;

    struct Exchange {
        IERC20 token;
        uint256 ethPool;
        uint256 tokenPool;
        // We are not storing the invariant because it dosent need to be stored, can just be calculated on the spot
        mapping (address => uint256) investorShares;
        uint256 totalShares;
    } 

    mapping (address => Exchange) public exchanges; // Mapping of token addresses to exchanges
    
    event TokenPurchase(address indexed exchange, address indexed user, address indexed recipient, uint256 ethIn, uint256 tokensOut);
    event EthPurchase(address indexed exchange, address indexed user, address indexed recipient, uint256 tokensIn, uint256 ethOut);
    event Investment(address indexed exchange, address indexed user, uint256 indexed sharesPurchased, uint256 ethInvested, uint256 tokensInvested);
    event Divestment(address indexed exchange, address indexed user, uint256 indexed sharesBurned, uint256 ethDivested, uint256 tokensDivested);
    
    
}