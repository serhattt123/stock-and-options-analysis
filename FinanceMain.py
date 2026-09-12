import pandas as pd

from data_layer import build_options_snapshot
from db_utils import get_connection
from pricing import bs_price, mc_price


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

    # SQL CHAR columns can include trailing spaces (for example, "PUT ").
    df["OptionType"] = df["OptionType"].str.strip().str.upper()

    df["T"] = (pd.to_datetime(df["Expiry"]) -
               pd.Timestamp(snapshot_date)).dt.days / 365

    df = df[df["T"] > 0]

    df["mid_price"] = (df["Bid"] + df["Ask"]) / 2

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

    return df


def main():

    # Example pricing
    S = 230
    K = 230
    T = 30 / 365
    r = 0.045
    sigma = 0.28

    bs = bs_price(
        S,
        K,
        T,
        r,
        sigma,
        "CALL"
    )

    mc, se = mc_price(
        S,
        K,
        T,
        r,
        sigma,
        "CALL"
    )

    print(f"Black-Scholes: {bs:.4f}")
    print(
        f"Monte Carlo:   "
        f"{mc:.4f} ± {1.96 * se:.4f}"
    )

    # Build today's options snapshot
    build_options_snapshot()
    print("Options snapshot built successfully.")

    snapshot_date = pd.Timestamp.today().normalize().date()
    df = price_snapshot(snapshot_date)
    print(df[["Ticker", "Expiry", "OptionType",
          "mid_price", "bs_price", "price_diff"]])


if __name__ == "__main__":
    main()
