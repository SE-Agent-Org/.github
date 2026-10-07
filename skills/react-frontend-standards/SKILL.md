---
name: react-frontend-standards
description: Build, edit, and test React frontend components — including writing new components, modifying existing ones, and creating Jest + React Testing Library unit tests for them. Use whenever asked to create or update a React component, page, hook, or UI element (in .tsx/.jsx files), asked for unit tests or test coverage for React code, or asked to make frontend work "match the existing style/theme/design system." CRITICAL: Jest + React Testing Library is this project's frontend unit test framework — install and configure it if missing rather than substituting a different runner.
---

# React Frontend Development

This skill covers two tightly linked jobs: writing React components (or editing existing ones) so they fit naturally into an existing codebase, and writing unit tests for them with Jest + React Testing Library.

The core idea behind both halves of this skill is the same: **never invent conventions that the codebase has already decided for you.** A component that reinvents its own spacing scale, or a test suite that reinvents its own render helper, immediately looks foreign next to everything around it — even if each one works fine in isolation. Most of the value you add here comes from noticing what's already there and reusing it, not from writing more code.

## Workflow overview

1. **Survey the codebase before writing anything.** (see "Discovering conventions" below)
2. **Write or edit the component**, reusing existing design tokens, primitives, and patterns.
3. **Write the unit tests**, matching the existing test suite's structure and helpers.
4. **Run the tests** (and lint/typecheck if configured) before considering the work done.

Don't skip step 1 even if the request seems simple. A five-line component that hardcodes a hex color or a pixel value when the project has a theme system is a bug, not a shortcut.

---

## Part 1: Discovering conventions

Before writing or editing a component, spend a couple of minutes actually looking around. This isn't optional busywork — it's what separates a component that looks like it belongs from one that looks bolted on.

### Find the theme/design system

**There is no default styling method for this skill.** Tailwind, CSS-in-JS, CSS Modules, a component library, plain CSS — none of these is preferred over another in the abstract. The only rule is: whatever the project is already using wins, every time. Treat this discovery step as mandatory, not something to skip because a request seems simple or because one method feels like the "normal" choice — the goal is code that's indistinguishable from something a teammate already familiar with this specific codebase would have written.

Check for each of the following — a project may use more than one:

- **Tailwind**: `tailwind.config.{js,ts}` — check `theme.extend` for custom colors, spacing, fonts, breakpoints. If present, use Tailwind utility classes drawn from these tokens, not raw hex/px values.
- **CSS-in-JS (styled-components, Emotion, vanilla-extract, stitches)**: look for a `theme.ts`/`theme.js` file, a `ThemeProvider` in the app root, or a `styled.ts` alongside components. Check how existing components consume the theme (`props.theme.colors.primary`, a `useTheme()` hook, etc.) and follow the same access pattern.
- **CSS Modules / Sass**: look for `*.module.css` or `*.module.scss` files next to components, plus a shared `variables.scss`, `tokens.css`, or `:root` custom-properties block. Reuse those variables instead of hardcoding values.
- **Plain CSS / global stylesheets**: a single `styles.css`/`App.css` with class names referenced directly — just as valid a convention as any of the above if that's what's already there.
- **Component libraries** (MUI, Chakra, Ant Design, shadcn/ui, Radix + custom wrappers): check `package.json` for these, and look for a local wrapper layer (often `src/components/ui/`) — new components should typically compose from these primitives rather than building raw HTML elements from scratch.
- **Design tokens as plain JSON/JS** (`tokens.json`, `theme/colors.ts`, etc.), sometimes generated from Figma — if these exist, they're the source of truth over anything inline, regardless of which of the above consumes them.
- **Inline styles**: rare as a deliberate convention, but if that's genuinely what the surrounding components do, matching it is more valuable than "upgrading" them to something more conventional without being asked.

If you're editing an existing component, the fastest way to find the convention is to look at 2-3 sibling components in the same directory — they'll show you the actual pattern in use far more reliably than a config file alone. Config files show what's *possible*; sibling files show what's *idiomatic here*.

If genuinely nothing exists (a greenfield project with no theme file, no config, no sibling components), it's fine to use plain, sensible CSS/inline styles — just don't fabricate a "design system" the project doesn't have.

### Find structural conventions

While you're looking around, also note:

