import hashlib
import importlib.util
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

spec = importlib.util.spec_from_file_location(
    "hosted_backup", Path(__file__).parents[2] / "scripts" / "hosted_backup.py"
)
backup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup_module)


class HostedBackupTests(SimpleTestCase):
    def test_inherited_libpq_settings_cannot_redirect_backup(self):
        with patch.dict(
            backup_module.os.environ,
            {
                "PGSERVICE": "other-account",
                "PGHOSTADDR": "192.0.2.1",
                "PGOPTIONS": "-c search_path=other",
                "PGSSLROOTCERT": "other.pem",
            },
        ):
            environment, _ = backup_module.connection_environment(self.values())
            for key in ("PGSERVICE", "PGHOSTADDR", "PGOPTIONS", "PGSSLROOTCERT"):
                self.assertNotIn(key, environment)
            self.assertEqual(environment["PGHOST"], "pooler.example.com")
            environment, _ = backup_module.connection_environment(
                {**self.values(), "POSTGRES_SSLROOTCERT": "chosen.pem"}
            )
            self.assertEqual(environment["PGSSLROOTCERT"], "chosen.pem")

    def values(self):
        return {
            "POSTGRES_HOST": "pooler.example.com",
            "POSTGRES_DB": "postgres",
            "POSTGRES_USER": "example",
            "POSTGRES_PASSWORD": "private-secret",
            "POSTGRES_SCHEMA": "horizonte",
        }

    def test_archive_list_hash_and_secret_only_in_environment(self):
        payload = b"synthetic archive" * 20

        def run(arguments, **kwargs):
            self.assertNotIn("private-secret", " ".join(arguments))
            self.assertEqual(kwargs["env"]["PGPASSWORD"], "private-secret")
            for argument in arguments:
                if argument.startswith("--file="):
                    Path(argument.partition("=")[2]).write_bytes(payload)
            return subprocess.CompletedProcess(arguments, 0, b"", b"")

        with (
            TemporaryDirectory() as directory,
            patch.object(backup_module.shutil, "which", side_effect=lambda value: value),
            patch.object(backup_module.subprocess, "run", side_effect=run),
        ):
            result = backup_module.backup(self.values(), Path(directory))
            self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertTrue(result["archive_list_verified"])
            self.assertFalse(result["restore_verified"])
            self.assertFalse(result["encrypted"])
            self.assertEqual(len(list(Path(directory).glob("*.dump"))), 1)
            self.assertFalse(list(Path(directory).glob("*.partial")))

    def test_failure_does_not_echo_provider_error_or_promote_archive(self):
        with (
            TemporaryDirectory() as directory,
            patch.object(backup_module.shutil, "which", side_effect=lambda value: value),
            patch.object(
                backup_module.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 1, b"", b"private-secret"),
            ),
        ):
            with self.assertRaises(RuntimeError) as error:
                backup_module.backup(self.values(), Path(directory))
            self.assertNotIn("private-secret", str(error.exception))
            self.assertFalse(list(Path(directory).glob("*.dump")))

    def test_unencrypted_connection_and_schema_patterns_are_rejected(self):
        for changes in (
            {"POSTGRES_SSLMODE": "disable"},
            {"POSTGRES_SCHEMA": "*"},
            {"POSTGRES_PASSWORD": ""},
            {"POSTGRES_PORT": "0"},
            {"POSTGRES_PORT": "65536"},
            {"POSTGRES_DB": "host=other dbname=postgres"},
            {"POSTGRES_DB": "postgresql://other/postgres"},
        ):
            with self.assertRaises(ValueError):
                backup_module.connection_environment({**self.values(), **changes})
