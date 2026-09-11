# Options Pricing & Market Analysis

A financial data analysis project focused on collecting real-world options market data and applying quantitative pricing models.

## Current Progress

* Collected real-time options chain data using `yfinance`
* Stored options data in **SQL Server**
* Stored underlying asset prices and risk-free rates
* Implemented data cleaning and snapshot management
* Implemented **Black-Scholes** pricing for European-style options
* Implemented **Monte Carlo** pricing using Geometric Brownian Motion
* Compared Black-Scholes theoretical prices with market **bid-ask mid prices**
* Calculated pricing differences and percentage errors

## Technologies

* Python
* Pandas
* NumPy
* SciPy
* yfinance
* SQL Server
* pyodbc

## Pricing Analysis

The current analysis uses the market's implied volatility as the volatility input for the Black-Scholes model and compares the resulting theoretical price with the observed market mid price.

Future work will include deeper error analysis, visualization, and further comparison of pricing models.

