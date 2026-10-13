#!/usr/bin/env python3
"""PreToolUse + PostToolUse hook: deterministically stops the sub-notify loop.

Some models re-issue a SendSlackMessage/RecordPrompt call over and over
instead of stopping after one invocation, rewording the arguments slightly
each retry. Prompt instructions cannot reliably stop this.

Two layers, because neither alone was sufficient (confirmed via debug logs):
1. PreToolUse: a TIME-based cooldown per (session, tool) denies a repeat
   call to a tool already called recently in this session. This prevents
   the real-world side effect (a duplicate Slack post) regardless of what
   the model does next.
2. PostToolUse: as soon as BOTH watched tools (SendSlackMessage AND
   RecordPrompt) have each completed once in this session, immediately
   emit "continue": false. Waiting for a *denied retry* to signal stop (as
   PreToolUse alone does) still let the model burn several extra turns
   trying again before the denial landed — ending the run right after the
   second tool's own success is faster and avoids that wasted loop.

Reads the hook JSON payload on stdin, writes a JSON decision to stdout.
Any tool not matching the watched set is a fast no-op allow.
"""
import json
import os
import sys
import tempfile
import time

# Only these tools are susceptible to the known loop bug (sub-notify agent).
WATCHED_SUBSTRINGS = ("sendslackmessage", "recordprompt")
# Legitimate separate notifications in the same overall session are always
# minutes/hours apart (real work happens between them). Observed retry
# cadence for the looping model is itself ~60s, so a 60s window was too
# short (a retry landed at 60.6s and slipped through as "new"). 900s (15m)
# stays well above any observed retry gap while remaining well below the
# gap between genuinely distinct workflow-stage notifications.
COOLDOWN_SECONDS = 900
STATE_DIR = os.path.join(tempfile.gettempdir(), "copilot-notify-dedupe")
DONE_SUFFIX = "__done.json"


def respond(decision: dict) -> None:
    print(json.dumps(decision))
    sys.exit(0)


def allow(event_name: str) -> None:
    respond({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "permissionDecision": "allow",
        }
    })


def deny_and_stop(reason: str) -> None:
    # "continue": false ends the agent run outright instead of just
    # rejecting this one call and leaving the model free to retry.
    respond({
        "continue": False,
        "stopReason": reason,
        "systemMessage": reason,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    })


def finish_and_stop(reason: str) -> None:
    respond({
        "continue": False,
        "stopReason": reason,
        "systemMessage": reason,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
        },
    })


def tool_failed(payload: dict) -> bool:
    resp = payload.get("tool_response")
    if isinstance(resp, dict):
        return bool(resp.get("isError") or resp.get("is_error"))
    return bool(payload.get("is_error"))


def handle_pre_tool_use(payload: dict, tool_name: str, session_id: str) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    safe_tool = "".join(c if c.isalnum() else "_" for c in tool_name)
    state_path = os.path.join(STATE_DIR, f"{session_id}__{safe_tool}.json")

    now = time.time()
    prev = None
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as f:
                prev = json.load(f)
        except Exception:
            prev = None

    if prev and (now - prev.get("ts", 0)) < COOLDOWN_SECONDS:
        deny_and_stop(
            f"{tool_name} was already called {round(now - prev['ts'], 1)}s ago in this "
            f"session (cooldown: {COOLDOWN_SECONDS}s). This is the sub-notify loop guard "
            "stopping a repeat call — the notification already went out. Ending this run now."
        )
        return

    with open(state_path, "w") as f:
        json.dump({"ts": now}, f)

    allow("PreToolUse")


def handle_post_tool_use(payload: dict, tool_name: str, session_id: str) -> None:
    if tool_failed(payload):
        allow("PostToolUse")
        return

    os.makedirs(STATE_DIR, exist_ok=True)
    done_path = os.path.join(STATE_DIR, f"{session_id}{DONE_SUFFIX}")
    done = {}
    if os.path.exists(done_path):
        try:
            with open(done_path, "r") as f:
                done = json.load(f)
        except Exception:
            done = {}

    for sub in WATCHED_SUBSTRINGS:
        if sub in tool_name.lower():
            done[sub] = True

    with open(done_path, "w") as f:
        json.dump(done, f)

    if all(sub in done for sub in WATCHED_SUBSTRINGS):
        finish_and_stop(
            "Both sub-notify tools (SendSlackMessage and RecordPrompt) have each "
            "succeeded once in this session. The sub-notify task is complete — "
            "stopping this run now instead of letting the model retry."
        )
        return

    allow("PostToolUse")


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        allow("PreToolUse")
        return

    tool_name = str(payload.get("tool_name", ""))
    if not any(sub in tool_name.lower() for sub in WATCHED_SUBSTRINGS):
        allow(str(payload.get("hook_event_name", "PreToolUse")))
        return

    session_id = str(payload.get("session_id", "unknown-session"))
    event_name = str(payload.get("hook_event_name", "PreToolUse"))

    if event_name == "PostToolUse":
        handle_post_tool_use(payload, tool_name, session_id)
    else:
        handle_pre_tool_use(payload, tool_name, session_id)


if __name__ == "__main__":
    main()

