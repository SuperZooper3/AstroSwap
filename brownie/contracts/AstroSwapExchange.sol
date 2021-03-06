// contracts/AstroSwapExchange.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// 0.8.0 so no need for safeMath
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./AstroSwapFactory.sol";

contract AstroSwapExchange {
    // The address of the factory that made us :)
    AstroSwapFactory public factory;

    // The address of the token we are swapping
    IERC20 public token;

    // The fee each transaction takes. The proportion taken in the inverse of the fee varaiable. Ex: 1% fee is 100
    uint256 public feeAmmount;

    // Keep track of the ethereum and token liquidity pools (both are in wei)
    uint256 public ethPool;
    uint256 public tokenPool;

    // The invariant in the product of the token and ethereum pools we want to keep
    uint256 public invariant;

    // Keep track of investor shares
    mapping (address => uint256) public investorShares;
    uint256 public totalShares;

    event TokenPurchase(address indexed user, address indexed recipient, uint256 ethIn, uint256 tokensOut);
    event EthPurchase(address indexed user, address indexed recipient, uint256 tokensIn, uint256 ethOut);
    event TokenToTokenOut(address indexed user, address indexed recipient, address indexed tokenExchangeAddress, uint256 tokensIn, uint256 ethTransfer);
    event Investment(address indexed user, uint256 indexed sharesPurchased, uint256 ethInvested, uint256 tokensInvested);
    event Divestment(address indexed user, uint256 indexed sharesBurned, uint256 ethDivested, uint256 tokensDivested);

    constructor(IERC20 _token, uint256 _fee) {
        factory = AstroSwapFactory(msg.sender);
        feeAmmount = _fee;
        token = _token;
    }

    modifier hasLiquidity() {
        require(invariant > 0);
        _;
    }

    function seedInvest(uint256 tokenInvestment) public payable {
        require (totalShares == 0, "Liquidity pool is already seeded, use invest() instead");
        require (tokenInvestment > 0 && msg.value > 0, "Must invest ETH and tokens");
        token.transferFrom(msg.sender, address(this), tokenInvestment);
        tokenPool = tokenInvestment;
        ethPool = msg.value;
        invariant = ethPool * tokenPool;
        // Give the starting investor 10000 shares
        investorShares[msg.sender] = 10000;
        totalShares = 10000;
        emit Investment(msg.sender, 10000, msg.value, tokenInvestment);
    }

    function invest(uint256 maxTokensInvested) public payable{
        // Amount of tokens to invest is bassed of of the current ratio of eth to token in the pools
        uint256 tokenInvestment = (tokenPool * msg.value / ethPool);
        require(maxTokensInvested >= tokenInvestment, "Max < required investment");
        require (token.transferFrom(msg.sender, address(this), tokenInvestment));
        uint256 sharesPurchased = (tokenInvestment * totalShares)/ tokenPool;
        ethPool += msg.value;
        tokenPool += tokenInvestment;
        invariant = ethPool * tokenPool;
        // Give the investor their shares
        investorShares[msg.sender] += sharesPurchased;
        totalShares += sharesPurchased;
        emit Investment(msg.sender, sharesPurchased, msg.value, tokenInvestment);
    }

    function investQuoteFromEth(uint256 ethPaid) public view returns (uint256 tokensRequired) {
        return (tokenPool * ethPaid / ethPool);
    }

    function investQuoteFromTokens(uint256 tokensPaid) public view returns (uint256 ethRequired) {
        return (ethPool * tokensPaid / tokenPool);
    }

    function divest(uint256 shares) public {
        require(investorShares[msg.sender] >= shares, "Not enough shares to divest");
        uint256 ethOut = (ethPool * shares) / totalShares;
        uint256 tokenOut = (tokenPool * shares) / totalShares;
        require(token.transfer(msg.sender, tokenOut));
        payable(msg.sender).call{value:ethOut};
        ethPool -= ethOut;
        tokenPool -= tokenOut;
        invariant = ethPool * tokenPool;
        investorShares[msg.sender] -= shares;
        totalShares -= shares;
        emit Divestment(msg.sender, shares, ethOut, tokenOut);
    }

    function getShares(address investor) public view returns (uint256 shareCount) {
        return investorShares[investor];
    }

    function getEthToTokenQuote(uint256 ethValue) public view returns (uint256 tokenQuote) {
        uint256 fee = ethValue / feeAmmount;
        uint256 mockPool = ethPool + ethValue;
        return (tokenPool - (invariant / (mockPool - fee) + 1));
    }

    function getTokenToEthQuote(uint256 tokenValue) public view returns (uint256 ethQuote) {
        uint256 fee = tokenValue / feeAmmount;
        uint256 mockPool = tokenPool + tokenValue;
        return (ethPool - (invariant / (mockPool - fee) + 1));
    }

    function getTokenToTokenQuote(uint256 tokenValue, address tokenOutAddress) public view returns (uint256 tokenQuote) {
        uint256 ethTransfer = getTokenToEthQuote(tokenValue);
        AstroSwapExchange outExchange = AstroSwapExchange(factory.tokenToExchange(tokenOutAddress));
        return outExchange.getEthToTokenQuote(ethTransfer);
    }

    function ethToTokenPrivate(uint256 value) private returns(uint256 tokenToPay){
        uint256 fee = value / feeAmmount;
        ethPool = ethPool + value;
        uint256 tokensPaid = tokenPool - (invariant / (ethPool - fee) + 1); // k = x * y <==> y = k / x, we payout the difference
        // The +1 in the above line is to prevent a rouding error that causes the invariant to lower on transactions where the fee rounds down to 0
        require(tokensPaid <= tokenPool, "Lacking pool tokens"); // Make sure we have enough tokens to pay out
        tokenPool = tokenPool - tokensPaid;
        invariant = tokenPool * ethPool;
        return tokensPaid;
    }

    function tokenToEthPrivate(uint256 tokensIn) private returns(uint256 ethToPay){
        uint256 fee = tokensIn / feeAmmount;
        tokenPool = tokenPool + tokensIn;
        uint256 ethPaid = ethPool - (invariant / (tokenPool - fee) + 1); // k = x * y <==> x = k / y, we payout the difference
        // The +1 in the above line is to prevent a rouding error that causes the invariant to lower on transactions where the fee rounds down to 0
        require(ethPaid <= ethPool, "Lacking pool eth"); // Make sure we have enough eth to pay out
        ethPool = ethPool - ethPaid;
        invariant = tokenPool * ethPool;
        return ethPaid;
    }

    function ethToToken(address recipient, uint256 minTokensOut) public payable hasLiquidity returns(uint256 tokensPaid){
        uint256 tokensPaid = ethToTokenPrivate(msg.value);
        require(tokensPaid >= minTokensOut, "tknsPaid < minTknsOut");
        emit TokenPurchase(msg.sender, recipient, msg.value, tokensPaid);
        require(token.transfer(recipient, tokensPaid), "Tkn OUT transfer fail");
        return tokensPaid;
    }

    function tokenToEth(address recipient, uint256 tokensIn, uint256 minEthOut) public hasLiquidity returns(uint256 ethPaid){
        require(token.transferFrom(msg.sender, address(this), tokensIn), "Tkn IN transfer fail");
        uint256 ethPaid = tokenToEthPrivate(tokensIn);
        require(ethPaid >= minEthOut, "ethPaid < minEthOut");
        emit EthPurchase(msg.sender, recipient, tokensIn, ethPaid);
        payable(recipient).call{value:ethPaid};
        return ethPaid;
    }

    function tokenToToken(address recipient, address tokenOutAddress, uint256 tokensIn, uint256 minTokensOut) public hasLiquidity{
        require(token.transferFrom(msg.sender, address(this), tokensIn), "Tkn IN transfer fail");
        uint256 ethTransfer = tokenToEthPrivate(tokensIn);
        require(ethTransfer > 0, "Eth out is too small");
        address tokenExchangeAddress = factory.tokenToExchange(tokenOutAddress);
        uint256 tokensOut = AstroSwapExchange(tokenExchangeAddress).ethToToken{value: ethTransfer}(recipient, minTokensOut); // Call the outcontract with the value
        require(tokensOut >= minTokensOut, "Output less than minTokensOut");
        emit TokenToTokenOut(msg.sender, recipient, tokenExchangeAddress, tokensIn, ethTransfer);
    }
}