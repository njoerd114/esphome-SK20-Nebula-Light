"""Shared pytest fixtures and helpers for the ESPHome config tests."""

import pathlib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


class _ConfigLoader(yaml.SafeLoader):
    """SafeLoader that tolerates ESPHome tags such as !secret and !lambda."""


def _construct_unknown(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


_ConfigLoader.add_multi_constructor("!", _construct_unknown)


def load_yaml(name):
    """Load a repo YAML file, ignoring ESPHome-specific tags."""
    return yaml.load((REPO_ROOT / name).read_text(), Loader=_ConfigLoader)


def find(items, key, value):
    """Return the first mapping in ``items`` whose ``key`` equals ``value``."""
    for item in items or []:
        if isinstance(item, dict) and item.get(key) == value:
            return item
    return None


@pytest.fixture(scope="session")
def device():
    return load_yaml("nebula_light_device.yaml")


@pytest.fixture(scope="session")
def base():
    return load_yaml("recommended_base.yaml")
