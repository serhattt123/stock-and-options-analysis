import numpy as np
from scipy.stats import norm



def bs_price(S, K, T, r, sigma, option_type="CALL", q=0.0):
    """q=0 verirsen düz Black-Scholes'e döner."""
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "CALL":
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == "PUT":
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'CALL' or 'PUT'")


def mc_price(
    S,
    K,
    T,
    r,
    sigma,
    option_type="CALL",
    n_paths=100_000,
    seed=42,
    q=0.0
):
    """Monte Carlo price under risk-neutral GBM.

    Single-step simulation for a European option.
    """

    rng = np.random.default_rng(seed)

    Z = rng.standard_normal(n_paths)

    S_T = S * np.exp((r - q - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)

    if option_type == "CALL":

        payoff = np.maximum(
            S_T - K,
            0
        )

    elif option_type == "PUT":

        payoff = np.maximum(
            K - S_T,
            0
        )

    else:
        raise ValueError(
            "option_type must be 'CALL' or 'PUT'"
        )

    discounted = (
        np.exp(-r * T)
        * payoff
    )

    price = discounted.mean()

    std_error = (
        discounted.std(ddof=1)
        / np.sqrt(n_paths)
    )

    return price, std_error


def no_arbitrage_lower_bound(S, K, T, r, q, option_type="CALL"):
    """Theoretical minimum price an option can trade at without creating
    an arbitrage opportunity."""
    if option_type == "CALL":
        bound = S * np.exp(-q * T) - K * np.exp(-r * T)
    elif option_type == "PUT":
        bound = K * np.exp(-r * T) - S * np.exp(-q * T)
    else:
        raise ValueError("option_type must be 'CALL' or 'PUT'")
    return max(bound, 0)


# Greeks calculation functions.
def calculate_greeks(S, K, T, r, sigma, option_type="CALL", q=0.0):
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    pdf_d1 = norm.pdf(d1)
    discount_q = np.exp(-q * T)
    discount_r = np.exp(-r * T)

    if option_type == "CALL":
        delta = discount_q * norm.cdf(d1)
        rho = K * T * discount_r * norm.cdf(d2)
        theta = (
            q * S * discount_q * norm.cdf(d1)
            - r * K * discount_r * norm.cdf(d2)
            - (S * discount_q * pdf_d1 * sigma) / (2 * np.sqrt(T))
        )
    elif option_type == "PUT":
        delta = -discount_q * norm.cdf(-d1)
        rho = -K * T * discount_r * norm.cdf(-d2)
        theta = (
            -q * S * discount_q * norm.cdf(-d1)
            + r * K * discount_r * norm.cdf(-d2)
            - (S * discount_q * pdf_d1 * sigma) / (2 * np.sqrt(T))
        )
    else:
        raise ValueError("option_type must be 'CALL' or 'PUT'")

    gamma = (discount_q * pdf_d1) / (S * sigma * np.sqrt(T))
    vega = S * discount_q * pdf_d1 * np.sqrt(T)

    return {
        "delta": delta,
        "gamma": gamma,
        "vega": vega / 100,
        "theta": theta / 365,
        "rho": rho / 100
    }
