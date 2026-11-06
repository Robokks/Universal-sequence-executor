"""Regression tests for the MCP subprocess environment allowlist bug.

The python-mcp stdio transport does not inherit arbitrary parent environment
variables; explicitly selected paths must be carried in server.env.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lvbatch.mcp_client import mcp_stdio_env


class MCPStdioEnvTests(unittest.TestCase):
    def test_missing_override_uses_sdk_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(mcp_stdio_env())

    def test_provisioned_bundle_is_forwarded(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "python.exe").touch()
            with patch.dict(os.environ, {"LABVIEWMCP_PYLABVIEW": folder}):
                self.assertEqual(
                    mcp_stdio_env(),
                    {"LABVIEWMCP_PYLABVIEW": folder},
                )

    def test_invalid_bundle_fails_before_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"LABVIEWMCP_PYLABVIEW": folder}):
                with self.assertRaisesRegex(FileNotFoundError, "python.exe"):
                    mcp_stdio_env()


if __name__ == "__main__":
    unittest.main()
