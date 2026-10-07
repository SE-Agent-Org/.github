---
name: laravel-react-integration
description: How the Laravel API backend and the React SPA frontend integrate — request/response contract, auth handshake, CORS, addressing, and verification steps for any ticket that touches both sides
---

# Laravel ⇄ React Integration

Authoritative reference for how the backend (`laravel-backend-standards`) and frontend (`react-frontend-standards`) fit together. Read this **only when a ticket's `PLAN` touches both sides** — a single-side ticket has nothing to integrate. This skill does not replace either side's own coding-standards skill; it covers the seam between them.

## Contract: What the Backend Returns, What the Frontend Expects

- The backend's public contract is whatever its `Http\Resources\*Resource` classes serialize (see `laravel-backend-standards`) — never the raw Eloquent model or database schema. The frontend must be written against the Resource's actual `toArray()` output, field-for-field.
- When a ticket adds or changes a Resource's shape, the frontend's corresponding type/interface (or PropTypes) and any mock/fixture data (e.g. MSW handlers, test fixtures) must be updated to match — a stale frontend type that silently diverges from the real Resource shape is the most common integration bug.
- Collection endpoints follow Laravel's default Resource wrapping: `{"data": [...], "meta": {...}, "links": {...}}` for paginated lists, `{"data": {...}}` for a single resource. The frontend's API layer (`src/api/*`) unwraps this envelope in one place — do not have every caller unwrap `.data` independently.

## Errors: Shape Parity

- Validation failures return HTTP 422 with `{"message": "...", "errors": {"field": ["message", ...]}}`. The frontend's API layer normalizes this into whatever error shape its components consume (see `react-frontend-standards`) — field-level errors from `errors` must reach the form, not just the top-level `message`.
- Other failures return `{"message": "..."}` with the appropriate status code (401/403/404/5xx). The frontend must not assume every error response has an `errors` object.

## Auth Handshake

- First-party SPA auth uses **Laravel Sanctum** in its cookie/session mode: the frontend must fetch the CSRF cookie (`GET /sanctum/csrf-cookie`) before the first authenticated request (login, or any state-changing call), and send credentials (cookies) with every request (`withCredentials`/`credentials: 'include'` in the API client).
- `config/cors.php` must explicitly list the frontend's origin(s) (dev and deployed), and `SANCTUM_STATEFUL_DOMAINS` must include the frontend's host(s) — a ticket that changes either origin (e.g. adding a new deployment URL) must update both.
- If this project instead uses token auth (no cookies), the frontend attaches the token as a bearer header in its API client's shared instance, not per-call.

## Addressing

- The frontend's API base URL is an environment variable (`VITE_API_BASE_URL` or equivalent — see `react-frontend-standards`), never hardcoded, and points at the backend's versioned prefix (e.g. `https://api.example.com/api/v1`).
- Route/endpoint paths on the backend are versioned under `routes/api.php`'s `v1` prefix (see `laravel-backend-standards`). A ticket that adds a `v2`-only endpoint must not silently break `v1` frontend callers.

## Implementation Order for a Cross-Side Ticket

1. Implement and verify the backend side first — the Resource shape, route, and validation rules are the contract. Confirm (via `php artisan route:list`, a manual request, or the Resource's `toArray()`) what it actually returns before writing the frontend against it.
2. Implement the frontend side against that real, verified shape — not against the shape assumed in `PLAN` when it was drafted, if the two differ.
3. If the backend Resource changed shape mid-ticket (e.g. during review feedback), re-verify the frontend side against the new shape before considering the ticket done.

## Verification Checklist (before returning `INTEGRATION NOTES`)

- [ ] Every field the frontend reads from a response exists, under the same name and type, in the backend Resource's actual output
- [ ] Every field the frontend sends in a request body matches what the backend's Form Request validates/accepts
- [ ] The frontend's error handling covers both the 422 validation shape and the generic error shape
- [ ] The API base URL/version prefix used by the frontend matches where the backend route is actually registered
- [ ] CORS/Sanctum config includes the frontend origin(s) this ticket's environment(s) actually use, if either changed
