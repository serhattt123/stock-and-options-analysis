import numpy as np
from scipy.stats import norm


def bs_price(
    S,
    K,
    T,
    r,
    sigma,
    option_type="CALL"
):
    """European option price under Black-Scholes.

    S: spot price
    K: strike price
    T: time to maturity in years
    r: annualized risk-free rate
    sigma: annualized volatility
    """

    d1 = (
        np.log(S / K)
        + (r + 0.5 * sigma**2) * T
    ) / (
        sigma * np.sqrt(T)
    )

    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "CALL":

        return (
            S * norm.cdf(d1)
            - K
            * np.exp(-r * T)
            * norm.cdf(d2)
        )

    elif option_type == "PUT":

        return (
            K
            * np.exp(-r * T)
            * norm.cdf(-d2)
            - S
            * norm.cdf(-d1)
        )

    else:
        raise ValueError(
            "option_type must be 'CALL' or 'PUT'"
        )


def mc_price(
    S,
    K,
    T,
    r,
    sigma,
    option_type="CALL",
    n_paths=100_000,
    seed=42
):
    """Monte Carlo price under risk-neutral GBM.

    Single-step simulation for a European option.
    """

    rng = np.random.default_rng(seed)

    Z = rng.standard_normal(n_paths)

    S_T = S * np.exp(
        (r - 0.5 * sigma**2) * T
        + sigma * np.sqrt(T) * Z
    )

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
