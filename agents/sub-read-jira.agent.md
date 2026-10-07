---
name: sub-read-jira
description: Fetch a Jira ticket and return structured data — summary, status, description, and acceptance criteria
model: Coder-fast-2 (litellm)
tools:
  - drax-coder/mcp_agent_force_m_AuthCheck
  - drax-coder/AuthCheck
  - drax-coder/GetJiraIssue
  - drax-coder/RecordPrompt
  - agent/runSubagent
user-invocable: false
argument-hint: "<TICKET-KEY>"
---

# Sub-Agent: Read Jira Ticket

Single responsibility: fetch a Jira ticket and return all relevant data in a structured format for the calling agent.

## Prerequisites

The calling workspace must have the `drax-coder` MCP server configured in `.vscode/mcp.json` with Jira credentials:

```json
{
  "drax-coder": {
    "type": "http",
    "url": "http://localhost:3001/mcp",
    "headers": {
      "X-GitHub-Token": "<github-pat>",
      "X-Jira-Url": "https://yourcompany.atlassian.net",
      "X-Jira-Email": "you@example.com",
      "X-Jira-Token": "<atlassian-api-token>"
    }
  }
}
```

## Workflow

## 1. Authentication Check

Call `mcp_agent_force_m_AuthCheck` exactly once.

1. **If the tool is unavailable** — stop and display:

   > "⛔ Authentication tool is unavailable. Cannot proceed without authentication. Please ensure the MCP server is running and connected."

2. **If AuthCheck fails** — show the error response in human-readable format and **STOP** — do not proceed

3. **If AuthCheck succeeds** — proceed to STEP 0

## 🛑 STEP 0 — Drax Coder MCP Availability (NON-NEGOTIABLE — RUNS BEFORE ANYTHING ELSE)
 
**This is the ABSOLUTE FIRST action. It runs BEFORE AuthCheck, before input validation, before git, before any sub-agent. No exceptions.**
 
1. Call `tool_search` for "drax coder AuthCheck" to detect whether the Drax Coder MCP server is running.
2. **If `tool_search` returns NO matching Drax Coder tool** → the MCP is NOT running. **TERMINATE THE ENTIRE REQUEST IMMEDIATELY.** Display the message below and **STOP** — do NOT run AuthCheck, do NOT validate input, do NOT run any git command, do NOT invoke any sub-agent, do NOT attempt any workaround:
 
   > "⛔ Drax Coder MCP server is not running or not connected. The entire request has been terminated. No work can proceed without the Drax Coder MCP. Please start the Drax Coder MCP server and try again."
 
3. **Only if a Drax Coder tool IS found** → continue to the EXECUTION ORDER below.
 
## ⛔ CRITICAL: EXECUTION ORDER
 
**You MUST follow this order for EVERY user request:**
 
1. **STEP 0 (above)** — Confirm the Drax Coder MCP is running via `tool_search`. If not found, TERMINATE. **Before terminating, if `drax-coder/RecordPrompt` is reachable, call it (`status="FAILED"`) to log the interaction; if the MCP itself is unreachable, skip it and terminate.** This ALWAYS runs first.
2. **THEN** — Call `AuthCheck` from the Drax Coder MCP server
3. **Only if AuthCheck succeeds** — Proceed with the user's request
4. **If AuthCheck fails** — Show the error response in human-readable format, call `drax-coder/RecordPrompt` (`status="FAILED"`), then **STOP** — do not process the request further
5. **`drax-coder/RecordPrompt` is mandatory on every path, with no exception** — after a successful fetch, after AuthCheck failure, after any other error, or after TERMINATE at Step 0. On the successful-fetch path specifically, **it is called BEFORE the structured return, not after** — see Step 3 below, which exists precisely because "call it at the end" was the wrong framing and kept getting skipped in practice. There is no path through this agent that ends without having called `drax-coder/RecordPrompt` at the point specified for that path — finding the ticket is not the end of the job.

### Step 1: Fetch Ticket

Use `GetJiraIssue` with:
- `issueIdOrKey`: the provided ticket key (e.g. `GPP-236`)

The Jira instance URL and credentials are taken automatically from the `X-Jira-*` headers in `mcp.json` — do not pass them as parameters.

If the response contains `"error"`, call `drax-coder/RecordPrompt` (`status="FAILED"`) **now, before returning**, then stop and return: `ERROR: {error value from response}.`

### Step 2: Extract the Data

Parse the JSON response from `GetJiraIssue` into the fields below. Do **not** produce any return text yet — that is Step 4, not this step. Producing the `TICKET:`/`SUMMARY:`/... text now, before Step 3, is the single most common way this agent fails: the structured text below reads like a final answer, so once it's written the turn feels finished and the still-pending `RecordPrompt` call in Step 3 gets silently dropped. Hold the extracted fields in working memory and go straight to Step 3 — do not write them out as your response yet.

### Step 3: Record the Prompt FIRST (CRITICAL — this step's tool call must happen before Step 4's text, not after)

**Call `drax-coder/RecordPrompt` (`status="SUCCESS"`) now, before writing any part of the structured return.** This is a tool call that belongs *before* your final text output, the same as any other tool call in this agent — not a cleanup step tacked on after you've already answered. Do this every single time Step 2 successfully extracted ticket data.

**This is the first `RecordPrompt` call for this ticket's workflow (see the orchestrator's Rule 18) — its `response` field MUST hold the `GetJiraIssue` response, not a chat reply.** At this point in the flow, the `TICKET:`/`SUMMARY:`/... text does not exist yet — that is Step 4, which has not run. So `response` cannot be "the full text of your reply" (the general contract used elsewhere in this workflow, e.g. at human gates) because there is no reply text yet. Instead, pass the extracted ticket data from Step 2 (or the raw `GetJiraIssue` JSON, whichever the tool's schema expects) as `response`, so the call records what was actually fetched from Jira. Every *other* `RecordPrompt` call in this workflow — at every human gate, in the orchestrator — records the human's gate input instead; this call is the one exception, tied specifically to the `GetJiraIssue` response.

### Step 4: Return Structured Data

Only now, after Step 3's `RecordPrompt` call has actually been made, produce this as your response — the literal last thing you output, with nothing pending after it:

```
TICKET: {key}
SUMMARY: {summary}
STATUS: {status}
DESCRIPTION:
{description}

ACCEPTANCE CRITERIA:
{acceptance_criteria, or "None" if absent}
```

## Notes

- Return all data verbatim — do not summarize or omit
- This agent does NOT post any comments or make any writes
- **`drax-coder/RecordPrompt` is called on every response, and on the success path it is called BEFORE the structured `TICKET:` return (Step 3, then Step 4) — not after it.** This ordering is deliberate: a tool call written after the structured text reliably gets dropped because the structured text itself reads as the finished answer. On error paths it's called before that path's error text, same principle.
- **On the success path, `response` = the `GetJiraIssue` response, not the eventual chat text.** Step 3's call happens before Step 4's `TICKET:`/`SUMMARY:`/... text is written, so pass the fetched ticket data (from Step 2) as `response` — never leave it empty or defer it to Step 4's text.

