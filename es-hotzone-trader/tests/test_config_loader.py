from __future__ import annotations

import tempfile
import textwrap
import unittest
import warnings
from pathlib import Path

from src.config.loader import load_config


class TestConfigLoaderCompatibility(unittest.TestCase):
    def test_load_config_ignores_deprecated_noop_keys_with_warning(self) -> None:
        config_text = textwrap.dedent(
            """
            strategy:
              vwap_session: "RTH"
            risk:
              use_volatility_sizing: true
              target_daily_risk_pct: 1.0
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(config_text, encoding="utf-8")
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                config = load_config(str(config_path))

        self.assertFalse(hasattr(config.strategy, "vwap_session"))
        self.assertFalse(hasattr(config.risk, "use_volatility_sizing"))
        self.assertFalse(hasattr(config.risk, "target_daily_risk_pct"))
        messages = [str(item.message) for item in caught]
        self.assertTrue(any("vwap_session" in message for message in messages))
        self.assertTrue(any("use_volatility_sizing" in message for message in messages))
        self.assertTrue(any("target_daily_risk_pct" in message for message in messages))
