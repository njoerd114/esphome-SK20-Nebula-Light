"""Structural tests for the ESPHome device/base configuration."""

import re

import pytest

from conftest import REPO_ROOT, find, load_yaml

# Scenes that must be static (clear any running effect).
STATIC_SCENES = {0, 1, 2, 3, 4, 5, 7}
# Scenes that start a named effect.
EFFECT_SCENES = {6: "Galaxy Travel", 8: "Strobe"}


def _scene_blocks(device):
    blocks = {}
    for step in device["select"]["on_value"]["then"]:
        if not (isinstance(step, dict) and "if" in step):
            continue
        condition = step["if"]["condition"]
        match = re.search(r"active_index\(\) == (\d+)", str(condition))
        if match:
            blocks[int(match.group(1))] = step["if"]["then"]
    return blocks


def _rgb_effect(actions):
    for action in actions:
        if isinstance(action, dict) and "light.turn_on" in action:
            cfg = action["light.turn_on"]
            if isinstance(cfg, dict) and cfg.get("id") == "rgb_light":
                return cfg.get("effect")
    return None


def test_calibration_substitutions(device):
    subs = device["substitutions"]
    assert subs["rgb_min_power"] == "20%"
    assert subs["laser_min_power"] == "56%"
    assert subs["motor_min_power"] == "15%"


@pytest.mark.parametrize("channel", ["red", "green", "blue"])
def test_rgb_outputs_are_calibrated(device, channel):
    out = find(device["output"], "id", channel)
    assert out["min_power"] == "${rgb_min_power}"
    assert out["zero_means_zero"] is True


def test_laser_and_motor_outputs_are_calibrated(device):
    laser = find(device["output"], "id", "laser_pwm")
    assert laser["min_power"] == "${laser_min_power}"
    assert laser["zero_means_zero"] is True

    motor = find(device["output"], "id", "motor_pwm")
    assert motor["min_power"] == "${motor_min_power}"
    assert motor["zero_means_zero"] is True


def test_laser_gamma_correction(device):
    assert find(device["light"], "id", "laser")["gamma_correct"] == 2.0


def test_motor_stays_a_speed_fan(device):
    # Tier 3 #1 (motor -> light) was not requested; the motor must remain a fan.
    assert device["fan"]["platform"] == "speed"
    assert device["fan"]["id"] == "motor"


def test_main_switch_uses_target_state_and_ignores_motor(device):
    lam = find(device["switch"], "id", "switch_main")["lambda"]
    assert "remote_values" in lam
    assert "motor" not in lam


def test_main_switch_restores_saved_state(device):
    switch = find(device["switch"], "id", "switch_main")
    text = str(switch["turn_on_action"])
    for global_id in ("saved_rgb_on", "saved_laser_on", "saved_motor_on"):
        assert global_id in text
    # The auto-off timer must be re-armed on restore.
    assert "script_turn_off_timer" in text


def test_sync_script_snapshots_and_stops_motor(device):
    script = str(find(device["script"], "id", "script_sync_state"))
    assert "saved_rgb_on" in script
    assert "id(motor).state" in script


def test_scene_options_extended(device):
    options = device["select"]["options"]
    assert options[:5] == [
        "Scene - Red",
        "Scene - Blue",
        "Scene - Green",
        "Scene - White",
        "Scene - Dimmed",
    ]
    assert "Scene - Red & Blue" in options
    assert "Scene - Galaxy" in options
    assert "Scene - Night Light" in options
    assert "Scene - Party" in options
    assert len(options) >= 8


def test_static_scenes_clear_effects_and_effect_scenes_set_them(device):
    blocks = _scene_blocks(device)
    assert set(blocks) == STATIC_SCENES | set(EFFECT_SCENES)

    for index in STATIC_SCENES:
        assert _rgb_effect(blocks[index]) == "None", f"scene {index} should clear effects"

    for index, effect in EFFECT_SCENES.items():
        assert _rgb_effect(blocks[index]) == effect, f"scene {index} should run {effect}"


def test_api_encryption_configured(base):
    assert base["api"]["encryption"]["key"] == "api_key"


def test_ota_encrypted_and_password_removed(base):
    ota = base["ota"]
    assert isinstance(ota, list)
    esphome_ota = [entry for entry in ota if entry.get("platform") == "esphome"][0]
    assert "password" not in esphome_ota
    assert esphome_ota["encryption"]["key"] == "api_key"


def test_web_server_ota_disabled(base):
    assert base["web_server"]["ota"] is False


def test_captive_portal_not_enabled(base):
    # The captive portal would re-add a plaintext web-server OTA listener.
    assert "captive_portal" not in base


def test_project_metadata(base):
    project = base["esphome"]["project"]
    assert project["name"] == "njoerd114.esphome_sk20_nebula_light"
    assert project["version"].count(".") == 2
    assert "min_version" in base["esphome"]


def test_packages_point_at_this_fork(base):
    url = base["packages"]["remote_package"]["url"]
    assert "njoerd114" in url


def test_diagnostics_present(base):
    assert any("wifi_info" in str(sensor) for sensor in base["text_sensor"])
    platforms = [sensor["platform"] for sensor in base["sensor"]]
    assert "uptime" in platforms
    assert "wifi_signal" in platforms


def test_secrets_template_matches_config():
    text = (REPO_ROOT / "secrets-template.yaml").read_text()
    assert "api_key:" in text
    assert "ota_password" not in text
    assert "api_password" not in text


@pytest.mark.parametrize("name", ["recommended_base.yaml", "nebula_light_device.yaml"])
def test_no_ota_password_referenced(name):
    assert "ota_password" not in (REPO_ROOT / name).read_text()


def test_local_build_uses_local_packages():
    # local.yaml must include the working-copy files, not the remote package.
    local = load_yaml("local.yaml")
    assert local["packages"]["platform"] == "platform_bk72xx.yaml"
    assert local["packages"]["device"] == "nebula_light_device.yaml"
