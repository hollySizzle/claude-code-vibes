"""hook runtimeのproject opt-in境界テスト。"""

from pathlib import Path

from src.application.hook_runtime import is_project_opted_in, resolve_project_root


def test_explicit_project_root_takes_priority(tmp_path, monkeypatch):
    configured = tmp_path / "configured"
    (configured / ".claude-nagger").mkdir(parents=True)
    (configured / ".claude-nagger/config.yaml").write_text("{}\n")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path / "other"))

    assert resolve_project_root(configured) == configured
    assert is_project_opted_in(configured) is True


def test_claude_project_dir_is_used(tmp_path, monkeypatch):
    (tmp_path / ".claude-nagger").mkdir()
    (tmp_path / ".claude-nagger/config.yaml").write_text("{}\n")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))

    assert resolve_project_root() == tmp_path
    assert is_project_opted_in() is True


def test_cwd_without_config_is_not_opted_in(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)

    assert resolve_project_root() == Path.cwd()
    assert is_project_opted_in() is False
    assert not (tmp_path / ".claude-nagger").exists()
