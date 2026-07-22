"""first-party Claude Code plugin adapterのテスト。"""

import json
import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins/claude-nagger"
DISPATCH_SCRIPT = PLUGIN_ROOT / "scripts/dispatch-hook.sh"
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin/marketplace.json"


def _load_json(relative_path: str) -> dict:
    return json.loads((PLUGIN_ROOT / relative_path).read_text())


def _configured_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    nagger_dir = project_root / ".claude-nagger"
    nagger_dir.mkdir(parents=True)
    (nagger_dir / "config.yaml").write_text("{}\n")
    return project_root


def _fake_core(tmp_path: Path) -> tuple[Path, Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    args_file = tmp_path / "core-args.txt"
    stdin_file = tmp_path / "core-stdin.txt"
    executable = bin_dir / "claude-nagger"
    executable.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$*\" > \"$FAKE_ARGS_FILE\"\n"
        "cat > \"$FAKE_STDIN_FILE\"\n"
    )
    executable.chmod(0o755)
    return bin_dir, args_file, stdin_file


def test_plugin_manifest_identifies_first_party_bundle():
    manifest = _load_json(".claude-plugin/plugin.json")

    assert manifest["name"] == "claude-nagger"
    assert manifest["author"]["name"] == "HollySizzle"
    assert manifest["repository"].endswith("/claude-nagger")
    assert manifest["license"] == "MIT"


def test_marketplace_identifies_actual_maintainer_and_plugin():
    marketplace = json.loads(MARKETPLACE_PATH.read_text())
    manifest = _load_json(".claude-plugin/plugin.json")

    assert marketplace["name"] == "claude-nagger-marketplace"
    assert marketplace["owner"] == {"name": "HollySizzle"}
    provenance_fields = {
        key: value
        for key, value in marketplace.items()
        if key != "$schema"
    }
    provenance_text = json.dumps(provenance_fields).lower()
    assert "anthropic" not in provenance_text
    assert "claude-code-plugins" not in provenance_text
    assert len(marketplace["plugins"]) == 1

    entry = marketplace["plugins"][0]
    assert entry["name"] == manifest["name"]
    assert entry["version"] == manifest["version"]
    assert entry["author"] == manifest["author"]
    assert entry["source"] == "./plugins/claude-nagger"


def test_hooks_use_plugin_root_and_thin_dispatch():
    hook_config = _load_json("hooks/hooks.json")
    commands = [
        hook["command"]
        for groups in hook_config["hooks"].values()
        for group in groups
        for hook in group["hooks"]
    ]

    assert commands
    assert all("${CLAUDE_PLUGIN_ROOT}" in command for command in commands)
    assert all("dispatch-hook.sh" in command for command in commands)
    assert all("pip install" not in command for command in commands)

    command_text = "\n".join(commands)
    expected_hooks = {
        "session-startup",
        "implementation-design",
        "sendmessage-guard",
        "suggest-rules-trigger",
        "transcript-storage",
        "compact-detected",
        "subagent-event",
        "redmine-discord",
    }
    assert all(hook_name in command_text for hook_name in expected_hooks)


def test_compatibility_is_machine_readable():
    compatibility = _load_json("compatibility.json")

    assert compatibility["schema_version"] == 1
    assert compatibility["adapter_protocol"] == 1
    assert compatibility["claude_code"]["minimum_version"]
    assert compatibility["claude_nagger_core"]["minimum_version"]
    assert compatibility["dependency_install_policy"] == "explicit_only"


def test_missing_config_does_not_invoke_core_or_create_files(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    bin_dir, args_file, stdin_file = _fake_core(tmp_path)
    env = os.environ.copy()
    env.update({
        "CLAUDE_PROJECT_DIR": str(project_root),
        "PATH": f"{bin_dir}:{env.get('PATH', '')}",
        "FAKE_ARGS_FILE": str(args_file),
        "FAKE_STDIN_FILE": str(stdin_file),
    })

    result = subprocess.run(
        [str(DISPATCH_SCRIPT), "implementation-design"],
        input='{"tool_name":"Bash"}',
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert not args_file.exists()
    assert not stdin_file.exists()
    assert list(project_root.iterdir()) == []


def test_configured_project_forwards_hook_name_and_stdin(tmp_path):
    project_root = _configured_project(tmp_path)
    bin_dir, args_file, stdin_file = _fake_core(tmp_path)
    env = os.environ.copy()
    env.update({
        "CLAUDE_PROJECT_DIR": str(project_root),
        "PATH": f"{bin_dir}:{env.get('PATH', '')}",
        "FAKE_ARGS_FILE": str(args_file),
        "FAKE_STDIN_FILE": str(stdin_file),
    })
    payload = '{"tool_name":"Bash"}'

    result = subprocess.run(
        [str(DISPATCH_SCRIPT), "implementation-design"],
        input=payload,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert args_file.read_text().strip() == "hook implementation-design"
    assert stdin_file.read_text() == payload


def test_missing_core_returns_diagnostic_without_install(tmp_path):
    project_root = _configured_project(tmp_path)
    env = os.environ.copy()
    env.update({
        "CLAUDE_PROJECT_DIR": str(project_root),
        "PATH": "/usr/bin:/bin",
    })

    result = subprocess.run(
        [str(DISPATCH_SCRIPT), "implementation-design"],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert "core CLI not found" in result.stderr


@pytest.mark.parametrize("hook_name", ["", "unknown", "../../command"])
def test_unsupported_hook_name_is_rejected(hook_name):
    result = subprocess.run(
        [str(DISPATCH_SCRIPT), hook_name],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 64
    assert "unsupported hook name" in result.stderr
