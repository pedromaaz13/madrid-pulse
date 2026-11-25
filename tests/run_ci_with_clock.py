"""Ejecuta los módulos de CI indicados con un reloj de pared simulado."""

from argparse import ArgumentParser
from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from tests.clock import api_wall_clock, frozen_datetime


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("wall_clock", type=datetime.fromisoformat)
    parser.add_argument("modules", nargs="+")
    args = parser.parse_args()
    clock = frozen_datetime(args.wall_clock)
    print(f"Reloj Python simulado: {clock.now(timezone.utc).isoformat()}", flush=True)

    from apps.api.tests import test_snapshot_contract
    from services.collector import collector

    with (
        api_wall_clock(args.wall_clock),
        patch.object(collector, "datetime", clock),
        patch.object(test_snapshot_contract, "datetime", clock),
    ):
        suite = unittest.defaultTestLoader.loadTestsFromNames(args.modules)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        f"casos={result.testsRun} fallos={len(result.failures)} "
        f"errores={len(result.errors)} skips={len(result.skipped)}"
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
