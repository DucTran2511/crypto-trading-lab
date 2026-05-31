from __future__ import annotations

import pytest


def test_multi_timeframe_confirmation_smoke_stub():
    module = pytest.importorskip(
        "user_data.strategies.MultiTimeframeConfirmation",
        reason="Task H owns the MultiTimeframeConfirmation implementation.",
    )
    strategy_cls = module.MultiTimeframeConfirmation
    strategy = strategy_cls({})

    assert strategy_cls.__name__ == "MultiTimeframeConfirmation"
    assert strategy.timeframe == "1d"
