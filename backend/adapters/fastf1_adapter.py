"""Real F1 telemetry adapter loading FastF1 cached telemetry.

Provides real lap and sensor telemetry for Silverstone and Suzuka sessions.
Satisfies the `SourceAdapter` and `ReplayCapable` contracts.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, List, Optional

from backend.adapters.base import AdapterHealth, SourceAdapter
from backend.adapters.replay import ReplayCapable, ReplayDescriptor
from backend.telemetry.schema import DataSource, RaceTelemetry
from data.loaders.fastf1_loader import load_fastf1_session_telemetry


class FastF1Adapter(SourceAdapter, ReplayCapable):
    source_type = DataSource.REAL_CAR

    def __init__(
        self,
        circuit: str = "Silverstone",
        season: int = 2023,
        session_type: str = "R",
        driver: str = "VER",
        cache_dir: str = "data/cache",
        tick_delay_s: float = 0.05,
    ):
        self.circuit = circuit
        self.season = season
        self.session_type = session_type
        self.driver = driver
        self.cache_dir = cache_dir
        self.tick_delay_s = tick_delay_s

        self._frames: List[RaceTelemetry] = []
        self._connected = False
        self._health = AdapterHealth(connected=False, source=self.source_type)

    async def connect(self) -> None:
        if self._connected:
            return
        # Load telemetry in an async worker thread so it doesn't block the loop
        loop = asyncio.get_running_loop()
        self._frames = await loop.run_in_executor(
            None,
            load_fastf1_session_telemetry,
            self.season,
            self.circuit,
            self.session_type,
            self.driver,
            self.cache_dir,
        )
        self._connected = True
        self._health.connected = True
        self._health.frames_received = len(self._frames)

    async def disconnect(self) -> None:
        self._connected = False
        self._health.connected = False

    def health(self) -> AdapterHealth:
        return self._health

    def replay_descriptor(self) -> ReplayDescriptor:
        config = {
            "circuit": self.circuit,
            "season": self.season,
            "session_type": self.session_type,
            "driver": self.driver,
        }
        return ReplayDescriptor.create(
            scenario_id=f"{self.circuit.lower()}_{self.season}_{self.driver.lower()}",
            seed=42,
            config=config,
        )

    async def stream(self) -> AsyncIterator[RaceTelemetry]:
        if not self._connected:
            await self.connect()

        for frame in self._frames:
            if not self._connected:
                break
            self._health.last_frame_timestamp = frame.source_timestamp.isoformat()
            yield frame
            if self.tick_delay_s > 0:
                await asyncio.sleep(self.tick_delay_s)
