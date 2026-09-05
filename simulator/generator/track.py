"""Synthetic and Real Circuit geometry definitions for RacePulse.

Includes official reference layouts for Silverstone (British GP) and Suzuka (Japanese GP).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Corner:
    number: int
    apex_distance_m: float
    apex_speed_kph: float
    arc_length_m: float
    direction: int  # +1 = right-hand, -1 = left-hand
    name: str = ""


@dataclass(frozen=True)
class SyntheticTrack:
    name: str
    length_m: float
    corners: tuple[Corner, ...]

    def corner_at(self, distance_m: float) -> Corner | None:
        """The corner whose arc contains this distance-along-lap, if any."""

        d = distance_m % self.length_m
        for corner in self.corners:
            half = corner.arc_length_m / 2.0
            lo, hi = corner.apex_distance_m - half, corner.apex_distance_m + half
            if lo <= d <= hi:
                return corner
        return None


def default_track() -> SyntheticTrack:
    """A fixed ~5.3km, 14-corner synthetic layout used by default simulator scenarios."""

    corners = (
        Corner(1, 350, 90, 120, +1, "Turn 1"),
        Corner(2, 900, 230, 90, -1, "Turn 2"),
        Corner(3, 1400, 70, 100, +1, "Turn 3 (hairpin)"),
        Corner(4, 1750, 180, 80, -1, "Turn 4"),
        Corner(5, 2200, 120, 90, +1, "Turn 5"),
        Corner(6, 2450, 200, 80, -1, "Turn 6"),
        Corner(7, 3000, 60, 110, +1, "Turn 7 (hairpin)"),
        Corner(8, 3300, 160, 80, -1, "Turn 8"),
        Corner(9, 3650, 240, 90, +1, "Turn 9"),
        Corner(10, 4000, 90, 100, -1, "Turn 10"),
        Corner(11, 4300, 150, 80, +1, "Turn 11"),
        Corner(12, 4600, 210, 90, -1, "Turn 12"),
        Corner(13, 4900, 100, 90, +1, "Turn 13"),
        Corner(14, 5150, 190, 80, -1, "Turn 14"),
    )
    return SyntheticTrack(name="Synthetic Circuit", length_m=5303.0, corners=corners)


def silverstone_track() -> SyntheticTrack:
    """Silverstone Circuit — British Grand Prix (5.891 km, 18 Corners)."""

    corners = (
        Corner(1, 350, 250, 120, +1, "Abbey"),
        Corner(2, 650, 290, 80, -1, "Farm"),
        Corner(3, 980, 110, 90, +1, "Village"),
        Corner(4, 1180, 85, 100, -1, "The Loop"),
        Corner(5, 1420, 210, 80, -1, "Aintree"),
        Corner(6, 2150, 145, 110, -1, "Brooklands"),
        Corner(7, 2450, 105, 120, +1, "Luffield"),
        Corner(8, 2750, 260, 80, +1, "Woodcote"),
        Corner(9, 3200, 265, 90, +1, "Copse"),
        Corner(10, 3600, 285, 80, -1, "Maggotts"),
        Corner(11, 3800, 235, 90, +1, "Becketts 1"),
        Corner(12, 3950, 195, 90, -1, "Becketts 2"),
        Corner(13, 4150, 240, 80, +1, "Chapel"),
        Corner(14, 4750, 185, 100, +1, "Stowe"),
        Corner(15, 5200, 95, 90, -1, "Vale"),
        Corner(16, 5400, 105, 90, +1, "Club 1"),
        Corner(17, 5550, 160, 80, +1, "Club 2"),
        Corner(18, 5750, 230, 80, +1, "Club Exit"),
    )
    return SyntheticTrack(name="Silverstone Circuit", length_m=5891.0, corners=corners)


def suzuka_track() -> SyntheticTrack:
    """Suzuka Circuit — Japanese Grand Prix (5.807 km, 18 Corners)."""

    corners = (
        Corner(1, 450, 240, 110, +1, "First Corner"),
        Corner(2, 620, 155, 90, +1, "Turn 2"),
        Corner(3, 900, 215, 80, -1, "S Curve 1"),
        Corner(4, 1150, 205, 80, +1, "S Curve 2"),
        Corner(5, 1380, 190, 80, -1, "S Curve 3"),
        Corner(6, 1600, 175, 80, +1, "S Curve 4"),
        Corner(7, 1950, 220, 110, -1, "Dunlop Curve"),
        Corner(8, 2350, 195, 80, +1, "Degner 1"),
        Corner(9, 2550, 135, 80, +1, "Degner 2"),
        Corner(10, 3100, 75, 90, -1, "Hairpin"),
        Corner(11, 3500, 270, 100, +1, "200R"),
        Corner(12, 3950, 175, 90, -1, "Spoon Curve 1"),
        Corner(13, 4200, 150, 90, -1, "Spoon Curve 2"),
        Corner(14, 4950, 290, 100, -1, "130R"),
        Corner(15, 5350, 85, 90, +1, "Casio Triangle 1"),
        Corner(16, 5480, 110, 80, -1, "Casio Triangle 2"),
        Corner(17, 5680, 220, 90, +1, "Final Corner"),
    )
    return SyntheticTrack(name="Suzuka Circuit", length_m=5807.0, corners=corners)
