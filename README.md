# AstroSwap
A Uniswap Clone (bassed off V1)

## Concept Source
https://hackmd.io/@HaydenAdams/HJ9jLsfTz

## Description
This is a two part token exchange system. The first part of it is an exchange contract that allows people to exchange tokens for ether and vice vera. The second part of it is a contract factory that spawns these exchanges and allows users to transfer tokens for tokens directly.

## Exchange Details
Contract: `AstroSwapExchange`

Each contract has two pools of liquidiy:
- An Ether pool
- An ERC20 token pool

### Price calculations

The exchange's goal is to make sure the product of the two pools is constant (this is called the invariant): `ethPool * tokenPool = invariant`. This is called a fixed product pool.

This means that when eth comes in, ethPool increases and therefore tokenPool must decrease to keep the product the same. This decrease is what is paid out to the users. 

This method means that the overall "value" of the liquidity stays constant by looking at the supply of each.

Example with math:

Liquidiy pools:
- Ether: 100 wei
- Tokens: 100 tokens
- Invariant is 100 * 100 = 10000

Order of events:
- User sends 10 wei to exchange
- New ether pool: 110 wei
- To calculate the amount paid out, we turn `i = e * t` into `t = i / e`. Here this comes out to 100000 / 110 = 909 (a decrease of 81 tokens).
- The contract pays out 81 tokens to the user.

*Note: In the real contract, there are allways fees that will be taken as a payment to investors.

A part of the liquidity grows and growns, the price of buying the other will increase (supply & demand).

Since solidity dose not have floats, things are allways so the exchange keeps more to avoid leaking liquidity.

### Investment
For each pool to work, it needs investments of both units being traded. This type of liquidity demands that when investments are put in, they have equal value. So if 1 token costs 1 wei, then you would invest equal amounts. But if on the other hand, 1 token cost 5 wei, you would invest 5 wei for each token put in.

If this is not followed, the price paid will be off and users will be able to get good deals untill the pool reaches equilibrium.

### Variables
- `uint256 public ethPool`: The amount of ether in the ether pool
- `uint256 public tokenPool`: The amount of tokens in the token pool
- `uint256 public invariant`: The fixed product pool
- `uint256 public feeAmmount`: The fee rate for exchanges on this contract. Stored as the denumerator of a fraction. Ex: `feeAmmount = 400` means that 1/400 of the amount exchanged will be taken as a fee or 0.25%
- `IERC20 public token`: The token being traded on this contract
- `AstroSwapFactory public factory`: The factory that creates the exchange (used for routing tokenToToken exchanges)
- `uint256 public totalShares`: The total amount of investor shares
- `mapping (address => uint256) public investorShares`: The shares held by each investor. When the first investor seed invests, they are given 10000 shares. When others invest, they are given `ethPool * totalShares / ethPaid` shares, so proportional to how much they are increasing the pools.

### Functions
- `seedInvest(uint256 tokenInvestment) public payable`: A function that seeds the contract with liquidity. If investors dont want to loose money, they should **invest equal values of tokens and ether**. This will set the investment rate for others
- `invest(uint256 maxTokensInvested) public payable`: Allows investors to invest after seeding. The investment `investEth/investTokens` will be equal to the current `ethPool/tokenPool`.
- `divest(uint256 shares) public`: Cash out shares for a part of the liquidity proportional to your amount of shares being cashed out.
- `ethToTokenPrivate(uint256 value) private returns(uint256 tokenToPay)`: A function used to do the price math and update variables. Will be used by other functions to transfer funds etc.
- `tokenToEthPrivate(uint256 tokensIn) private returns(uint256 ethToPay)`: Same as above, but for tokens to ether trades
- `ethToToken(address recipient, uint256 minTokensOut) public payable hasLiquidity returns(uint256 tokensPaid)`: Allows users to exchange ether for tokens.
  - Recipient: The address that will receive the tokens (if you want it to go to your wallet, use your own address)
  - minTokensOut: The minimum amount of tokens that the user is willing to receive. This exists to make sure that users don't send a transaction with one quote, and then when it mines they got a much worse deal.
- `tokenToEth(address recipient, uint256 tokensIn, uint256 minEthOut) public hasLiquidity returns(uint256 ethPaid)`: Same as above, but for tokens to ether trades
- `tokenToToken(address recipient, address tokenOutAddress, uint256 tokensIn, uint256 minTokensOut) public hasLiquidity`: Allows users to trade tokens for tokens in one transaction directly.
  - Recipient: The address that will receive the tokens (if you want it to go to your wallet, use your own address)
  - tokenOutAddress: The address of the token the users want to receive
  - tokensIn: The ammount of tokens being spent for the trade
  - minTokensOut: The minimum amount of tokens that the user is willing to receive. This exists to make sure that users don't send a transaction with one quote, and then when it mines they got a much worse deal.
  - *Note: This trade takes a fee on both sides of the transfer since two pools are being used.
  - **How it works**:
    - In our contract, turn tokens into ether.
    - Call the factory contract to get the address of the other token's exchange.
    - Send that exchange a `ethToToken` request with the same same recipient.
    - That function will return the amount going to be paid and that is compared to the minimum amount the user is willing to receive.
