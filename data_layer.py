import pandas as pd
import yfinance as yf

from db_utils import (
    get_connection,
    already_snapshotted,
    insert_underlying_snapshot,
    insert_risk_free_rate,
    insert_options_chain
)


TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "META",
    "TSLA",
    "JPM",
    "SPY"
]


def pick_expiries(ticker, near_days=35, far_days=120):
    """Pick the listed expiry closest to each target day count.

    Real expiries land on fixed weekdays, so we cannot
    hit near_days/far_days exactly.
    """

    available = pd.to_datetime(
        yf.Ticker(ticker).options
    )

    today = pd.Timestamp.today().normalize()

    days_out = (available - today).days

    near_expiry = available[
        abs(days_out - near_days).argmin()
    ]

    far_expiry = available[
        abs(days_out - far_days).argmin()
    ]

    return (
        near_expiry.strftime("%Y-%m-%d"),
        far_expiry.strftime("%Y-%m-%d")
    )


def clean_chain(df):
    """Remove option contracts without usable market quotes."""

    df = df.copy()

    # No trades today does not mean invalid contract.
    df["volume"] = df["volume"].fillna(0)

    valid = (
        (df["bid"] > 0)
        & (df["ask"] > 0)
        & (df["bid"] <= df["ask"])
    )

    dropped = len(df) - valid.sum()

    print(
        f"{dropped} / {len(df)} kontrat "
        f"kotasyonsuz olduğu için düşürüldü"
    )

    return df[valid].reset_index(drop=True)


def get_risk_free_rate():
    """Get the latest 13-week T-bill yield from ^IRX."""

    irx = yf.Ticker("^IRX").history(period="5d")

    latest = irx["Close"].iloc[-1]

    return round(latest / 100, 4)


def build_options_snapshot():

    snapshot_date = (
        pd.Timestamp.today()
        .normalize()
        .date()
    )

    conn = get_connection()
    cursor = conn.cursor()

    # Get current risk-free rate
    r = get_risk_free_rate()

    insert_risk_free_rate(
        cursor,
        snapshot_date,
        r
    )

    for ticker in TICKERS:

        if already_snapshotted(
            cursor,
            ticker,
            snapshot_date
        ):
            print(
                f"{ticker}: bugün için zaten kayıtlı, atlanıyor"
            )
            continue

        # Current stock price
        spot = (
            yf.Ticker(ticker)
            .history(period="1d")["Close"]
            .iloc[-1]
        )

        insert_underlying_snapshot(
            cursor,
            ticker,
            snapshot_date,
            spot
        )

        # Select near and far expiries
        near_expiry, far_expiry = pick_expiries(ticker)

        for expiry in (
            near_expiry,
            far_expiry
        ):

            chain = yf.Ticker(
                ticker
            ).option_chain(expiry)

            for option_type, df in [
                ("CALL", chain.calls),
                ("PUT", chain.puts)
            ]:

                cleaned = clean_chain(df)

                insert_options_chain(
                    cursor,
                    ticker,
                    snapshot_date,
                    expiry,
                    option_type,
                    cleaned
                )

        print(f"{ticker}: kaydedildi")

    conn.commit()

    cursor.close()
    conn.close()
