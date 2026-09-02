import os
import subprocess
import sys
import unittest
from preflight.config import Settings, get_settings


class TestConfig(unittest.TestCase):
    def test_default_settings(self):
        s = Settings()
        self.assertEqual(s.env, "development")
        self.assertTrue(s.auth_required)
        self.assertEqual(s.port, 8001)
        self.assertIn("http://localhost:3000", s.cors_origins_list)

    def test_production_validation_catches_default_session_secret(self):
        s = Settings(PREFLIGHT_ENV="production", PREFLIGHT_SESSION_SECRET="dev-secret-key-change-in-production")
        errors = s.validate_production_requirements()
        self.assertTrue(any("PREFLIGHT_SESSION_SECRET" in e for e in errors))

    def test_production_validation_passes_with_strong_secret(self):
        s = Settings(PREFLIGHT_ENV="production", PREFLIGHT_SESSION_SECRET="super-secure-production-random-secret-key-32chars")
        errors = s.validate_production_requirements()
        self.assertEqual(len(errors), 0)

    def test_safe_summary_masks_secrets(self):
        s = Settings(
            GEMINI_API_KEY="secret-gemini-key",
            TELEGRAM_BOT_TOKEN="secret-tele-token",
            ZALO_ACCESS_TOKEN="secret-zalo-token",
        )
        summary = s.get_safe_summary()
        self.assertEqual(summary["gemini_ocr"], "configured")
        self.assertEqual(summary["telegram"], "live")
        self.assertEqual(summary["zalo"], "live")
        self.assertNotIn("secret-gemini-key", str(summary))
        self.assertNotIn("secret-tele-token", str(summary))

    def test_gen_env_example_check_script(self):
        result = subprocess.run(
            [sys.executable, "scripts/gen_env_example.py", "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, f"gen_env_example.py --check failed: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
