// contracts/AstroSwapExchange.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// 0.8.0 so no need for safeMath
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract AstroSwapExchange {
    // The address of the factory that made us :)
    address public factory;

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

    event TokenPurchase(address indexed user, uint256 ethIn, uint256 tokensOut);
    event EthPurchase(address indexed user, uint256 tokensIn, uint256 ethOut);
    event Investment(address indexed user, uint256 indexed sharesPurchased);
    event Divestment(address indexed user, uint256 indexed sharesBurned);

    constructor(IERC20 _token, uint256 _fee) {
        factory = msg.sender;
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
        // Give the starting investor 100 shares
        investorShares[msg.sender] = 100;
        totalShares = 100;
        emit Investment(msg.sender, 100);
    }

    function invest() public payable{
        // Amount of tokens to invest is bassed of of the current ratio of eth to token in the pools
        uint256 tokenInvestment = (tokenPool / ethPool) * msg.value;
        token.transferFrom(msg.sender, address(this), tokenInvestment);
        uint256 sharesPurchased = (tokenInvestment / tokenPool) * totalShares;
        ethPool += msg.value;
        tokenPool += tokenInvestment;
        invariant = ethPool * tokenPool;
        // Give the investor their shares
        investorShares[msg.sender] += sharesPurchased;
        totalShares += sharesPurchased;
        emit Investment(msg.sender, sharesPurchased);
    }

    function ethToToken(address recipient, uint256 minTokensOut) public payable hasLiquidity{
        uint256 fee = msg.value / feeAmmount;
        ethPool = ethPool + msg.value;
        uint256 tokensPaid = tokenPool - (invariant / ethPool - fee); // k = x * y <==> y = k / x, we payout the difference 
        require(tokensPaid >= minTokensOut, "Price has slipped lower than minimum"); // Ensure users are getting the price they want
        require(tokensPaid <= tokenPool, "Lacking pool tokens"); // Make sure we have enough tokens to pay out
        tokenPool = tokenPool - tokensPaid;
        invariant = tokenPool * ethPool;
        emit TokenPurchase(msg.sender, msg.value, tokensPaid);
        require(token.transfer(recipient, tokensPaid), "Tkn transfer fail");
    }

    function tokenToEth(address recipient, uint256 tokensIn, uint256 minEthOut) public hasLiquidity{
        uint256 fee = tokensIn / feeAmmount;
        token.transferFrom(msg.sender, address(this), tokensIn);
        tokenPool = tokenPool + tokensIn;
        uint256 ethPaid = ethPool - (invariant / tokenPool - fee); // k = x * y <==> x = k / y, we payout the difference
        require(ethPaid >= minEthOut, "Price has slipped lower than minimum"); // Ensure users are getting the price they want
        require(ethPaid <= ethPool, "Lacking pool eth"); // Make sure we have enough eth to pay out
        ethPool = ethPool - ethPaid;
        invariant = tokenPool * ethPool;
        emit EthPurchase(msg.sender, tokensIn, ethPaid);
        payable(recipient).call{value:ethPaid};
    }
}