import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


class SettingsSecurityTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_dir = Path(__file__).resolve().parents[3]

    def import_settings(self, overrides):
        env = os.environ.copy()
        for key in (
            'ALLOWED_HOSTS',
            'CORS_ALLOW_ALL_ORIGINS',
            'DEBUG',
            'SECRET_KEY',
        ):
            env.pop(key, None)
        env.update({
            'SKIP_DOTENV': 'True',
            **overrides,
        })
        return subprocess.run(
            [sys.executable, '-c', 'import config.settings; print("settings imported")'],
            cwd=self.backend_dir,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_production_requires_secret_key(self):
        result = self.import_settings({
            'DEBUG': 'False',
            'ALLOWED_HOSTS': 'erp.example.com',
        })

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SECRET_KEY', result.stdout + result.stderr)

    def test_production_requires_allowed_hosts(self):
        result = self.import_settings({
            'DEBUG': 'False',
            'SECRET_KEY': 'test-production-secret-key',
        })

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ALLOWED_HOSTS', result.stdout + result.stderr)

    def test_debug_mode_can_use_local_defaults(self):
        result = self.import_settings({'DEBUG': 'True'})

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('settings imported', result.stdout)

    def test_production_rejects_wildcard_cors(self):
        result = self.import_settings({
            'DEBUG': 'False',
            'SECRET_KEY': 'test-production-secret-key',
            'ALLOWED_HOSTS': 'erp.example.com',
            'CORS_ALLOW_ALL_ORIGINS': 'True',
        })

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('CORS_ALLOW_ALL_ORIGINS', result.stdout + result.stderr)
