// contracts/AstroSwapFactory.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./AstroSwapExchange.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

// Almost directly taken from https://github.com/Uniswap/old-solidity-contracts/blob/master/contracts/Exchange/UniswapFactory.sol
contract AstroSwapFactory {
    uint256 public feeRate;
    address[] public tokensAvailable;
    mapping(address => address) public tokenToExchange;
    mapping(address => address) public exchangeToToken;

    constructor(uint256 _fee) {
        feeRate = _fee;
    }

    event TokenExchangeAdded(address indexed tokenExchange, address indexed tokenAddress);

    function convertTokenToExchange(address token) public view returns (address exchange) {
        return tokenToExchange[token];
    }

    function convertExchangeToToken(address exchange) public view returns (address token) {
        return exchangeToToken[exchange];
    }

    function exchangeCount() public view returns (uint256 count) {
        return tokensAvailable.length;
    }

    function addTokenExchange(address tokenAddress) public {
        require(tokenToExchange[tokenAddress] == address(0), "Allready added");
        require(tokenAddress != address(0));
        AstroSwapExchange exchange = new AstroSwapExchange(IERC20(tokenAddress), feeRate);
        tokensAvailable.push(tokenAddress);
        tokenToExchange[tokenAddress] = address(exchange);
        exchangeToToken[address(exchange)] = tokenAddress;
        emit TokenExchangeAdded(address(exchange), tokenAddress);
    }
}