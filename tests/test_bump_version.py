"""Tests for the release version-bump helper.

The helper resolves the repo root from its own location, so each test copies it
into an isolated temporary repo and runs that copy.
"""

import shutil
import subprocess
import sys
import textwrap

from conftest import REPO_ROOT

TOOL = REPO_ROOT / "tools" / "bump_version.py"

TEMPLATE = textwrap.dedent(
    """\
    esphome:
      name: "nebula"
      project:
        name: "njoerd114.esphome_sk20_nebula_light"
        version: "2026.10.0"
    """
)


def _make_repo(tmp_path, content=TEMPLATE):
    (tmp_path / "tools").mkdir()
    shutil.copy(TOOL, tmp_path / "tools" / "bump_version.py")
    (tmp_path / "recommended_base.yaml").write_text(content)
    return tmp_path


def _run_bump(repo, version):
    return subprocess.run(
        [sys.executable, str(repo / "tools" / "bump_version.py"), version],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def test_bump_sets_project_version(tmp_path):
    repo = _make_repo(tmp_path)
    result = _run_bump(repo, "2026.10.1")
    assert result.returncode == 0, result.stderr
    content = (repo / "recommended_base.yaml").read_text()
    assert 'version: "2026.10.1"' in content
    assert content.count('version: "') == 1


def test_bump_leaves_other_versions_untouched(tmp_path):
    content = TEMPLATE + '    min_version: "2026.9.1"\n'
    repo = _make_repo(tmp_path, content)
    _run_bump(repo, "2026.11.0")
    text = (repo / "recommended_base.yaml").read_text()
    assert 'version: "2026.11.0"' in text
    assert 'min_version: "2026.9.1"' in text


def test_bump_missing_version_fails(tmp_path):
    repo = _make_repo(tmp_path, content='esphome:\n  name: "nebula"\n')
    result = _run_bump(repo, "2026.10.1")
    assert result.returncode != 0
