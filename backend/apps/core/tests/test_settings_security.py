import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

STRONG_SECRET_KEY = 'k7#Qp2!vZ9@mL4$wX8^nR1&bT6*cY3(hJ5)dF0_gS-aE+uI=oP'
PRODUCTION_ENV = {
    'DEBUG': 'False',
    'SECRET_KEY': STRONG_SECRET_KEY,
    'ALLOWED_HOSTS': 'erp.example.com',
    'DB_NAME': 'erp_db',
    'DB_USER': 'erp_user',
    'DB_PASSWORD': 'db-password',
    'DB_HOST': 'db.internal',
}


class SettingsSecurityTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_dir = Path(__file__).resolve().parents[3]

    def import_settings(self, overrides, print_expr='"settings imported"'):
        env = os.environ.copy()
        for key in (
            'ALLOWED_HOSTS',
            'API_DOCS_ENABLED',
            'APP_ENV',
            'CORS_ALLOW_ALL_ORIGINS',
            'CORS_ALLOW_CREDENTIALS',
            'CSRF_COOKIE_SECURE',
            'DB_HOST',
            'DB_NAME',
            'DB_PASSWORD',
            'DB_USER',
            'DEBUG',
            'SECRET_KEY',
            'SESSION_COOKIE_SECURE',
            'X_FRAME_OPTIONS',
        ):
            env.pop(key, None)
        env.update({
            'SKIP_DOTENV': 'True',
            **overrides,
        })
        return subprocess.run(
            [sys.executable, '-c', f'import config.settings as s; print({print_expr})'],
            cwd=self.backend_dir,
            env=env,
            capture_output=True,
            text=True,
        )

    def production(self, **overrides):
        env = {**PRODUCTION_ENV, **overrides}
        return {key: value for key, value in env.items() if value is not None}

    def assert_rejected(self, result, setting_name):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(setting_name, result.stdout + result.stderr)

    def test_production_requires_secret_key(self):
        self.assert_rejected(self.import_settings(self.production(SECRET_KEY=None)), 'SECRET_KEY')

    def test_production_rejects_weak_secret_key(self):
        for weak_key in ('test-production-secret-key', 'a' * 60, 'django-insecure-' + 'x1y2z3' * 10):
            with self.subTest(weak_key=weak_key):
                self.assert_rejected(self.import_settings(self.production(SECRET_KEY=weak_key)), 'SECRET_KEY')

    def test_production_requires_allowed_hosts(self):
        self.assert_rejected(self.import_settings(self.production(ALLOWED_HOSTS=None)), 'ALLOWED_HOSTS')

    def test_production_rejects_wildcard_allowed_hosts(self):
        self.assert_rejected(self.import_settings(self.production(ALLOWED_HOSTS='*')), 'ALLOWED_HOSTS')

    def test_production_rejects_wildcard_cors(self):
        result = self.import_settings(self.production(CORS_ALLOW_ALL_ORIGINS='True'))
        self.assert_rejected(result, 'CORS_ALLOW_ALL_ORIGINS')

    def test_production_requires_database_credentials(self):
        for name in ('DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST'):
            with self.subTest(missing=name):
                self.assert_rejected(self.import_settings(self.production(**{name: None})), name)

    def test_debug_is_rejected_when_app_env_is_production(self):
        result = self.import_settings({'DEBUG': 'True', 'APP_ENV': 'Production'})
        self.assert_rejected(result, 'DEBUG')

    def test_invalid_x_frame_options_is_rejected(self):
        result = self.import_settings(self.production(X_FRAME_OPTIONS='ALLOW-FROM https://evil.example'))
        self.assert_rejected(result, 'X_FRAME_OPTIONS')

    def test_debug_mode_can_use_local_defaults(self):
        result = self.import_settings({'DEBUG': 'True'})

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('settings imported', result.stdout)

    def test_production_imports_with_required_environment(self):
        result = self.import_settings(self.production())

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('settings imported', result.stdout)

    def test_production_forces_secure_cookies_and_hides_browsable_api(self):
        result = self.import_settings(
            self.production(SESSION_COOKIE_SECURE='False', CSRF_COOKIE_SECURE='False'),
            print_expr=(
                's.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, s.CORS_ALLOW_CREDENTIALS, '
                's.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"], '
                's.SPECTACULAR_SETTINGS["SERVE_PERMISSIONS"]'
            ),
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "True True False ('rest_framework.renderers.JSONRenderer',) "
            "['rest_framework.permissions.IsAdminUser']",
        )
