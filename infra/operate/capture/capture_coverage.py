"""Mide cobertura confirmada sin conectar rondas separadas por una interrupción."""

from datetime import timedelta

from capture_manifest import FEEDS

WALL_STEP_TOLERANCE_S = 2
DEFAULT_GAP_S = 120
DEFAULT_MAX_CIVIL_MINUTES = 360


def interval(start, end):
    return {
        "from_utc": start.isoformat(),
        "to_utc": end.isoformat(),
        "seconds": (end - start).total_seconds(),
    }


class Coverage:
    def __init__(self, started, monotonic, gap_seconds, profile):
        self.started = self.wall = started
        self.monotonic = monotonic
        self.gap_seconds = gap_seconds
        self.profile = profile
        self.suspension_gaps = []
        self.cycle_gaps = []
        self.segments = []
        self.covered = timedelta()
        self.last_success = started
        self.breaks = []
        self.pending = []
        self.adjacent = False
        self.profile_mismatches = 0

    @property
    def effective(self):
        return self.covered.total_seconds()

    def sample(self, wall, monotonic):
        elapsed = (wall - self.wall).total_seconds()
        offset = elapsed - (monotonic - self.monotonic)
        discontinuity = abs(offset) > WALL_STEP_TOLERANCE_S or elapsed < 0
        if discontinuity or elapsed > self.gap_seconds:
            start, end = sorted((self.wall, wall))
            self.suspension_gaps.append({
                **interval(start, end),
                "kind": "clock_discontinuity" if discontinuity else "supervisor_stall",
                "wall_minus_monotonic_s": offset,
            })
            self.breaks.append((start, end))
        self.wall, self.monotonic = wall, monotonic
        return elapsed < 0 or offset < -WALL_STEP_TOLERANCE_S

    def record(self, run):
        feed = run["feed_name"]
        if run["anchor_profile"] != self.profile:
            self.profile_mismatches += 1
        if feed == FEEDS[0]:
            if self.pending:
                self.adjacent = False
            self.pending = []
        if feed != FEEDS[len(self.pending)]:
            self.pending = []
            self.adjacent = False
            return
        self.pending.append(run)
        if len(self.pending) < len(FEEDS):
            return
        first = self.pending[0]["started_at"]
        last = self.pending[-1]["finished_at"]
        healthy = (
            last is not None and self.started <= first <= last <= self.wall
            and all(item["status"] == "ok" and item["anchor_profile"] == self.profile
                    for item in self.pending)
            and not self.crosses_break(first, last)
        )
        self.pending = []
        if healthy:
            self.record_success(first)
        self.adjacent = healthy

    def crosses_break(self, start, end):
        return any(left < end and right > start for left, right in self.breaks)

    def record_success(self, first):
        gap = interval(self.last_success, first)
        if gap["seconds"] > self.gap_seconds:
            self.cycle_gaps.append(gap)
        elif (self.adjacent and gap["seconds"] > 0
              and not self.crosses_break(self.last_success, first)):
            self.covered += first - self.last_success
            if self.segments and self.segments[-1][1] == self.last_success:
                self.segments[-1] = (self.segments[-1][0], first)
            else:
                self.segments.append((self.last_success, first))
        self.last_success = first

    def fields(self):
        trailing = interval(self.last_success, self.wall)
        gaps = self.cycle_gaps.copy()
        if trailing["seconds"] > self.gap_seconds:
            gaps.append(trailing)
        return {
            "civil_duration_s": max(0.0, (self.wall - self.started).total_seconds()),
            "effective_coverage_s": self.effective,
            "suspension_gaps": self.suspension_gaps,
            "cycle_gaps": gaps,
            "coverage_segments": [interval(left, right) for left, right in self.segments],
            "profile_mismatches": self.profile_mismatches,
        }
