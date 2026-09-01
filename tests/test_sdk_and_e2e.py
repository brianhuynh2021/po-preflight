from __future__ import annotations

import unittest
from pathlib import Path

from scripts.demo_e2e import run_demo


class TestSDKAndDemo(unittest.TestCase):
    def test_frontend_sdk_files_exist(self):
        """Test TypeScript API client SDK files exist in apps/web/app/lib/api/."""
        api_dir = Path("apps/web/app/lib/api")
        self.assertTrue((api_dir / "types.ts").exists())
        self.assertTrue((api_dir / "client.ts").exists())
        self.assertTrue((api_dir / "index.ts").exists())

    def test_run_e2e_demo_script(self):
        """Test E2E demo script executes all 6 stages without errors."""
        # run_demo should complete without raising any exceptions
        try:
            run_demo()
        except Exception as exc:
            self.fail(f"demo_e2e.py raised an exception: {exc}")


if __name__ == "__main__":
    unittest.main()
