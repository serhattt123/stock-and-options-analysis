import pyodbc


def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=.\\SQLEXPRESS;"
        "DATABASE=FinanceProject;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


def already_snapshotted(cursor, ticker, snapshot_date):
    cursor.execute("""
        SELECT COUNT(*) FROM OptionsChain
        WHERE Ticker = ? AND SnapshotDate = ?
    """, ticker, snapshot_date)

    return cursor.fetchone()[0] > 0


def insert_underlying_snapshot(cursor, ticker, snapshot_date, spot_price, dividend_yield):
    cursor.execute("""
        INSERT INTO UnderlyingSnapshot
            (Ticker, SnapshotDate, SpotPrice, DividendYield)
        VALUES (?, ?, ?, ?)
    """, ticker, snapshot_date, spot_price, dividend_yield)


def insert_risk_free_rate(cursor, snapshot_date, rate):
    cursor.execute("""
        IF EXISTS (
            SELECT 1 FROM RiskFreeRate
            WHERE SnapshotDate = ?
        )
            UPDATE RiskFreeRate
            SET Rate = ?
            WHERE SnapshotDate = ?;
        ELSE
            INSERT INTO RiskFreeRate (SnapshotDate, Rate)
            VALUES (?, ?);
    """, snapshot_date, rate, snapshot_date, snapshot_date, rate)


def insert_options_chain(
    cursor,
    ticker,
    snapshot_date,
    expiry,
    option_type,
    df
):
    """Insert cleaned option-chain data into SQL Server."""

    for row in df.itertuples(index=False):
        cursor.execute("""
            INSERT INTO OptionsChain (
                Ticker,
                SnapshotDate,
                Expiry,
                OptionType,
                Strike,
                ContractSymbol,
                LastTradeDate,
                LastPrice,
                Bid,
                Ask,
                Volume,
                OpenInterest,
                ImpliedVolatility
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
                       ticker,
                       snapshot_date,
                       expiry,
                       option_type,
                       row.strike,
                       row.contractSymbol,
                       row.lastTradeDate,
                       row.lastPrice,
                       row.bid,
                       row.ask,
                       row.volume,
                       row.openInterest,
                       row.impliedVolatility
                       )
