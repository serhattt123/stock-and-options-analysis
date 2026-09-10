import pandas as pd
import numpy as np
import yfinance as yf
import pyodbc
from pathlib import Path


TICKERS = ["AAPL", "MSFT", "NVDA", "META", "TSLA", "JPM", "SPY"]

expiry = yf.Ticker(TICKERS[0]).options[0]
chain = yf.Ticker(TICKERS[0]).option_chain(expiry)

calls = chain.calls
puts = chain.puts

print(calls.dtypes)
print(calls.head())
print(calls.isna().sum())
print((calls["bid"] == 0).sum(), (calls["ask"] == 0).sum())


def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=.\\SQLEXPRESS;"
        "DATABASE=FinanceProject;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


def pick_expiries(ticker, near_days=35, far_days=120):
    """Pick the listed expiry closest to each target day count.
    Real expiries land on fixed weekdays, so we can't hit near_days/far_days
    exactly - we find the closest available one."""
    available = pd.to_datetime(yf.Ticker(ticker).options)
    today = pd.Timestamp.today().normalize()
    days_out = (available - today).days

    near_expiry = available[np.argmin(np.abs(days_out - near_days))]
    far_expiry = available[np.argmin(np.abs(days_out - far_days))]

    return near_expiry.strftime("%Y-%m-%d"), far_expiry.strftime("%Y-%m-%d")


def clean_chain(df):
    """Drop contracts with no usable market quote before they reach pricing."""
    df = df.copy()
    # no trades today != invalid contract
    df["volume"] = df["volume"].fillna(0)

    valid = (df["bid"] > 0) & (df["ask"] > 0) & (df["bid"] <= df["ask"])
    dropped = len(df) - valid.sum()
    print(f"{dropped} / {len(df)} kontrat kotasyonsuz olduğu için düşürüldü")

    return df[valid].reset_index(drop=True)


def get_risk_free_rate():
    """^IRX quotes the 13-week T-bill discount yield in percent (e.g. 4.85 = %4.85)."""
    irx = yf.Ticker("^IRX").history(period="5d")
    latest = irx["Close"].iloc[-1]
    return round(latest / 100, 4)


def already_snapshotted(cursor, ticker, snapshot_date):
    cursor.execute("""
        SELECT COUNT(*) FROM OptionsChain
        WHERE Ticker = ? AND SnapshotDate = ?
    """, ticker, snapshot_date)
    return cursor.fetchone()[0] > 0


def insert_underlying_snapshot(cursor, ticker, snapshot_date, spot_price):
    cursor.execute("""
        INSERT INTO UnderlyingSnapshot (Ticker, SnapshotDate, SpotPrice)
        VALUES (?, ?, ?)
    """, ticker, snapshot_date, spot_price)


def insert_risk_free_rate(cursor, snapshot_date, rate):
    cursor.execute("""
        INSERT INTO RiskFreeRate (SnapshotDate, Rate)
        VALUES (?, ?)
    """, snapshot_date, rate)


def insert_options_chain(cursor, ticker, snapshot_date, expiry, option_type, df):
    """df: clean_chain'den geçmiş calls ya da puts dataframe'i."""
    for row in df.itertuples(index=False):
        cursor.execute("""
            INSERT INTO OptionsChain (
                Ticker, SnapshotDate, Expiry, OptionType, Strike,
                ContractSymbol, LastTradeDate, LastPrice, Bid, Ask,
                Volume, OpenInterest, ImpliedVolatility
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ticker, snapshot_date, expiry, option_type, row.strike,
                       row.contractSymbol, row.lastTradeDate, row.lastPrice, row.bid, row.ask,
                       row.volume, row.openInterest, row.impliedVolatility)


def build_options_snapshot():
    snapshot_date = pd.Timestamp.today().normalize().date()
    conn = get_connection()  # FinanceMain.py'deki bağlantı stringiyle aynı
    cursor = conn.cursor()

    r = get_risk_free_rate()
    insert_risk_free_rate(cursor, snapshot_date, r)

    for ticker in TICKERS:
        if already_snapshotted(cursor, ticker, snapshot_date):
            print(f"{ticker}: bugün için zaten kayıtlı, atlanıyor")
            continue

        spot = yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]
        insert_underlying_snapshot(cursor, ticker, snapshot_date, spot)

        near_expiry, far_expiry = pick_expiries(ticker)

        for expiry in (near_expiry, far_expiry):
            chain = yf.Ticker(ticker).option_chain(expiry)

            for option_type, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                cleaned = clean_chain(df)
                insert_options_chain(
                    cursor, ticker, snapshot_date, expiry, option_type, cleaned)

        print(f"{ticker}: kaydedildi")

    conn.commit()
    cursor.close()
    conn.close()


build_options_snapshot()
