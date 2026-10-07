---
name: token-efficient-workflow
description: Rules to minimise token consumption — truncate output, split tasks, compact early, query graphify not extract, use subagents for exploration
---

# Token-Efficient Workflow

> Token cost is ~99% input (re-sent conversation history). Every line of terminal output and every file read is re-sent on every subsequent turn. These rules keep the context small.

## 1. Truncate all CLI output
- Pipe verbose commands through `Select-Object -Last 20` or `Select-String -Pattern 'error|Error'`.
- Redirect >50-line outputs to a temp file; return only the summary or error lines.
- `dotnet build` / `dotnet test`: **never** return 5000+ warnings — filter to errors only.
- `graphify extract`: redirect to a file, read only the summary line.

## 2. Split long workflows into separate prompts
- Build, test, and debug are **separate conversations** — do not chain them in one.
- Start a new chat between major phases; paste a 5-line state summary (ticket key, files changed, build status, test count, next step).
- Each new prompt starts with a fresh, small context window.

## 3. Compact early
- Trigger `/compact` when the conversation exceeds 30 messages — do not wait for auto-compaction at 100+.
- A 24-request conversation at 80K tokens/request (1.92M) becomes 3 conversations of ~8 requests at 40K (960K).

## 4. Query graphify, don't extract
- `graphify extract` is run **ONCE**, outside the agent loop (in a standalone terminal).
- Inside agents, use only:
  - `graphify query "<question>"` — scoped subgraph of relevant nodes + files
  - `graphify explain "<symbol>"` — a symbol's connections, source file:line, community
  - `graphify path "<SymbolA>" "<SymbolB>"` — how two things connect
- These return targeted, compact results instead of dumping hundreds of NODE lines into context.

## 5. Never re-run a failing command
- Capture errors once, fix the root cause, then rebuild.
- Do not re-capture the same large error output 3–4 times.

## 6. Use subagents for exploration
- Delegate file-reading sprees to the `Explore` subagent.
- Only its compact summary enters the main context — the full exploration stays out.
- Prefer this over reading 10 files inline (each adding to the conversation).

## 7. Prefer targeted project builds
- `dotnet build <Project>.csproj --no-restore` instead of full solution builds.
- Full MAUI solution builds produce 5000+ warnings and take 6+ minutes — avoid inside the agent loop.