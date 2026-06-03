"""Sprint 25 top-20 universe alias for the daily Donchian breakout strategy."""
from __future__ import annotations

try:
    from user_data.strategies.DonchianBreakoutDaily import DonchianBreakoutDaily
except ModuleNotFoundError:
    from DonchianBreakoutDaily import DonchianBreakoutDaily


class DonchianBreakoutDailyTop20(DonchianBreakoutDaily):
    """Daily Donchian breakout with logic inherited unchanged for top-20 tests."""
