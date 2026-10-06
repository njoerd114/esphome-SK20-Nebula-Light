"""Integration test: validate the composed local config with the esphome CLI."""

import base64
import os
import pathlib
import re
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
    """Compose a config from recommended_base.yaml with local package files."""
    for name in ("platform_bk72xx.yaml", "nebula_light_device.yaml"):
        shutil.copy(REPO_ROOT / name, tmp_path / name)

    content = (REPO_ROOT / "recommended_base.yaml").read_text()
    content = re.sub(
        r"(?ms)^packages:.*$",
        "packages:\n"
        "  platform: !include platform_bk72xx.yaml\n"
        "  device: !include nebula_light_device.yaml\n",
        content,
    )
    content = content.replace('name: "nebula"', 'name: "nebula-test"', 1)
    (tmp_path / "test_config.yaml").write_text(content)

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
        [ESPHOME, "config", "test_config.yaml"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "Configuration is valid!" in output
    # No plaintext web-server OTA listener should be compiled in.
    assert "platform: web_server" not in output
