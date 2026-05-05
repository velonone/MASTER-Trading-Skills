"""
Calibration — Inference Confidence Source Resolver
====================================================
Resolves which calibration values feed the inference engine.

Resolution order (first non-empty wins):

  1. Explicit kwarg passed to Calibration(...)
  2. Environment variable MASTER_TRADING_CALIBRATION
  3. Per-user config file ~/.master-trading/config.json
  4. Bundled VelonLabs Reference Snapshot (free, real values)

The bundled snapshot is the actual VelonLabs calibration as of its
release date — it is NOT a placeholder. Users who install the package
get usable values immediately. Subscription tiers exist for fresher
calibrations (markets evolve and snapshot ages).

Sources
-------
snapshot     — bundled VelonLabs Reference Calibration (default, free)
live         — VelonLabs subscription API (paid, monthly updates)
self         — locally calibrated from your own trading history
custom       — user-provided JSON file path
placeholder  — all confidences forced to 0.5 (DO NOT use for live trading)

Programmatic usage
------------------
    from skills.inference.calibration import Calibration

    cal = Calibration.resolve()                  # default: snapshot
    cal = Calibration.from_file("my.json")
    cal = Calibration.placeholder()
    Calibration.persist_choice("snapshot")

CLI usage
---------
    python -m skills.inference.calibration show
    python -m skills.inference.calibration set snapshot
    python -m skills.inference.calibration set custom --path=./my.json
    python -m skills.inference.calibration set live --api-key=xxx
    python -m skills.inference.calibration reset
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from skills.core.logging import get_logger
from skills.inference._calibration_data import VELONLABS_SNAPSHOT_2026_05


_logger = get_logger("inference.calibration")


CONFIG_DIR = Path.home() / ".master-trading"
CONFIG_PATH = CONFIG_DIR / "config.json"
ENV_VAR = "MASTER_TRADING_CALIBRATION"
ENV_VAR_API_KEY = "MASTER_TRADING_VELONLABS_KEY"
ENV_VAR_CUSTOM_PATH = "MASTER_TRADING_CALIBRATION_PATH"

FRESHNESS_WARN_DAYS = 90


class CalibrationSource(str, Enum):
    SNAPSHOT = "snapshot"
    LIVE = "live"
    SELF = "self"
    CUSTOM = "custom"
    PLACEHOLDER = "placeholder"


SETUP_PROMPT = """\
The trading inference engine uses calibration values to produce confidence
scores. Pick a source so your agent knows which numbers it's standing on.

  ✓ snapshot    (recommended · free · default)
                VelonLabs Reference Calibration v{version} — the actual
                calibration values used by VelonLabs trading operations,
                derived from market data {start} to {end}. Real numbers,
                not placeholders. Frozen at release date.
                When to use: starting out, learning the framework, or any
                strategy where stable calibration matters more than fresh.

  ⊕ live        (paid subscription)
                Monthly-updated calibration from VelonLabs. The same engine,
                with confidences re-fit against the latest market regime
                each month. Requires {api_env} to be set.
                When to use: production strategies that need calibration
                to track market evolution.

  ⊙ self        (free, requires your own data)
                Run tools/calibrate.py against your own trade history
                (6+ months recommended) to produce a custom calibration.
                When to use: you have proprietary data and want full control.

  ⊘ custom      (free, advanced)
                Point at any JSON file matching the snapshot schema.
                When to use: you have a third-party calibration source
                or want to A/B different sets.

  ⚠ placeholder (testing only)
                All confidences forced to 0.5. DO NOT USE FOR LIVE TRADING.
                When to use: architecture verification, unit tests.

If you skip this, the snapshot is used by default and a one-time hint is
emitted. You can change at any time:

    python -m skills.inference.calibration set <source>
