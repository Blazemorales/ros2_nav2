#!/usr/bin/env bash
# Configure ollmcp (mcp-client-for-ollama) to talk to the rover through the
# restricted rover_mcp_safe proxy -- never to the raw ros-mcp server.
#
#   pipx install ros-mcp ollmcp
#   ollama pull qwen2.5:7b
#   tools/rover_mcp_safe/setup_ollmcp.sh [ROSBRIDGE_IP] [MODEL]
#   ollmcp -j ~/.config/ollmcp/rover-servers.json
#
# Writes ~/.config/ollmcp/rover-servers.json (always) and
# ~/.config/ollmcp/config.json (only if it does not exist yet).
set -euo pipefail

ROSBRIDGE_IP="${1:-127.0.0.1}"
MODEL="${2:-qwen2.5:7b}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="$(pipx environment --value PIPX_LOCAL_VENVS)/ros-mcp/bin/python"
CFG_DIR="$HOME/.config/ollmcp"
mkdir -p "$CFG_DIR"

[ -x "$VENV_PY" ] || { echo "ros-mcp venv not found: run 'pipx install ros-mcp'" >&2; exit 1; }

"$VENV_PY" -I - "$HERE" "$VENV_PY" "$ROSBRIDGE_IP" "$MODEL" "$CFG_DIR" <<'EOF'
import json, os, sys
here, py, ip, model, cfg_dir = sys.argv[1:]
servers = {"mcpServers": {"rover": {
    "command": py,
    "args": ["-I", os.path.join(here, "rover_mcp_safe.py")],
    "env": {"ROSBRIDGE_IP": ip, "ROSBRIDGE_PORT": "9090"},
}}}
p = os.path.join(cfg_dir, "rover-servers.json")
json.dump(servers, open(p, "w"), indent=2)
print("wrote", p)

cfg = os.path.join(cfg_dir, "config.json")
if os.path.exists(cfg):
    print("kept existing", cfg, "(set temperature 0.1 in ollmcp: 'model-config')")
    sys.exit(0)
sys.path.insert(0, here)
src = open(os.path.join(here, "rover_mcp_safe.py")).read()
start = src.index('INSTRUCTIONS = """\\\n') + len('INSTRUCTIONS = """\\\n')
prompt = src[start:src.index('"""', start)]
json.dump({
    "defaultProvider": "ollama",
    "providers": {"ollama": {"host": "http://localhost:11434", "model": model, "apiKey": ""}},
    "enabledTools": {},
    "contextSettings": {"retainContext": True},
    # qwen2.5 is not a "thinking" model
    "modelSettings": {"thinkingMode": False, "showThinking": False},
    "agentSettings": {"loopLimit": 7},
    # Low temperature: above ~0.1 small local models invent tool names
    # and emit malformed JSON arguments.
    "modelConfig": {"system_prompt": prompt, "temperature": 0.1},
    "displaySettings": {"showToolExecution": True, "showMetrics": True,
                        "answerRenderMode": "markdown"},
    "inputSettings": {"inputMode": "single"},
    # Human-in-the-loop: confirm every tool call before it runs.
    "hilSettings": {"enabled": True},
}, open(cfg, "w"), indent=2)
print("wrote", cfg)
EOF
