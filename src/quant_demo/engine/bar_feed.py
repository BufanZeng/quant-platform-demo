"""Replay BarClosed events from a parquet or CSV file."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd

from quant_demo.events import BarClosed


class BarFeed:
    def __init__(self, bars: pd.DataFrame):
        self._bars = bars.sort_values("timestamp").reset_index(drop=True)

    @classmethod
    def from_parquet(cls, path: Path) -> BarFeed:
        return cls(pd.read_parquet(path))

    @classmethod
    def from_csv(cls, path: Path) -> BarFeed:
        df = pd.read_csv(path, parse_dates=["timestamp"])
        return cls(df)

    def __iter__(self) -> Iterator[BarClosed]:
        for row in self._bars.itertuples(index=False):
            yield BarClosed(
                symbol=row.symbol,
                timeframe=row.timeframe,
                timestamp=row.timestamp.to_pydatetime()
                if hasattr(row.timestamp, "to_pydatetime")
                else row.timestamp,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=int(row.volume),
                source=str(getattr(row, "source", "synthetic")),
            )

    def __len__(self) -> int:
        return len(self._bars)
