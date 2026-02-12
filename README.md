# ⚡ Agent Command Center (`acc`)

A Python+Textual TUI that monitors and manages independent AI coding agent sessions (Claude Code, OpenCode, Codex, Aider, etc.) running in tmux panes. See all sessions at a glance, track status, surface links, and jump into any session when needed.

## Features

- **Multi-agent support** — Works with Claude Code, OpenCode, Codex, Aider, and custom agents
- **Auto-discovery** — Finds agent sessions in tmux by walking process trees
- **Status detection** — 🟢 Working / 🟡 Idle / 🔴 Needs input / ✅ Done / 💀 Crashed
- **LLM summarization** — Uses Claude Haiku to extract goals and progress from terminal output
- **Link detection** — Surfaces GitHub PRs, issues, Linear tickets, localhost URLs, and custom patterns
- **Notifications** — Terminal bell + badge on state transitions
- **Session spawning** — Launch new Claude sessions with `n`
- **Quick navigation** — `Enter` to jump straight into a tmux pane

## Install

```bash
# From source
uv tool install .

# Or run directly
uv run acc
```

## Usage

```bash
# Launch the command center
acc

# With custom claude path
CLAUDE_PATH=~/.local/bin/claude acc
```

### Keybindings

| Key | Action |
|-----|--------|
| `↑/↓` or `j/k` | Navigate session list |
| `Enter` | Jump to tmux pane |
| `n` | Spawn new Claude session |
| `o` | Open link in browser |
| `r` | Force refresh summaries |
| `q` | Quit |

## Configuration

Create `~/.config/acc/config.yaml`:

```yaml
claude_path: claude
tmux_session: acc
refresh_interval: 3
summary_interval: 60
summary_model: haiku

links:
  - name: jira
    icon: "🎫"
    pattern: "[A-Z]{2,}-\\d+"
    label: "Jira"

# Custom agent detectors for attention detection
agents:
  - name: MyCustomAgent
    process_names: ["myagent", "ma"]
    attention_patterns:
      - "\\\\?\\s*$"
      - "waiting for input"
    working_patterns:
      - "processing"
      - "loading"
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PATH` | `claude` | Path to claude binary |
| `ACC_TMUX_SESSION` | `acc` | Tmux session for spawned panes |
| `ACC_REFRESH_INTERVAL` | `3` | Poll interval (seconds) |
| `ACC_SUMMARY_INTERVAL` | `60` | LLM re-summarization interval |
| `ACC_MODEL` | `haiku` | Model for summarization |

## Development

```bash
uv sync
uv run pytest tests/ -v
```

## Verification

To verify the installation and functionality:

1. **Start a test session:**
   ```bash
   tmux new-session -d -s test-acc "echo 'Simulating agent...'; sleep 3600"
   ```

2. **Run acc:**
   ```bash
   acc
   ```
   You should see the "Simon Says..." session listed.

3. **Interact:**
   - Use `Up`/`Down` to select the session.
   - Press `i` to send input (e.g., `ls -la`) directly.
   - Press `Enter` to attach to the full tmux session (take control).
