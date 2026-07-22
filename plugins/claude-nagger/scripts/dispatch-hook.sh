#!/bin/sh

set -u

hook_name=${1-}

case "$hook_name" in
  session-startup|implementation-design|compact-detected|suggest-rules-trigger|transcript-storage|subagent-event|sendmessage-guard|redmine-discord)
    ;;
  *)
    printf '%s\n' "claude-nagger plugin: unsupported hook name: $hook_name" >&2
    exit 64
    ;;
esac

project_root=${CLAUDE_PROJECT_DIR:-"$(pwd)"}
project_config="$project_root/.claude-nagger/config.yaml"

# Pluginはproject設定を生成しない。configが無ければ未採用として扱う。
if [ ! -f "$project_config" ]; then
  exit 0
fi

# Hook実行中にdependencyをinstallしない。診断を返してfail-openする。
if ! command -v claude-nagger >/dev/null 2>&1; then
  printf '%s\n' \
    "claude-nagger plugin: core CLI not found; install claude-nagger explicitly" >&2
  exit 0
fi

exec claude-nagger hook "$hook_name"
