# voice-note Known Issues

## Open Issue: Tab Navigation Is Unstable

Status: open

### Description

Tab navigation in the TUI is not behaving reliably. Pressing `l`, `h`, or the
left/right arrow keys can jump to unexpected tabs instead of cycling cleanly
through:

- `Notes`
- `Session`
- `Help`
- `Settings`
- back to `Notes`

### Expected Behavior

- `l` and `right` should move forward one tab.
- `h` and `left` should move backward one tab.
- Tab navigation should wrap around at the ends.
- Each key press should trigger exactly one tab change.

### Observed Behavior

- The tab selection can jump or appear to skip.
- The runtime behavior does not always match the intended wrap-around cycle.
- The problem appears to involve live Textual event handling rather than the
  binding table alone.

### Current Investigation Notes

- Tab order is defined in `voice_note/tui/app.py`.
- Tab movement currently routes through `on_key()` and `_cycle_tab()`.
- The issue likely involves interaction between app-level key handling and
  `TabbedContent` or widget focus.
- The binding table and unit tests are not sufficient to prove the runtime path
  is stable.

### Next Steps

1. Reproduce the issue in a live TUI session.
2. Confirm which widget has focus when the key is pressed.
3. Verify whether `TabbedContent` is handling the same keys internally.
4. Simplify tab switching if necessary so there is a single source of truth for
   tab state changes.

FIXED
