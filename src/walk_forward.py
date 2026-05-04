from __future__ import annotations

import pandas as pd

from backtest import run_backtest


def walk_forward_backtest(
    price_frame: pd.DataFrame,
    asset: str,
    model: str,
    horizons=(30, 90, 365),
    train_window: int = 365,
) -> list[dict]:
    return run_backtest(
        price_frame=price_frame,
        asset=asset,
        model=model,
        horizons=horizons,
        train_window=train_window,
    )
