from __future__ import annotations


def sizing_by_var(risk_budget: float, var_value: float | None, max_position: float = 1.0) -> float:
    if var_value is None or var_value <= 0:
        return 0.0
    return float(max(0.0, min(max_position, risk_budget / var_value)))


def sizing_by_cvar(risk_budget: float, cvar_value: float | None, max_position: float = 1.0) -> float:
    if cvar_value is None or cvar_value <= 0:
        return 0.0
    return float(max(0.0, min(max_position, risk_budget / cvar_value)))


def kelly_fraction(prob_win: float, payoff_ratio: float, max_fraction: float = 0.25) -> float:
    if payoff_ratio <= 0:
        return 0.0
    fraction = prob_win - (1 - prob_win) / payoff_ratio
    return float(max(0.0, min(max_fraction, fraction)))


def apply_drawdown_limit(position_fraction: float, expected_drawdown: float | None, drawdown_limit: float = 0.20) -> float:
    if expected_drawdown is None:
        return float(max(0.0, position_fraction * 0.5))
    drawdown = abs(expected_drawdown)
    if drawdown <= 0:
        return float(max(0.0, position_fraction))
    scale = min(1.0, drawdown_limit / drawdown)
    return float(max(0.0, position_fraction * scale))


def position_sizing_summary(risk_metrics: dict, distribution: dict, risk_budget: float = 0.02) -> dict:
    var_size = sizing_by_var(risk_budget, risk_metrics.get("var_95"))
    cvar_size = sizing_by_cvar(risk_budget, risk_metrics.get("cvar_95"))
    upside = max(distribution.get("p90_return", 0.0), 0.0)
    downside = abs(min(distribution.get("p10_return", 0.0), 0.0))
    payoff = upside / downside if downside > 0 else 0.0
    kelly = kelly_fraction(distribution.get("prob_up", 0.0), payoff)
    constrained = apply_drawdown_limit(min(var_size, cvar_size, kelly if kelly > 0 else var_size), risk_metrics.get("max_drawdown"))
    return {
        "risk_budget": risk_budget,
        "var_based_fraction": var_size,
        "cvar_based_fraction": cvar_size,
        "kelly_fraction": kelly,
        "drawdown_limited_fraction": constrained,
    }
