// contracts/AstroSwapFactory.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./AstroSwapExchange.sol";

// Almost directly taken from https://github.com/Uniswap/old-solidity-contracts/blob/master/contracts/Exchange/UniswapFactory.sol
contract AstroSwapFactory {
    address[] public tokensAvailable;
    mapping(address => address) public tokenToExchange;
    mapping(address => address) public exchangeToToken;

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
        AstroSwapExchange exchange = new AstroSwapExchange(tokenAddress);
        tokensAvailable.push(tokenAddress);
        tokenToExchange[tokenAddress] = exchange;
        exchangeToToken[exchange] = tokenAddress;
        TokenExchangeAdded(exchange, tokenAddress);
    }
}