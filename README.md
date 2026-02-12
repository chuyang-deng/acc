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

### User Install (Recommended)

Using **Homebrew**:
```bash
brew tap chuyang-deng/acc
brew install acc
```

Using **pipx** (application isolation):
```bash
pipx install git+https://github.com/chuyang-deng/acc.git
```

Using **uv**:
```bash
uv tool install git+https://github.com/chuyang-deng/acc.git
```

Using **pip**:
```bash
pip install git+https://github.com/chuyang-deng/acc.git
```

### Developer / Local Install

```bash
# From source folder
pip install -e .

# Or using uv
uv tool install .
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
| `ACC_LLM_API_KEY` | - | Custom API key (optional) |
| `ACC_LLM_BASE_URL` | - | Custom LLM base URL (optional) |

## Advanced Configuration

### Columns

Customize the session table columns:

```yaml
columns:
  - key: "#"
    width: 3
  - key: "status"
    width: 12
  - key: "agent" 
    width: 10
  - key: "goal"
    width: 0 # flexible width
  # Omit columns to hide them
```

### LLM Configuration

Use a local LLM or a different provider compatible with Anthropic client (or just set the key):

```yaml
llm_api_key: "sk-..."
llm_base_url: "https://api.anthropic.com" # or local proxy
summary_model: "claude-3-opus-20240229"
```

### Custom Links

Add regex patterns to detect custom IDs or URLs:

```yaml
links:
  - name: "jira"
    icon: "🎫"
    pattern: "PROJ-\\d+"
    label: "Jira"
```

### Custom Agents

Teach `acc` to recognize other agents or processes:

```yaml
agents:
  - name: "MyAgent"
    process_names: ["run_agent.py"]
    working_patterns:
      - "Thinking..."
    attention_patterns:
      - "User input required:"
```

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
