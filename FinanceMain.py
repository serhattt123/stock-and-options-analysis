import pandas as pd

from data_layer import build_options_snapshot
from db_utils import get_connection
from pricing import bs_price, mc_price, no_arbitrage_lower_bound, calculate_greeks


def price_snapshot(snapshot_date):
    """Run bs_price/mc_price on every contract from a snapshot, using the
    market's own implied volatility as sigma - checks that the engine
    reproduces market prices when fed the same inputs the market used."""
    conn = get_connection()
    query = """
        SELECT
            oc.Ticker, oc.Expiry, oc.OptionType, oc.Strike,
            oc.LastPrice, oc.Bid, oc.Ask, oc.ImpliedVolatility,
            us.SpotPrice,
            COALESCE(us.DividendYield, 0.0) AS DividendYield,
            rfr.Rate
        FROM OptionsChain oc
        JOIN UnderlyingSnapshot us
            ON oc.Ticker = us.Ticker AND oc.SnapshotDate = us.SnapshotDate
        JOIN RiskFreeRate rfr
            ON oc.SnapshotDate = rfr.SnapshotDate
        WHERE oc.SnapshotDate = ?
    """
    df = pd.read_sql(query, conn, params=[snapshot_date])
    conn.close()

    # SQL CHAR columns may include trailing spaces (for example, "PUT ").
    df["OptionType"] = df["OptionType"].str.strip().str.upper()

    df["T"] = (pd.to_datetime(df["Expiry"]) -
               pd.Timestamp(snapshot_date)).dt.days / 365

    df = df[df["T"] > 0]

    df["mid_price"] = (df["Bid"] + df["Ask"]) / 2

    # ---- NEW: no-arbitrage filter ----
    df["lower_bound"] = df.apply(
        lambda row: no_arbitrage_lower_bound(
            row["SpotPrice"], row["Strike"], row["T"], row["Rate"],
            row["DividendYield"], row["OptionType"]
        ),
        axis=1
    )

    before = len(df)
    df = df[df["mid_price"] >= df["lower_bound"]].reset_index(drop=True)
    print(f"{before - len(df)} kontrat no-arbitrage alt sınırını ihlal ettiği için düşürüldü")
    # ---- END OF NEW SECTION ----

    df["bs_price"] = df.apply(
        lambda row: bs_price(
            row["SpotPrice"],
            row["Strike"],
            row["T"],
            row["Rate"],
            row["ImpliedVolatility"],
            row["OptionType"],
            q=row["DividendYield"]
        ),
        axis=1
    )
    df["price_diff"] = df["bs_price"] - df["mid_price"]

    greeks = df.apply(
        lambda row: calculate_greeks(
            row["SpotPrice"], row["Strike"], row["T"], row["Rate"],
            row["ImpliedVolatility"], row["OptionType"], q=row["DividendYield"]
        ),
        axis=1, result_type="expand"
    )
    df = pd.concat([df, greeks], axis=1)

    return df


def main():

    # Example option pricing
    S = 230
    K = 230
    T = 30 / 365
    r = 0.045
    sigma = 0.28

    bs = bs_price(
        S, K, T, r, sigma, "CALL"
    )

    mc, se = mc_price(
        S, K, T, r, sigma, "CALL"
    )

    print("\n" + "=" * 60)
    print("OPTION PRICING EXAMPLE")
    print("=" * 60)
    print(f"Underlying Price : ${S:.2f}")
    print(f"Strike Price     : ${K:.2f}")
    print(f"Time to Expiry   : {T:.4f} years")
    print(f"Risk-Free Rate   : {r:.2%}")
    print(f"Volatility       : {sigma:.2%}")
    print("-" * 60)
    print(f"Black-Scholes    : ${bs:.4f}")
    print(f"Monte Carlo      : ${mc:.4f}")
    print(f"95% Confidence   : ± ${1.96 * se:.4f}")

    # Build today's options snapshot
    build_options_snapshot()

    print("\n" + "=" * 60)
    print("OPTIONS SNAPSHOT")
    print("=" * 60)
    print("Options snapshot built successfully.")

    snapshot_date = pd.Timestamp.today().normalize().date()

    df = price_snapshot(snapshot_date)

    print(f"Snapshot Date    : {snapshot_date}")
    print(f"Contracts Analyzed: {len(df):,}")

    # AAPL PUT example
    one_slice = df[
        (df["Ticker"] == "AAPL")
        & (df["Expiry"] == df["Expiry"].unique()[0])
        & (df["OptionType"] == "PUT")
    ].sort_values("Strike")

    print("\n" + "=" * 60)
    print("GREEKS - AAPL PUT OPTIONS")
    print("=" * 60)

    print(
        one_slice[
            [
                "Strike",
                "SpotPrice",
                "mid_price",
                "bs_price",
                "delta",
                "gamma",
                "vega",
                "theta",
                "rho"
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}"
        )
    )

    # Pricing error
    df["pct_diff"] = (
        df["price_diff"] / df["mid_price"] * 100
    )

    print("\n" + "=" * 60)
    print("PRICING ERROR ANALYSIS")
    print("=" * 60)

    stats = df["pct_diff"].describe()

    print(f"Number of Contracts : {stats['count']:.0f}")
    print(f"Mean Error          : {stats['mean']:.2f}%")
    print(f"Standard Deviation  : {stats['std']:.2f}%")
    print(f"Minimum Error       : {stats['min']:.2f}%")
    print(f"25th Percentile     : {stats['25%']:.2f}%")
    print(f"Median Error        : {stats['50%']:.2f}%")
    print(f"75th Percentile     : {stats['75%']:.2f}%")


    # Worst contract
    worst_idx = df["price_diff"].abs().idxmax()
    worst = df.loc[worst_idx]

    print("\n" + "=" * 60)
    print("WORST PRICING DIFFERENCE")
    print("=" * 60)

    print(f"Ticker              : {worst['Ticker']}")
    print(f"Option Type         : {worst['OptionType']}")
    print(f"Expiry              : {worst['Expiry']}")
    print(f"Strike              : ${worst['Strike']:.2f}")
    print(f"Spot Price          : ${worst['SpotPrice']:.2f}")
    print(f"Market Mid Price    : ${worst['mid_price']:.2f}")
    print(f"Black-Scholes Price : ${worst['bs_price']:.2f}")
    print(f"Price Difference    : ${worst['price_diff']:.2f}")
    print(f"Percentage Difference: {worst['pct_diff']:.2f}%")
    print(f"Implied Volatility  : {worst['ImpliedVolatility']:.2%}")
    print(f"Risk-Free Rate      : {worst['Rate']:.2%}")
    print(f"Dividend Yield      : {worst['DividendYield']:.2%}")

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

