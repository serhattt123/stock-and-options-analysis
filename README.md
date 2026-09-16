# Options Pricing & Analysis

A quantitative finance project for collecting real-world options market data, storing it in SQL Server, pricing European options with the Black-Scholes model, calculating option Greeks, and analyzing differences between theoretical and observed market prices.

## Features

* Real-time options data collection using `yfinance`
* SQL Server data storage
* Black-Scholes option pricing
* Monte Carlo pricing with risk-neutral GBM
* Dividend yield adjustment
* No-arbitrage lower-bound checks
* Option Greeks:

  * Delta
  * Gamma
  * Vega
  * Theta
  * Rho
* Bid-ask midpoint pricing
* Pricing error analysis
* Implied volatility analysis
* Volatility smile visualization
* Greek curves
* Option profit/loss at expiration

## Project Structure

```text
OptionsPricing/
│
├── main.py
├── pricing.py
├── data_layer.py
├── db_utils.py
├── visualization.py
└── README.md
```

### `pricing.py`

Contains the quantitative models:

* Black-Scholes pricing
* Monte Carlo pricing
* No-arbitrage lower bounds
* Option Greeks

### `data_layer.py`

Responsible for collecting market data from Yahoo Finance and creating daily option snapshots.

The project currently tracks:

```text
AAPL
MSFT
NVDA
META
TSLA
JPM
SPY
```

For each underlying, near- and far-dated option expirations are collected.

### `db_utils.py`

Handles the connection between Python and SQL Server and inserts market data into the database.

### `visualization.py`

Contains plotting functions for:

* Implied volatility vs. strike
* Greeks vs. strike
* Option profit/loss at expiration

### `main.py`

Runs the complete workflow:

1. Test Black-Scholes and Monte Carlo pricing
2. Build the current options snapshot
3. Load market data from SQL Server
4. Calculate theoretical prices
5. Calculate Greeks
6. Apply no-arbitrage filtering
7. Calculate pricing errors
8. Display analysis results
9. Generate visualizations

## Data Pipeline

```text
Yahoo Finance
      │
      ▼
Data Collection
      │
      ▼
SQL Server
      │
      ├── UnderlyingSnapshot
      ├── RiskFreeRate
      └── OptionsChain
              │
              ▼
       Pricing Engine
              │
       ┌──────┴──────┐
       ▼             ▼
Black-Scholes      Greeks
       │
       ▼
Pricing Error Analysis
       │
       ▼
Visualization
```

## Pricing Models

### Black-Scholes

The project uses the Black-Scholes-Merton model with continuous dividend yield:

$$
C = Se^{-qT}N(d_1)-Ke^{-rT}N(d_2)
$$

$$
P = Ke^{-rT}N(-d_2)-Se^{-qT}N(-d_1)
$$

where:

* \(S\) = underlying price
* \(K\) = strike price
* \(T\) = time to expiration
* \(r\) = risk-free interest rate
* \(q\) = dividend yield
* \(\sigma\) = implied volatility

### Monte Carlo

European option prices can also be estimated using risk-neutral Geometric Brownian Motion:

$$
S_T =
S_0
\exp
\left[
(r-q-\frac{1}{2}\sigma^2)T
+
\sigma\sqrt{T}Z
\right]
$$

The implementation uses 100,000 simulation paths with a fixed random seed for reproducibility.

## Market Price Comparison

The observed option price is represented by the bid-ask midpoint:

$$
P_{mid}=\frac{Bid+Ask}{2}
$$

The pricing difference is:

$$
Price\ Difference =
BS\ Price-P_{mid}
$$

and the percentage difference is:

$$
Percentage\ Difference =
\frac{BS\ Price-P_{mid}}{P_{mid}}\times100
$$

The analysis uses the option's market-implied volatility as the volatility input for Black-Scholes.

Therefore, this analysis measures how closely Black-Scholes reprices the observed market price when supplied with the market's implied volatility. It should not be interpreted as a pure out-of-sample prediction test.

## Option Greeks

The project calculates the main Black-Scholes Greeks:

| Greek | Description                                                  |
| ----- | ------------------------------------------------------------ |
| Delta | Sensitivity to a change in the underlying price              |
| Gamma | Sensitivity of Delta to the underlying price                 |
| Vega  | Sensitivity to a 1 percentage-point change in volatility     |
| Theta | Approximate daily time decay                                 |
| Rho   | Sensitivity to a 1 percentage-point change in interest rates |

## Risk-Free Rate

The risk-free rate is obtained from the 13-week U.S. Treasury Bill yield (`^IRX`) through Yahoo Finance.

The same daily risk-free rate is currently used across the contracts in a snapshot.

## Database

The project uses Microsoft SQL Server Express.

Main tables:

```text
UnderlyingSnapshot
RiskFreeRate
OptionsChain
```

`OptionsChain` stores market information including:

* Ticker
* Snapshot date
* Expiration
* Option type
* Strike
* Contract symbol
* Last trade date
* Last price
* Bid
* Ask
* Volume
* Open interest
* Implied volatility

## Example Results

A test case with:

```text
Underlying Price : $230
Strike Price     : $230
Time to Expiry   : 30 days
Risk-Free Rate   : 4.5%
Volatility       : 28%
```

produces Black-Scholes and Monte Carlo prices that are close to each other, with the Black-Scholes result falling within the Monte Carlo 95% confidence interval.

A market snapshot can contain thousands of option contracts. For each contract, the project calculates theoretical price, pricing difference, percentage difference, and Greeks.

## Technologies

* Python
* NumPy
* Pandas
* SciPy
* Matplotlib
* yfinance
* pyodbc
* Microsoft SQL Server Express

## Future Improvements

* Historical volatility-based Black-Scholes pricing
* More accurate maturity-specific risk-free rates
* Bid-ask spread and liquidity analysis
* Moneyness-based analysis
* Historical pricing-error tracking
* Monte Carlo comparison on selected real-world contracts
* Additional volatility-surface visualizations
* Automated daily data collection
* More advanced option pricing models

## Disclaimer

This project is developed for educational and quantitative-finance research purposes. The models and market data are not intended to provide investment advice or trading recommendations.
