#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

SESSION=${SESSION:-server-agentic-operator}
CONDA_ENV=${CONDA_ENV:-com3d-ace}
INTERVAL=${INTERVAL:-900}
ENABLE_ORCHESTRATOR_START=${ENABLE_ORCHESTRATOR_START:-0}
ENABLE_AUTO_RESEARCH=${ENABLE_AUTO_RESEARCH:-1}
ENABLE_PUBLISH=${ENABLE_PUBLISH:-0}
ENABLE_NOTION=${ENABLE_NOTION:-0}
ENABLE_OLLAMA_OPERATOR=${ENABLE_OLLAMA_OPERATOR:-1}
ENABLE_OPENAI_ANALYST=${ENABLE_OPENAI_ANALYST:-0}
OLLAMA_MODEL=${OLLAMA_MODEL:-}
OPENAI_ANALYST_MODEL=${OPENAI_ANALYST_MODEL:-gpt-5.2}
LOG_DIR=${LOG_DIR:-outputs/logs/agentic_operator}

mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION"
  echo "Attach with: tmux attach -t $SESSION"
  exit 0
fi

args=(--interval "$INTERVAL")
if [[ "$ENABLE_ORCHESTRATOR_START" == "1" ]]; then
  args+=(--enable-orchestrator-start)
fi
if [[ "$ENABLE_AUTO_RESEARCH" == "1" ]]; then
  args+=(--enable-auto-research)
fi
if [[ "$ENABLE_PUBLISH" == "1" ]]; then
  args+=(--enable-publish)
fi
if [[ "$ENABLE_NOTION" == "1" ]]; then
  args+=(--enable-notion)
fi
if [[ "$ENABLE_OLLAMA_OPERATOR" == "1" && -n "$OLLAMA_MODEL" ]]; then
  args+=(--enable-ollama --ollama-model "$OLLAMA_MODEL")
fi
if [[ "$ENABLE_OPENAI_ANALYST" == "1" ]]; then
  args+=(--enable-openai --openai-model "$OPENAI_ANALYST_MODEL")
fi

tmux new-session -d -s "$SESSION" -n operator \
  "cd '$PWD' && ENABLE_OPENAI_ANALYST='$ENABLE_OPENAI_ANALYST' ENABLE_OLLAMA_OPERATOR='$ENABLE_OLLAMA_OPERATOR' OLLAMA_MODEL='$OLLAMA_MODEL' OPENAI_ANALYST_MODEL='$OPENAI_ANALYST_MODEL' conda run --no-capture-output -n '$CONDA_ENV' python -m scripts.agentic_operator_loop ${args[*]} 2>&1 | tee '$LOG_DIR/operator.log'"

echo "Started agentic operator: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Status: outputs/automation/agentic_operator_status.md"
echo "OpenAI analyst: ${ENABLE_OPENAI_ANALYST} (set OPENAI_API_KEY to enable a real OpenAI call)"
echo "Log: $LOG_DIR/operator.log"