""".format(
    version=VELONLABS_SNAPSHOT_2026_05["version"],
    start=VELONLABS_SNAPSHOT_2026_05["calibrated_against"]["start"],
    end=VELONLABS_SNAPSHOT_2026_05["calibrated_against"]["end"],
    api_env=ENV_VAR_API_KEY,
)


class CalibrationNotConfigured(RuntimeError):
    """
    Raised in strict mode when no calibration source has been configured.

    Agents catching this exception MUST surface :data:`SETUP_PROMPT` to
    the user verbatim and let them choose, then call
    :meth:`Calibration.persist_choice` with the answer.
    """
    prompt: str = SETUP_PROMPT


@dataclass
class Calibration:
    """
    A resolved calibration ready to be plugged into the inference engine.

    The :attr:`data` dict matches the shape of
    :data:`VELONLABS_SNAPSHOT_2026_05` — primitives, causal_chains,
    singularity_weights, signal_thresholds, convergence_ratios.

    :attr:`meta` carries provenance suitable for embedding into
    inference outputs (so downstream consumers and audit logs know
    which calibration produced a given decision).
    """
    data: Dict[str, Any]
    meta: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Public accessors used by the inference engine
    # ------------------------------------------------------------------
    @property
    def version(self) -> str:
        return self.data.get("version", "unknown")

    @property
    def source(self) -> str:
        return self.meta.get("source", self.data.get("source", "unknown"))

    @property
    def released_at(self) -> Optional[str]:
        return self.data.get("released_at")

    def age_days(self) -> Optional[int]:
        ra = self.released_at
        if not ra:
            return None
        try:
            released = datetime.fromisoformat(ra)
        except ValueError:
            return None
        return (datetime.utcnow() - released).days

    def freshness_warning(self) -> Optional[str]:
        age = self.age_days()
        if age is None:
            return None
        if age > FRESHNESS_WARN_DAYS and self.source in {"snapshot", "custom"}:
            return (
                f"Calibration is {age} days old (released {self.released_at}). "
                f"Markets evolve — consider upgrading to a fresher source: "
                f"see `python -m skills.inference.calibration set live`."
            )
        return None

    def emit_meta(self) -> Dict[str, Any]:
        """Provenance dict to attach to engine outputs as ``_meta``."""
        return {
            "calibration_source": self.source,
            "calibration_version": self.version,
            "calibration_released_at": self.released_at,
            "calibration_age_days": self.age_days(),
            "freshness_warning": self.freshness_warning(),
            "attribution": self.data.get("attribution"),
        }

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------
    @classmethod
    def velonlabs_snapshot(cls) -> "Calibration":
        """Bundled VelonLabs Reference Calibration — real values, free."""
        data = copy.deepcopy(VELONLABS_SNAPSHOT_2026_05)
        return cls(data=data, meta={"source": CalibrationSource.SNAPSHOT.value})

    @classmethod
    def placeholder(cls) -> "Calibration":
        """All confidences clamped to 0.5. Architecture verification only."""
        data = copy.deepcopy(VELONLABS_SNAPSHOT_2026_05)
        data["version"] = "placeholder"
        data["source"] = CalibrationSource.PLACEHOLDER.value
        for prim in data["primitives"].values():
            prim["base_confidence"] = 0.5
        for chain in data["causal_chains"].values():
            for step in chain:
                step["confidence"] = 0.5
        return cls(data=data, meta={"source": CalibrationSource.PLACEHOLDER.value})

    @classmethod
    def from_file(cls, path: os.PathLike) -> "Calibration":
        """Load a calibration JSON matching the snapshot schema."""
        p = Path(path)
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        cls._validate_shape(data)
        meta = {
            "source": data.get("source", CalibrationSource.CUSTOM.value),
            "loaded_from": str(p),
        }
        return cls(data=data, meta=meta)

    @classmethod
    def from_velonlabs_api(cls, api_key: Optional[str] = None) -> "Calibration":
        """
        Fetch the current month's VelonLabs calibration.

        Currently raises NotImplementedError — the live endpoint is not
        bundled with the open-source package. Subscribers receive an
        endpoint URL + API key. The integration shape is intentionally
        kept stable so swapping in a real client is a single-line change.
        """
        api_key = api_key or os.environ.get(ENV_VAR_API_KEY)
        if not api_key:
            raise ValueError(
                f"Live calibration requires an API key. "
                f"Set {ENV_VAR_API_KEY} or pass api_key=..."
            )
        raise NotImplementedError(
            "VelonLabs live calibration endpoint is provided to subscribers. "
            "Visit https://velonlabs.example/calibration for access. "
            "Until then, the snapshot remains the recommended default."
        )

    # ------------------------------------------------------------------
    # Resolution chain
    # ------------------------------------------------------------------
    @classmethod
    def resolve(
        cls,
        explicit: Optional["Calibration"] = None,
        *,
        strict: bool = False,
    ) -> "Calibration":
        """
        Resolve calibration in order:
            explicit kwarg → env var → config file → snapshot fallback

        In strict mode, the snapshot fallback is replaced by raising
        :class:`CalibrationNotConfigured`. Agents and CLIs catch that
        and prompt the user; non-interactive callers (CI, single-shot
        scripts) typically prefer the default non-strict behaviour.
        """
        if explicit is not None:
            return explicit

        env = os.environ.get(ENV_VAR, "").strip().lower()
        if env:
            return cls._from_source_name(env)

        if CONFIG_PATH.exists():
            try:
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                source = cfg.get("calibration_source")
                if source:
                    return cls._from_source_name(source, cfg)
            except Exception as exc:  # noqa: BLE001
                _logger.warning("calibration.config_read_failed path=%s err=%s",
                                CONFIG_PATH, exc)

        if strict:
            raise CalibrationNotConfigured(SETUP_PROMPT)

        cal = cls.velonlabs_snapshot()
        cal.meta["fallback"] = True
        cal.meta["hint"] = (
            "No calibration configured — using bundled snapshot. "
            "Run `python -m skills.inference.calibration set <source>` "
            "to make this explicit."
        )
        return cal

    @classmethod
    def _from_source_name(
        cls,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> "Calibration":
        config = config or {}
        name = name.strip().lower()
        if name in {CalibrationSource.SNAPSHOT.value, "default", ""}:
            return cls.velonlabs_snapshot()
        if name == CalibrationSource.PLACEHOLDER.value:
            return cls.placeholder()
        if name == CalibrationSource.CUSTOM.value:
            path = config.get("calibration_path") or os.environ.get(ENV_VAR_CUSTOM_PATH)
            if not path:
                raise ValueError(
                    "custom source requires a path. "
                    f"Set {ENV_VAR_CUSTOM_PATH} or store 'calibration_path' "
                    f"in {CONFIG_PATH}."
                )
            return cls.from_file(path)
        if name == CalibrationSource.LIVE.value:
            api_key = config.get("velonlabs_api_key") or os.environ.get(ENV_VAR_API_KEY)
            return cls.from_velonlabs_api(api_key)
        if name == CalibrationSource.SELF.value:
            path = config.get("calibration_path")
            if not path:
                raise ValueError(
                    "self source expects 'calibration_path' in config "
                    "pointing at the file produced by tools/calibrate.py."
                )
            cal = cls.from_file(path)
            cal.meta["source"] = CalibrationSource.SELF.value
            return cal
        raise ValueError(f"Unknown calibration source: {name!r}")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    @classmethod
    def persist_choice(
        cls,
        source: str,
        *,
        path: Optional[os.PathLike] = None,
        api_key: Optional[str] = None,
    ) -> Path:
        """
        Persist the user's calibration choice to ``~/.master-trading/config.json``
        so future invocations resolve it without prompting.

        Returns the path to the written config file.
        """
        cfg: Dict[str, Any] = {
            "calibration_source": source,
            "configured_at": datetime.utcnow().isoformat(),
        }
        if path:
            cfg["calibration_path"] = str(Path(path).resolve())
        if api_key:
            cfg["velonlabs_api_key"] = api_key

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        try:
            os.chmod(CONFIG_PATH, 0o600)  # best-effort: avoid leaking api_key
        except OSError:
            pass
        _logger.info("calibration.persisted source=%s path=%s", source, CONFIG_PATH)
        return CONFIG_PATH

    @classmethod
    def reset(cls) -> bool:
        """Remove the persisted config. Returns True if a file was deleted."""
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()
            return True
        return False

    @classmethod
    def show(cls) -> Dict[str, Any]:
        """Diagnostic snapshot of how :meth:`resolve` would behave right now."""
        info: Dict[str, Any] = {
            "env_var": os.environ.get(ENV_VAR),
            "config_path": str(CONFIG_PATH),
            "config_exists": CONFIG_PATH.exists(),
            "velonlabs_api_key_set": bool(os.environ.get(ENV_VAR_API_KEY)),
        }
        if CONFIG_PATH.exists():
            try:
                info["config"] = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                info["config_error"] = str(exc)
        cal = cls.resolve()
        info["resolved"] = cal.emit_meta()
        return info

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_shape(data: Dict[str, Any]) -> None:
        required = {"primitives", "causal_chains", "singularity_weights", "signal_thresholds"}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(
                f"Calibration JSON is missing required keys: {sorted(missing)}"
            )


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def _cli(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m skills.inference.calibration",
        description="Manage trading inference calibration source.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show", help="Show current resolution and config.")
    sub.add_parser("reset", help="Delete persisted config.")
    sub.add_parser("prompt", help="Print the agent setup prompt.")

    p_set = sub.add_parser("set", help="Persist a calibration source choice.")
    p_set.add_argument("source", choices=[s.value for s in CalibrationSource])
    p_set.add_argument("--path", help="For 'custom' or 'self' sources.")
    p_set.add_argument("--api-key", help="For 'live' source.")

    args = parser.parse_args(argv)

    if args.cmd == "show":
        info = Calibration.show()
        print(json.dumps(info, indent=2, default=str))
        return 0

    if args.cmd == "reset":
        deleted = Calibration.reset()
        print("config removed" if deleted else "no config to remove")
        return 0

    if args.cmd == "prompt":
        print(SETUP_PROMPT)
        return 0

    if args.cmd == "set":
        path = Calibration.persist_choice(
            args.source, path=args.path, api_key=args.api_key,
        )
        print(f"saved {args.source} → {path}")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
