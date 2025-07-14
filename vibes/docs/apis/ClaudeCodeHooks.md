---
created: 2025-07-08T19:46:59 (UTC +09:00)
tags: []
source: https://docs.anthropic.com/en/docs/claude-code/hooks
author:
---

# Hooks - Anthropic

> ## Excerpt
>
> Customize and extend Claude Code's behavior by registering shell commands

---

## Introduction

Claude Code hooks are user-defined shell commands that execute at various points in Claude Code’s lifecycle. Hooks provide deterministic control over Claude Code’s behavior, ensuring certain actions always happen rather than relying on the LLM to choose to run them.

Example use cases include:

- **Notifications**: Customize how you get notified when Claude Code is awaiting your input or permission to run something.
- **Automatic formatting**: Run `prettier` on .ts files, `gofmt` on .go files, etc. after every file edit.
- **Logging**: Track and count all executed commands for compliance or debugging.
- **Feedback**: Provide automated feedback when Claude Code produces code that does not follow your codebase conventions.
- **Custom permissions**: Block modifications to production files or sensitive directories.

By encoding these rules as hooks rather than prompting instructions, you turn suggestions into app-level code that executes every time it is expected to run.

## Quickstart

In this quickstart, you’ll add a hook that logs the shell commands that Claude Code runs.

Quickstart Prerequisite: Install `jq` for JSON processing in the command line.

### Step 1: Open hooks configuration

