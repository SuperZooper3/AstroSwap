// contracts/AstroSwapFactory.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
// The goal of this contract is to create a multi-token exchange that allows pools to be made without creating other contracts.
// Heavily bassed off of AstroSwapExchange


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
    event TokenToToken(address indexed exchange, address indexed user, address recipient, address indexed tokenExchangeAddress, uint256 tokensIn, uint256 ethTransfer); // Recipeint is not indexed here due to the 3 index limit
    event Investment(address indexed exchange, address indexed user, uint256 indexed sharesPurchased, uint256 ethInvested, uint256 tokensInvested);
    event Divestment(address indexed exchange, address indexed user, uint256 indexed sharesBurned, uint256 ethDivested, uint256 tokensDivested);
    
    constructor(uint256 _fee) {
        feeRate = _fee;
    }

    modifier hasLiquidity(address token) {
        require(exchanges[token].ethPool > 0);
        _;
    }

    function seedInvest(address tokenAddress, uint256 tokenInvestment) public payable {
        require (exchanges[tokenAddress].totalShares == 0, "Liquidity pool is already seeded, use invest() instead");
        require (tokenInvestment > 0 && msg.value > 0, "Must invest ETH and tokens");
        exchanges[tokenAddress].token.transferFrom(msg.sender, address(this), tokenInvestment);
        exchanges[tokenAddress].tokenPool = tokenInvestment;
        exchanges[tokenAddress].ethPool = msg.value;
        // Give the starting investor 10000 shares
        exchanges[tokenAddress].investorShares[msg.sender] = 10000;
        exchanges[tokenAddress].totalShares = 10000;
        emit Investment(tokenAddress, msg.sender, 10000, msg.value, tokenInvestment);
    }

    function invest(address tokenAddress, uint256 maxTokensInvested) public payable{
        // Amount of tokens to invest is bassed of of the current ratio of eth to token in the pools
        uint256 tokenInvestment = (exchanges[tokenAddress].tokenPool * msg.value / exchanges[tokenAddress].ethPool);
        require(maxTokensInvested >= tokenInvestment, "Max < required investment");
        require (exchanges[tokenAddress].token.transferFrom(msg.sender, address(this), tokenInvestment));
        uint256 sharesPurchased = (tokenInvestment * exchanges[tokenAddress].totalShares)/ exchanges[tokenAddress].tokenPool;
        exchanges[tokenAddress].ethPool += msg.value;
        exchanges[tokenAddress].tokenPool += tokenInvestment;
        // Give the investor their shares
        exchanges[tokenAddress].investorShares[msg.sender] += sharesPurchased;
        exchanges[tokenAddress].totalShares += sharesPurchased;
        emit Investment(tokenAddress, msg.sender, sharesPurchased, msg.value, tokenInvestment);
    }

    function investQuoteFromEth(address tokenAddress, uint256 ethPaid) public view returns (uint256 tokensRequired) {
        return (exchanges[tokenAddress].tokenPool * ethPaid / exchanges[tokenAddress].ethPool);
    }

    function investQuoteFromTokens(address tokenAddress, uint256 tokensPaid) public view returns (uint256 ethRequired) {
        return (exchanges[tokenAddress].ethPool * tokensPaid / exchanges[tokenAddress].tokenPool);
    }

    function divest(address tokenAddress, uint256 shares) public {
        require(exchanges[tokenAddress].investorShares[msg.sender] >= shares, "Not enough shares to divest");
        uint256 ethOut = (exchanges[tokenAddress].ethPool * shares) / exchanges[tokenAddress].totalShares;
        uint256 tokenOut = (exchanges[tokenAddress].tokenPool * shares) / exchanges[tokenAddress].totalShares;
        require(exchanges[tokenAddress].token.transfer(msg.sender, tokenOut));
        payable(msg.sender).call{value:ethOut};
        exchanges[tokenAddress].ethPool -= ethOut;
        exchanges[tokenAddress].tokenPool -= tokenOut;
        exchanges[tokenAddress].investorShares[msg.sender] -= shares;
        exchanges[tokenAddress].totalShares -= shares;
        emit Divestment(tokenAddress, msg.sender, shares, ethOut, tokenOut);
    }

    function getShares(address tokenAddress, address investor) public view returns (uint256 shareCount) {
        return exchanges[tokenAddress].investorShares[investor];
    }

    function getEthToTokenQuote(address tokenAddress, uint256 ethValue) public view returns (uint256 tokenQuote) {
        uint256 fee = ethValue / feeRate;
        uint256 mockPool = exchanges[tokenAddress].ethPool + ethValue;
        uint256 invariant = exchanges[tokenAddress].ethPool * exchanges[tokenAddress].tokenPool;
        return (exchanges[tokenAddress].tokenPool - (invariant / (mockPool - fee) + 1));
    }

    function getTokenToEthQuote(address tokenAddress, uint256 tokenValue) public view returns (uint256 ethQuote) {
        uint256 fee = tokenValue / feeRate;
        uint256 mockPool = exchanges[tokenAddress].tokenPool + tokenValue;
        uint256 invariant = exchanges[tokenAddress].ethPool * exchanges[tokenAddress].tokenPool;
        return (exchanges[tokenAddress].ethPool - (invariant / (mockPool - fee) + 1));
    }
    
    function ethToTokenPrivate(address tokenAddress, uint256 value) private returns(uint256 tokenToPay){
        uint256 fee = value / feeRate;
        exchanges[tokenAddress].ethPool += value;
        uint256 invariant = exchanges[tokenAddress].ethPool * exchanges[tokenAddress].tokenPool;
        uint256 tokensPaid = exchanges[tokenAddress].tokenPool - (invariant / (exchanges[tokenAddress].ethPool - fee) + 1); // k = x * y <==> y = k / x, we payout the difference
        // The +1 in the above line is to prevent a rouding error that causes the invariant to lower on transactions where the fee rounds down to 0
        require(tokensPaid <= exchanges[tokenAddress].tokenPool, "Lacking pool tokens"); // Make sure we have enough tokens to pay out
        exchanges[tokenAddress].tokenPool -= tokensPaid;
        return tokensPaid;
    }

    function tokenToEthPrivate(address tokenAddress, uint256 tokensIn) private returns(uint256 ethToPay){
        uint256 fee = tokensIn / feeRate;
        exchanges[tokenAddress].tokenPool += tokensIn;
        uint256 invariant = exchanges[tokenAddress].ethPool * exchanges[tokenAddress].tokenPool;
        uint256 ethPaid = exchanges[tokenAddress].ethPool - (invariant / (exchanges[tokenAddress].tokenPool - fee) + 1); // k = x * y <==> x = k / y, we payout the difference
        // The +1 in the above line is to prevent a rouding error that causes the invariant to lower on transactions where the fee rounds down to 0
        require(ethPaid <= exchanges[tokenAddress].ethPool, "Lacking pool eth"); // Make sure we have enough eth to pay out
        exchanges[tokenAddress].ethPool -= ethPaid;
        return ethPaid;
    }

    function ethToToken(address tokenAddress, address recipient, uint256 minTokensOut) public payable hasLiquidity(tokenAddress) returns(uint256 tokensPaid){
        uint256 tokensPaid = ethToTokenPrivate(tokenAddress, msg.value);
        require(tokensPaid >= minTokensOut, "tknsPaid < minTknsOut");
        emit TokenPurchase(tokenAddress, msg.sender, recipient, msg.value, tokensPaid);
        require(exchanges[tokenAddress].token.transfer(recipient, tokensPaid), "Tkn OUT transfer fail");
        return tokensPaid;
    }

    function tokenToEth(address tokenAddress, address recipient, uint256 tokensIn, uint256 minEthOut) public hasLiquidity(tokenAddress) returns(uint256 ethPaid){
        require(exchanges[tokenAddress].token.transferFrom(msg.sender, address(this), tokensIn), "Tkn IN transfer fail");
        uint256 ethPaid = tokenToEthPrivate(tokenAddress, tokensIn);
        require(ethPaid >= minEthOut, "ethPaid < minEthOut");
        emit EthPurchase(tokenAddress, msg.sender, recipient, tokensIn, ethPaid);
        payable(recipient).call{value:ethPaid};
        return ethPaid;
    }

    function tokenToToken(address tokenFromAddress, address recipient, address tokenToAddress, uint256 tokensIn, uint256 minTokensOut) public hasLiquidity(tokenFromAddress) hasLiquidity(tokenToAddress) returns(uint256 tokensPaid){
        require(exchanges[tokenFromAddress].token.transferFrom(msg.sender, address(this), tokensIn), "Tkn IN transfer fail");
        uint256 ethTransfer = tokenToEthPrivate(tokenFromAddress, tokensIn);
        require(ethTransfer > 0, "Not enough tokens in paid in");
        uint256 tokensOut = ethToTokenPrivate(tokenToAddress, ethTransfer);
        require(tokensOut >= minTokensOut, "Output less than minTokensOut");
        require(exchanges[tokenToAddress].token.transfer(recipient, tokensOut), "Tkn OUT transfer fail");
        emit TokenToToken(tokenFromAddress, msg.sender, recipient, tokenToAddress, tokensIn, ethTransfer);
        return tokensOut;
    }
}