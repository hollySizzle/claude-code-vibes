# claude-nagger Claude Code plugin

Claude Code の plugin loader から、既存の `claude-nagger hook` entrypointへ処理を渡す薄いadapterです。

## 前提

- `claude-nagger` core CLIを利用者が明示的にinstallしていること
- 適用するprojectに `.claude-nagger/config.yaml` が存在すること

configが無いprojectでは何も生成せず終了します。core CLIが無い場合もhook内でinstallせず、診断を出してfail-openします。

このadapterはcoreの `hook` entrypointだけを登録します。legacy settingsに含まれるDiscord `Notification` / `Stop`通知は現時点では移行対象外です。

## 検証

```bash
claude plugin validate ./plugins/claude-nagger --strict
```

配布・marketplace表記・責任境界の正本は[plugin配布architecture・guardrail](https://github.com/hollySizzle/claude-nagger/blob/main/docs/specs/claude_code_plugin_distribution.yaml)です。
