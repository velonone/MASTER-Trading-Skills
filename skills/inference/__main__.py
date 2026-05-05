"""``python -m skills.inference`` — show the resolved calibration."""

from __future__ import annotations

import json
import sys

from skills.inference.calibration import Calibration, _cli


def main(argv: list) -> int:
    if argv:
        return _cli(argv)
    print(json.dumps(Calibration.show(), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
