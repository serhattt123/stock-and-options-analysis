import numpy as np
import matplotlib.pyplot as plt


def plot_volatility_smile(df, ticker, expiry, option_type="PUT"):
    subset = df[
        (df["Ticker"] == ticker)
        & (df["Expiry"] == expiry)
        & (df["OptionType"] == option_type)
    ].sort_values("Strike")

    plt.figure(figsize=(8, 5))
    plt.plot(subset["Strike"], subset["ImpliedVolatility"], marker="o")
    plt.axvline(subset["SpotPrice"].iloc[0], color="gray",
                linestyle="--", label="Spot")
    plt.xlabel("Strike")
    plt.ylabel("Implied Volatility")
    plt.title(f"Volatility Smile — {ticker} {option_type} ({expiry})")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()


def plot_greek_curve(df, ticker, expiry, option_type, greek="delta"):
    subset = df[
        (df["Ticker"] == ticker)
        & (df["Expiry"] == expiry)
        & (df["OptionType"] == option_type)
    ].sort_values("Strike")

    plt.figure(figsize=(8, 5))
    plt.plot(subset["Strike"], subset[greek], marker="o")
    plt.axvline(subset["SpotPrice"].iloc[0], color="gray",
                linestyle="--", label="Spot")
    plt.xlabel("Strike")
    plt.ylabel(greek.capitalize())
    plt.title(
        f"{greek.capitalize()} vs Strike — {ticker} {option_type} ({expiry})")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()


def plot_payoff(row):
    """row: price_snapshot()'tan gelen tek bir kontrat satırı (df.loc[idx])."""
    K = row["Strike"]
    premium = row["mid_price"]
    S_range = np.linspace(0.5 * K, 1.5 * K, 200)

    if row["OptionType"] == "CALL":
        payoff = np.maximum(S_range - K, 0) - premium
    else:
        payoff = np.maximum(K - S_range, 0) - premium

    plt.figure(figsize=(8, 5))
    plt.plot(S_range, payoff)
    plt.axhline(0, color="gray", linewidth=0.5)
    plt.axvline(K, color="gray", linestyle="--", linewidth=0.5, label="Strike")
    plt.axvline(row["SpotPrice"], color="green",
                linestyle=":", label="Current Spot")
    plt.xlabel("Underlying price at expiry")
    plt.ylabel("Profit / Loss")
    plt.title(f"Payoff — {row['Ticker']} {row['OptionType']} K={K:.0f}")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()