Run the `/hooks` [slash command](https://docs.anthropic.com/en/docs/claude-code/slash-commands) and select the `PreToolUse` hook event.

`PreToolUse` hooks run before tool calls and can block them while providing Claude feedback on what to do differently.

### Step 2: Add a matcher

Select `+ Add new matcher…` to run your hook only on Bash tool calls.

Type `Bash` for the matcher.

### Step 3: Add the hook

Select `+ Add new hook…` and enter this command:

### Step 4: Save your configuration

For storage location, select `User settings` since you’re logging to your home directory. This hook will then apply to all projects, not just your current project.

Then press Esc until you return to the REPL. Your hook is now registered!

### Step 5: Verify your hook

Run `/hooks` again or check `~/.claude/settings.json` to see your configuration:

## Configuration

Claude Code hooks are configured in your [settings files](https://docs.anthropic.com/en/docs/claude-code/settings):

- `~/.claude/settings.json` - User settings
- `.claude/settings.json` - Project settings
- `.claude/settings.local.json` - Local project settings (not committed)
- Enterprise managed policy settings

### Structure

Hooks are organized by matchers, where each matcher can have multiple hooks:

- **matcher**: Pattern to match tool names (only applicable for `PreToolUse` and `PostToolUse`)
  - Simple strings match exactly: `Write` matches only the Write tool
  - Supports regex: `Edit|Write` or `Notebook.*`
  - If omitted or empty string, hooks run for all matching events
- **hooks**: Array of commands to execute when the pattern matches
  - `type`: Currently only `"command"` is supported
  - `command`: The bash command to execute
  - `timeout`: (Optional) How long a command should run, in seconds, before canceling that specific command.

## Hook Events

### PreToolUse

Runs after Claude creates tool parameters and before processing the tool call.

**Common matchers:**

- `Task` - Agent tasks
- `Bash` - Shell commands
- `Glob` - File pattern matching
- `Grep` - Content search
- `Read` - File reading
- `Edit`, `MultiEdit` - File editing
- `Write` - File writing
- `WebFetch`, `WebSearch` - Web operations

### PostToolUse

Runs immediately after a tool completes successfully.

Recognizes the same matcher values as PreToolUse.

### Notification

Runs when Claude Code sends notifications.

### Stop

Runs when the main Claude Code agent has finished responding.

### SubagentStop

Runs when a Claude Code subagent (Task tool call) has finished responding.

## Hook Input

Hooks receive JSON data via stdin containing session information and event-specific data:

### PreToolUse Input

The exact schema for `tool_input` depends on the tool.

### PostToolUse Input

The exact schema for `tool_input` and `tool_response` depends on the tool.

### Notification Input

### Stop and SubagentStop Input

`stop_hook_active` is true when Claude Code is already continuing as a result of a stop hook. Check this value or process the transcript to prevent Claude Code from running indefinitely.

## Hook Output

There are two ways for hooks to return output back to Claude Code. The output communicates whether to block and any feedback that should be shown to Claude and the user.

### Simple: Exit Code

Hooks communicate status through exit codes, stdout, and stderr:

- **Exit code 0**: Success. `stdout` is shown to the user in transcript mode (CTRL-R).
- **Exit code 2**: Blocking error. `stderr` is fed back to Claude to process automatically. See per-hook-event behavior below.
- **Other exit codes**: Non-blocking error. `stderr` is shown to the user and execution continues.

#### Exit Code 2 Behavior

| Hook Event     | Behavior                                        |
| -------------- | ----------------------------------------------- |
| `PreToolUse`   | Blocks the tool call, shows error to Claude     |
| `PostToolUse`  | Shows error to Claude (tool already ran)        |
| `Notification` | N/A, shows stderr to user only                  |
| `Stop`         | Blocks stoppage, shows error to Claude          |
| `SubagentStop` | Blocks stoppage, shows error to Claude subagent |

### Advanced: JSON Output

Hooks can return structured JSON in `stdout` for more sophisticated control:

#### Common JSON Fields

All hook types can include these optional fields:

If `continue` is false, Claude stops processing after the hooks run.

- For `PreToolUse`, this is different from `"decision": "block"`, which only blocks a specific tool call and provides automatic feedback to Claude.
- For `PostToolUse`, this is different from `"decision": "block"`, which provides automated feedback to Claude.
- For `Stop` and `SubagentStop`, this takes precedence over any `"decision": "block"` output.
- In all cases, `"continue" = false` takes precedence over any `"decision": "block"` output.

`stopReason` accompanies `continue` with a reason shown to the user, not shown to Claude.

#### `PreToolUse` Decision Control

`PreToolUse` hooks can control whether a tool call proceeds.

- “approve” bypasses the permission system. `reason` is shown to the user but not to Claude.
- “block” prevents the tool call from executing. `reason` is shown to Claude.
- `undefined` leads to the existing permission flow. `reason` is ignored.

#### `PostToolUse` Decision Control

`PostToolUse` hooks can control whether a tool call proceeds.

- “block” automatically prompts Claude with `reason`.
- `undefined` does nothing. `reason` is ignored.

#### `Stop`/`SubagentStop` Decision Control

`Stop` and `SubagentStop` hooks can control whether Claude must continue.

- “block” prevents Claude from stopping. You must populate `reason` for Claude to know how to proceed.
- `undefined` allows Claude to stop. `reason` is ignored.

#### JSON Output Example: Bash Command Editing

Claude Code hooks work seamlessly with [Model Context Protocol (MCP) tools](https://docs.anthropic.com/en/docs/claude-code/mcp). When MCP servers provide tools, they appear with a special naming pattern that you can match in your hooks.

### MCP Tool Naming

MCP tools follow the pattern `mcp__<server>__<tool>`, for example:

- `mcp__memory__create_entities` - Memory server’s create entities tool
- `mcp__filesystem__read_file` - Filesystem server’s read file tool
- `mcp__github__search_repositories` - GitHub server’s search tool

### Configuring Hooks for MCP Tools

You can target specific MCP tools or entire MCP servers:

## Examples

### Code Formatting

Automatically format code after file modifications:

### Notification

Customize the notification that is sent when Claude Code requests permission or when the prompt input has become idle.

## Security Considerations

### Disclaimer

**USE AT YOUR OWN RISK**: Claude Code hooks execute arbitrary shell commands on your system automatically. By using hooks, you acknowledge that:

- You are solely responsible for the commands you configure
- Hooks can modify, delete, or access any files your user account can access
- Malicious or poorly written hooks can cause data loss or system damage
- Anthropic provides no warranty and assumes no liability for any damages resulting from hook usage
- You should thoroughly test hooks in a safe environment before production use

Always review and understand any hook commands before adding them to your configuration.

### Security Best Practices

Here are some key practices for writing more secure hooks:

1.  **Validate and sanitize inputs** - Never trust input data blindly
2.  **Always quote shell variables** - Use `"$VAR"` not `$VAR`
3.  **Block path traversal** - Check for `..` in file paths
4.  **Use absolute paths** - Specify full paths for scripts
5.  **Skip sensitive files** - Avoid `.env`, `.git/`, keys, etc.

### Configuration Safety

Direct edits to hooks in settings files don’t take effect immediately. Claude Code:

1.  Captures a snapshot of hooks at startup
2.  Uses this snapshot throughout the session
3.  Warns if hooks are modified externally
4.  Requires review in `/hooks` menu for changes to apply

This prevents malicious hook modifications from affecting your current session.

## Hook Execution Details

- **Timeout**: 60-second execution limit by default, configurable per command.
  - A timeout for an individual command does not affect the other commands.
- **Parallelization**: All matching hooks run in parallel
- **Environment**: Runs in current directory with Claude Code’s environment
- **Input**: JSON via stdin
- **Output**:
  - PreToolUse/PostToolUse/Stop: Progress shown in transcript (Ctrl-R)
  - Notification: Logged to debug only (`--debug`)

## Debugging

To troubleshoot hooks:

1.  Check if `/hooks` menu displays your configuration
2.  Verify that your [settings files](https://docs.anthropic.com/en/docs/claude-code/settings) are valid JSON
3.  Test commands manually
4.  Check exit codes
5.  Review stdout and stderr format expectations
6.  Ensure proper quote escaping
7.  Use `claude --debug` to debug your hooks. The output of a successful hook appears like below.

Progress messages appear in transcript mode (Ctrl-R) showing:

- Which hook is running
- Command being executed
- Success/failure status
- Output or error messages
