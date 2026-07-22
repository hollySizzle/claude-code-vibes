"""Claude Code hook runtime の project opt-in 判定。"""

import os
from pathlib import Path
from typing import Optional


PROJECT_CONFIG_PATH = Path(".claude-nagger/config.yaml")


def resolve_project_root(project_root: Optional[Path] = None) -> Path:
    """hook対象projectのrootを副作用なしで解決する。"""
    if project_root is not None:
        return Path(project_root)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if claude_project_dir:
        return Path(claude_project_dir)

    return Path.cwd()


def is_project_opted_in(project_root: Optional[Path] = None) -> bool:
    """project configが実在する場合のみclaude-nagger採用済みと判定する。"""
    return (resolve_project_root(project_root) / PROJECT_CONFIG_PATH).is_file()
