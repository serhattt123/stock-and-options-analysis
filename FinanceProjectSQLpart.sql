CREATE TABLE UnderlyingSnapshot (
    Ticker       VARCHAR(10)   NOT NULL,
    SnapshotDate DATE          NOT NULL,
    SpotPrice    DECIMAL(10,4) NOT NULL,
    CONSTRAINT PK_UnderlyingSnapshot PRIMARY KEY (Ticker, SnapshotDate)
);

CREATE TABLE RiskFreeRate (
    SnapshotDate DATE          NOT NULL PRIMARY KEY,
    Rate         DECIMAL(6,4)  NOT NULL   -- annualized, e.g. 0.0450 = %4.50
);

CREATE TABLE OptionsChain (
    Ticker            VARCHAR(10)   NOT NULL,
    SnapshotDate      DATE          NOT NULL,
    Expiry            DATE          NOT NULL,
    OptionType        CHAR(4)       NOT NULL,   -- 'CALL' ya da 'PUT'
    Strike            DECIMAL(10,4) NOT NULL,
    ContractSymbol    VARCHAR(30)   NULL,
    LastTradeDate     DATETIME2     NULL,
    LastPrice         DECIMAL(10,4) NULL,
    Bid               DECIMAL(10,4) NULL,
    Ask               DECIMAL(10,4) NULL,
    Volume            INT           NULL,
    OpenInterest      INT           NULL,
    ImpliedVolatility DECIMAL(8,6)  NULL,
);

CREATE UNIQUE INDEX UQ_OptionsChain
ON OptionsChain (Ticker, SnapshotDate, Expiry, OptionType, Strike)
WITH (IGNORE_DUP_KEY = ON);