"""Integration test: validate the local development config with the esphome CLI."""

import base64
import os
import pathlib
import shutil
import subprocess

import pytest

from conftest import REPO_ROOT

ESPHOME = shutil.which("esphome")
if not ESPHOME:
    candidate = pathlib.Path.home() / ".local" / "bin" / "esphome"
    if candidate.exists():
        ESPHOME = str(candidate)


def _write_local_config(tmp_path):
    for name in ("local.yaml", "platform_bk72xx.yaml", "nebula_light_device.yaml"):
        shutil.copy(REPO_ROOT / name, tmp_path / name)

    key = base64.b64encode(os.urandom(32)).decode()
    (tmp_path / "secrets.yaml").write_text(
        "wifi_ssid: test-ssid\n"
        "wifi_password: test-password\n"
        "wifi_fallback_password: test-fallback\n"
        f'api_key: "{key}"\n'
    )


@pytest.mark.skipif(not ESPHOME, reason="esphome CLI is not available")
def test_esphome_config_is_valid(tmp_path):
    _write_local_config(tmp_path)
    result = subprocess.run(
        [ESPHOME, "config", "local.yaml"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "Configuration is valid!" in output
    # No plaintext web-server OTA listener should be compiled in.
    assert "platform: web_server" not in output