#### Quote functions:
These are a bunch of functions to get information about the prices of trades, amounts needed to invest and other viewing functions.
- `investQuoteFromEth(uint256 ethPaid) public view returns (uint256 tokensRequired)`: Takes in the amount of eth being paid and returns the amount of tokens needed to be invested to keep the balance.
- `investQuoteFromTokens`: Same as above, but instead of basing the investment off eth, it is based off tokens being proposed.
- `getShares(address investor) public view returns (uint256 shareCount)`: Get an investor's share count
- Tranaction quotes:
  - `getEthToTokenQuote(uint256 ethValue) public view returns (uint256 tokenQuote)`
  - `getTokenToEthQuote(uint256 tokenValue) public view returns (uint256 ethQuote)`
  - `getTokenToTokenQuote(uint256 tokenValue, address tokenOutAddress) public view returns (uint256 tokenQuote)`
  - These all give the amount that will be paid out based on the amount going in.
### Events
- `event TokenPurchase(address indexed user, address indexed recipient, uint256 ethIn, uint256 tokensOut)`: A user has purchased tokens using ether
- `event EthPurchase(address indexed user, address indexed recipient, uint256 tokensIn, uint256 ethOut)`: A user has purchased ether using tokens
- `event TokenToTokenOut(address indexed user, address indexed recipient, address indexed tokenExchangeAddress, uint256 tokensIn, uint256 ethTransfer)`: The master TokenToToken event. Keeps track of the first call that trades your tokens for ether in this contract and then sends the ether off to another contract to be turned back into tokens.
- `event Investment(address indexed user, uint256 indexed sharesPurchased, uint256 ethInvested, uint256 tokensInvested)`
- `event Divestment(address indexed user, uint256 indexed sharesBurned, uint256 ethDivested, uint256 tokensDivested)`

### Gas price benchmarks:
- constructor      -  avg: 1237526  avg (confirmed): 1237526  low: 1237515  high: 1237527
- seedInvest       -  avg:  148157  avg (confirmed):  158386  low:   22426  high:  164268
- invest           -  avg:   67089  avg (confirmed):   69591  low:   23453  high:   82157
- tokenToEth       -  avg:   61853  avg (confirmed):   65024  low:   22964  high:   71017
- ethToToken       -  avg:   57754  avg (confirmed):   62588  low:   22858  high:   62667
- divest           -  avg:   49329  avg (confirmed):   56030  low:   22527  high:   74707

## Factory details:
The factory is used to create new exchanges that are garunteed to be the exact AstroSwapExchange. It also facilitates finding the exchange linked to a token and vice versa.

### How it works:
- Anyone can send a transaction to `addTokenExchange` with the address of the token they want to be traded.
- The factory then creates a new exchange and emits a event with the address of the new exchange. This exchange is also added to the two way mapping of tokens to exchanges.
- When someone has an exchange and wants to find the token, they can use `convertExchangeToToken` to get the token being traded. If you have a token and want to find the exchange, use `convertTokenToExchange`. These functions will return the 0x0 address if there is no exchange for that token or if that is not a valid exchange.

### Variables
- `uint256 public feeRate`: The fee rate that will be given to all contracts that are created by the factory.
- `uint256 public exchangeCount`: The number of exchanges that have been created by the factory.
- `mapping(address => address) public tokenToExchange` + `mapping(address => address) public exchangeToToken`: Two one-way mappings of tokens to exchanges and exchanges to tokens, creating a two way mapping.

### Functions 
- `addTokenExchange(address tokenAddress) public`: Takes in a token address and creates an exchange for it, adding it to the mapping. Emits a `TokenExchangeAdded` event
- `convertTokenToExchange(address token) public view returns (address exchange)`: Takes in a token and returns the exchange that is trades it.
- `convertExchangeToToken(address exchange) public view returns (address token)`: Takes in an exchange and returns the token that is traded in that exchange.

### Events
- `TokenExchangeAdded(address indexed tokenExchange, address indexed tokenAddress)`: Emitted when a new exchange is created throught the factory. 
  - `tokenExchange`: The address of the new exchange
  - `tokenAddress`: The address of the token being traded

## Brownie Setup
- Install all the dependencies in requirements.txt using `pip install -r requirements.txt` (preferably using a virtual environment)
- Add a .env file to /brownie with in it:
  - An infura key for easy network access in `WEB3_INFURA_PROJECT_ID` 
  - An etherscan API tokoen for contract verification in `ETHERSCAN_TOKEN`
- `cd brownie` && `brownie compile` to compile the smart contracts.
- Use `brownie test` to test the smart contracts.
- Use `brownie run scripts\deploy.py` to deploy the factory to a local network. (Add the --network NETWORKNAME flag to deploy it to a real network).

### Brownie expectations:
This project expects you to have accounts added to your brownie install. I have a bunch of test accounts and my naming convention for them is `test1, test2, test3...`. This is used in `smart_get_account` in helpers.py to get me accounts depending on if I am on a local network or a real network. If you want to use your own accounts with a differnt naming convention, comment out `return accounts.load("test"+str(index))` and add your account names to the `realAccountNames` list in `deploy.py` (the way this project is structured, I dose not store the accounts and asks for them over and over again so I really recommend using accounts without a password or you will be stuck typing it in a million times).

## Warnings
This contract has not been audited and I do not expect it to be perfect. It has been tested extensively and is working as intended on a local machine and on the Rinkeby Testnet but might not work on other networks.
It comes as is with no warranty and is not intended for use in production.