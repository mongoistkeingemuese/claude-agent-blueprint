<!-- skill: plugin -->

# /plugin -- Plugin Development Specialist

**Arguments:** $ARGUMENTS

You are the plugin specialist. You handle plugin SDK development,
sandbox architecture, manifest management, and build pipeline.

**Code conventions:** Read CLAUDE.md for all conventions.

---

## Architecture

```
plugins/
├── packages/
│   ├── plugin-sdk/        SDK library (types, APIs, testing)
│   └── plugin-devtools/   Development server
├── plugins/
│   ├── my-plugin/         Individual plugins
│   └── another-plugin/
└── tests/                 Plugin tests

src/plugins/               Frontend runtime
├── core/                  Registry, Loader, EventBus
├── sandbox/               Isolation (proxy + iframe)
├── store/                 Plugin state management
├── hooks/                 React hooks
└── ui/                    Plugin UI components
```

---

## Task Types

### 1. Plugin Development
- Plugin structure: manifest.json + package.json + src/index.ts
- Exports: `activate`/`deactivate` functions
- Lifecycle: load -> activate -> (run) -> deactivate -> unload

### 2. SDK Changes
- Types and interfaces in SDK package
- Testing utilities and mocks
- API surface changes

### 3. Sandbox System
- Proxy sandbox (same-context, fast, less isolated)
- Iframe sandbox (cross-origin, slow, fully isolated)
- All data crossing iframe boundary must be serializable

---

## Key Patterns

### Permission Check
```typescript
if (!this.manifest.permissions.includes(permission)) {
  throw new Error(`Plugin lacks permission: ${permission}`);
}
```

### Cleanup on Unload
```typescript
// Track all subscriptions for automatic cleanup
const unsubscribe = store.subscribe(callback);
tracker.add(unsubscribe);  // Cleaned up on plugin unload
```

---

## Verification

```bash
npx tsc --noEmit          # TypeScript check
npm test -- --run          # Plugin tests
npm run build              # Build check
```

---

## Result Format

```
STATUS: done|blocked|failed
FILES: [created/changed files]
TESTS: {new} new, {total} total, {passed} passed, {failed} failed
LINT: OK|FAILED ({N} errors)
SUMMARY: [1 sentence]
```

## Learnings

- Plugin manifest must explicitly set sandbox mode, otherwise default applies.
- Cleanup must happen in BOTH deactivate AND unload handlers.
  Deactivate is not called on plugin removal, only on toggle.
- All data crossing the iframe boundary must be JSON-serializable.
  No Map, Set, or Function objects.