- **File/folder layout**: one file per component vs. a folder per component (`Button/index.tsx` + `Button/Button.module.css` + `Button/Button.test.tsx`)
- **Naming**: `PascalCase.tsx` for components, and whether hooks live in a `hooks/` folder as `useXyz.ts`
- **Props typing style**: `interface Props` vs `type Props =`, and whether props are destructured inline or via a named type
- **Export style**: default export vs. named export (this affects how you import it in the test file — check this specifically, it's a common source of import errors)
- **State/data patterns**: local `useState`, a global store (Redux/Zustand/Jotai/Context), or server state (React Query/SWR) — match whatever the surrounding code already uses rather than introducing a new pattern for one component

### Quick-reference discovery checklist

Skim this on an unfamiliar codebase instead of re-reading the two sections above in full.

**Styling system — no default, always detect.** None of the methods below is the "normal" or preferred one — a project may even mix a couple. Whichever is actually in use wins; don't substitute a different approach out of habit.

- [ ] `tailwind.config.{js,ts}` exists? → Tailwind project. Check `theme.extend` for custom colors/spacing/fonts.
- [ ] `package.json` has `styled-components`, `@emotion/*`, `@vanilla-extract/css`, or `@stitches/react`? → CSS-in-JS. Find the `theme.ts`/`ThemeProvider`.
- [ ] `*.module.css` / `*.module.scss` files next to components? → CSS Modules. Find shared `variables.scss` / `tokens.css` / `:root` vars.
- [ ] `package.json` has `@mui/material`, `@chakra-ui/react`, `antd`, or `shadcn`-style `components/ui/`? → Component library. Look for a local wrapper layer first.
- [ ] A `tokens.json` / `theme/colors.ts` / similar plain-data file? → Treat as source of truth over any inline values.
- [ ] None of the above? → Plain CSS/inline styles are fine. Don't invent a design system that isn't there.

**Structural conventions — check 2-3 sibling files.**

- [ ] One-file-per-component, or a folder per component with colocated styles/tests?
- [ ] Component file naming: `PascalCase.tsx`?
- [ ] Props: `interface Props` or `type Props = {...}`?
- [ ] Export style: `export default function X()` or `export function X()`? (Check this before writing the test's import line.)
- [ ] State management already in use nearby: local `useState`, Context, Redux/Zustand/Jotai, or server-state (React Query/SWR)?

**Test infrastructure — check before writing tests.**

- [ ] A custom render wrapper (`test-utils.tsx`, `src/test/utils.tsx`) that supplies providers (theme/router/store)? Use it instead of raw `render` from `@testing-library/react`.
- [ ] `jest.config.js` / `setupTests.ts` — what's globally available already (e.g. jest-dom matchers)?
- [ ] One existing `*.test.tsx` file for describe/it naming style and mocking patterns (`jest.mock(...)`).
- [ ] Jest vs Vitest? (Check `package.json` scripts/devDependencies — swap `jest.fn`→`vi.fn` etc. if Vitest.)

---

## Part 2: Writing the component

With conventions in hand, write the styling in whatever method Part 1 turned up — don't substitute a different method you might personally prefer or reach for by habit:

- Reuse existing primitives/tokens rather than duplicating their values. If the theme defines `spacing.md = 16px`, use the token, not `16px` or `1rem` written literally.
- Match accessibility patterns already present in the codebase (e.g., if buttons elsewhere use `aria-label` for icon-only variants, do the same here).
- Keep new components colocated the way existing ones are (same folder structure, same file naming).
- Prefer composing existing shared components (a `Button`, `Card`, `Input` the project already has) over writing raw markup that duplicates them.
- If the request is a modification to an existing component, make the smallest change that accomplishes the goal — don't restyle or restructure parts the user didn't ask about.

When a genuinely new visual pattern is needed (nothing existing covers it), it's fine to introduce it — just base its values (colors, spacing, radii, shadows) on the existing token scale so it still feels consistent, rather than picking arbitrary new numbers.

---

## Part 3: Writing unit tests

**CRITICAL — Jest is this project's frontend unit test framework. This is not a default to override or a preference to weigh against alternatives — treat it as a hard requirement:** every React unit test file is written for **Jest + React Testing Library (RTL)**, with `@testing-library/user-event` for interactions. If Jest is not yet installed or configured in the frontend project, install and configure it rather than reaching for a different runner (e.g. Vitest) because it seemed more convenient or was already present for some other purpose — do not silently substitute frameworks. The only exception is an existing `*.test.tsx` suite already written and passing under Vitest — match that existing suite's runner rather than introducing a second one, and flag the mismatch rather than treating it as normal; for a new project or one with no existing frontend tests, Jest is the answer, full stop. Where Vitest genuinely is the existing runner, RTL's APIs are nearly identical — swap `jest.fn()` → `vi.fn()` and the `jest` global → `vi`, everything else below still applies.

### Test Location (HARD RULE)

**Every test file MUST be colocated with the source file it tests — never a separate top-level `tests/` directory mirroring `src/`.** Colocation is Jest's own default discovery convention and the most recognized pattern in the React ecosystem, and it takes exactly two forms:

- **A sibling file** named `{Component}.test.tsx` (or `.spec.tsx`) directly next to `{Component}.tsx` in the same folder — Jest's plain default (`testMatch` unset), and the more common of the two across the ecosystem generally.
- **A `__tests__/` folder** colocated inside the same directory as the source (e.g. `components/Button/__tests__/Button.test.tsx` next to `components/Button/Button.tsx`).

**This project has already settled on the `__tests__/` folder form, and it's enforced, not just a preference:** `frontend/jest.config.js` sets `testMatch: ['**/__tests__/**/*.test.(ts|tsx)']`, which narrows discovery to *only* files inside a colocated `__tests__/` folder. A bare sibling `Component.test.tsx` file placed directly next to the component — Jest's own plain default — would **not** be discovered by this project's configured test run; it would silently never execute. Always write new tests as `{feature-or-component-dir}/__tests__/{Component}.test.tsx`, matching the existing pattern already in the codebase (e.g. `src/features/welfare-events/components/__tests__/`) — never as a bare sibling file here, and never anywhere Jest's configured `testMatch` wouldn't discover it.

### Guiding principle

Test the component the way a user would use it, not the way it's implemented. RTL is built around this: query by role/label/text (what a user sees), not by CSS class or internal state (implementation detail). Tests written against implementation details break every time you refactor, even when behavior hasn't changed — that's the failure mode to avoid.

### Before writing tests, check for existing test infrastructure

- Is there a custom render function (often `test-utils.tsx` or `src/test/utils.tsx`) that wraps `render()` with providers (theme, router, redux store, query client)? **Use it instead of RTL's raw `render`** — importing the plain `render` from `@testing-library/react` directly when a custom wrapper exists is one of the most common ways generated tests fail immediately (missing context/provider errors).
- What Jest config/setup file is referenced (`jest.config.js`, `setupTests.ts`)? It tells you what's already globally available (e.g., `jest-dom` matchers like `.toBeInTheDocument()` are usually pre-loaded — don't re-import them if so).
- Look at one existing `*.test.tsx` file in the project for describe/it structure, naming conventions, and how mocks are typically set up (`jest.mock(...)` patterns for API calls, router, etc.).

### What to cover

For a typical component, aim to cover:

1. **Renders without crashing**, with default/minimal required props.
2. **Renders the right content** for given props (text, labels, conditional branches — e.g., an empty state vs. populated state).
3. **User interactions** — clicks, typing, selecting — using `userEvent`, asserting the resulting state/callback/DOM change, not just that a handler "was called" if there's observable behavior to check instead.
4. **Conditional rendering / edge cases** — loading state, error state, empty list, disabled state — whatever branches exist in the component.
5. **Accessibility basics** where relevant — the right role is exposed, form inputs are associated with labels — RTL's query methods (`getByRole`, `getByLabelText`) naturally enforce this since they fail if the element isn't accessible.

Don't test things React itself guarantees (e.g., "prop gets passed to child") or pure implementation details (internal state variable names, whether a particular helper function was called) — those tests are brittle and don't tell you anything a refactor should care about.

### Query priority

Use this order (matches RTL's own recommended priority — the higher an item, the more it reflects how an actual user/assistive tech finds the element):

1. `getByRole` (with `{ name: ... }` for the accessible name) — for almost everything interactive
2. `getByLabelText` — for form fields
3. `getByText` — for non-interactive content
4. `getByTestId` — last resort, only when there's genuinely no accessible way to select the element (e.g., a decorative element with no text/role)

Reaching for `getByTestId` first is the most common way generated tests drift from RTL's philosophy — it makes tests pass without confirming the UI is actually usable/accessible.

### Example structure

```tsx
import { render, screen } from '@testing-library/react'; // or the project's custom render — check first
import userEvent from '@testing-library/user-event';
import { Counter } from './Counter';

describe('Counter', () => {
  it('renders with an initial count of 0', () => {
    render(<Counter />);
    expect(screen.getByText('Count: 0')).toBeInTheDocument();
  });

  it('increments the count when the increment button is clicked', async () => {
    const user = userEvent.setup();
    render(<Counter />);

    await user.click(screen.getByRole('button', { name: /increment/i }));

    expect(screen.getByText('Count: 1')).toBeInTheDocument();
  });

  it('calls onCountChange with the new value', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(<Counter onCountChange={handleChange} />);

    await user.click(screen.getByRole('button', { name: /increment/i }));

    expect(handleChange).toHaveBeenCalledWith(1);
  });
});
```

### Advanced testing patterns

Pull these in for anything beyond a straightforward presentational component.

**Mocking modules and API calls.** Mock at the boundary the component actually talks to. If a component calls a `fetchUser` function from an API module, mock that module — don't mock `fetch`/`axios` globally unless the codebase already does it that way elsewhere.

```tsx
jest.mock('../api/users', () => ({
  fetchUser: jest.fn(),
}));

import { fetchUser } from '../api/users';

it('shows the user name once loaded', async () => {
  (fetchUser as jest.Mock).mockResolvedValue({ name: 'Ada Lovelace' });

  render(<UserProfile userId="1" />);

  expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument();
});
```

Use `findBy*` queries (async, retrying) for content that appears after a promise resolves — not `getBy*` wrapped in `waitFor` as a first resort, though `waitFor` is the right tool for asserting something *disappears* or for multi-step async flows.

**Testing components that fetch data.** If the project uses React Query/SWR, wrap the render in the relevant provider with a fresh client per test, and prefer mocking the query function itself over mocking the library's internals:

```tsx
const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function renderWithClient(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}
```

If a custom `test-utils.tsx` render already does this, use that instead of rebuilding it per test file.

**Testing custom hooks.** Use `renderHook` from `@testing-library/react` directly rather than building a throwaway component to exercise the hook:

```tsx
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

it('increments the count', () => {
  const { result } = renderHook(() => useCounter());

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

**Testing components wrapped in context/providers.** If a component reads from a Context (theme, auth, feature flags), tests need that provider in the tree — either via the project's custom render wrapper, or a local one for tests specific to that context:

```tsx
function renderWithTheme(ui: React.ReactElement, theme = defaultTheme) {
  return render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>);
}
```

Prefer testing behavior that changes with context value (e.g., a dark-mode toggle actually changing what's rendered) over just asserting the provider was called.

**Snapshot testing — when it helps and when it doesn't.** Snapshots are good for catching *unintended* markup changes in something stable and structurally simple (e.g., an icon library wrapper). They're a poor fit for most components because:
- Large snapshots get rubber-stamped ("update snapshot") without being read, defeating the point.
- They don't express *intent* — a failing assertion like `expect(screen.getByRole('alert')).toHaveTextContent('Required')` documents what should be true; a failing snapshot just shows a diff.

Default to explicit RTL assertions. Only reach for a snapshot when the component is genuinely about stable markup output and the team's existing tests already use snapshots that way.

**Common failure modes and fixes:**

| Symptom | Likely cause | Fix |
|---|---|---|
| `Unable to find role "..."` | Element isn't accessible the way you assumed (missing `aria-label`, wrong role) | Check rendered output with `screen.debug()`; fix the component's accessibility, don't just switch to `getByTestId` |
| "could not find react-redux context" / similar provider errors | Used raw `render` instead of the project's custom wrapper | Import the project's `test-utils` render function instead of `@testing-library/react`'s |
| Test passes locally but is flaky in CI for async UI | Used `getBy*` for content that appears after a delay | Switch to `findBy*` or wrap in `waitFor` |
| `act(...)` warnings | State update happening outside of an awaited user-event/act block | Ensure `await user.click(...)` etc. are awaited; wrap manual state-triggering calls in `act()` |
| Import error on the component in the test file | Guessed default vs. named export | Check the component file's actual export statement before writing the import |

---

## Part 4: Verify before finishing

If a test runner is configured (check `package.json` scripts for `test`), run it for the file(s) you touched, e.g. `npm test -- Counter.test.tsx` or `yarn test Counter.test.tsx`. Fix failures rather than leaving them for the user to discover. If lint/typecheck scripts exist (`npm run lint`, `npm run typecheck`), it's worth running those too for anything more than a trivial change — TypeScript will often catch a prop-typing mismatch immediately that would otherwise surface later.

If no test runner is reachable in the current environment, say so plainly rather than claiming the tests pass.

### Ensuring Jest is installed (CRITICAL — a missing install is never a reason to skip frontend tests)

If Jest isn't yet installed or configured for this frontend, install and configure it rather than skipping, deferring, or substituting a different runner:

1. Check `package.json` `devDependencies` for `jest` (and, for a TypeScript project, `ts-jest` or `@babel/preset-typescript`/`babel-jest`), plus `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, and `jest-environment-jsdom`.
2. If any are missing, install them as dev dependencies using this project's existing package manager (npm/yarn/pnpm, per its lockfile): `jest jest-environment-jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event ts-jest @types/jest` (drop `ts-jest`/`@types/jest` for a plain-JS project).
3. If no `jest.config.{js,ts,cjs}` (or a `"jest"` key in `package.json`) exists, create a minimal one: `testEnvironment: "jsdom"`, a setup file wiring `@testing-library/jest-dom` (referenced via `setupFilesAfterEnv`), and a transform matching the project's TS/JS setup.
4. If `package.json` has no `test` script, add one (`"test": "jest"`) so it's discoverable the same way in future runs and CI.
5. Verify with `npx jest --version` before relying on it — if that fails, treat it as a real blocker to escalate, not something to silently work around by skipping tests.

### Running the full suite

`npx jest --colors` (or `npm test`, if `package.json` wires it to Jest) runs every test; pass a path to scope it to one file, e.g. `npx jest Counter.test.tsx`.
