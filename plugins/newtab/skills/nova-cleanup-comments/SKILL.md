---
name: nova-cleanup-comments
description: Add @nova-cleanup comments to Firefox newtab code to enable automated Claude-assisted cleanup after Nova ships. Use when adding cleanup comments to Nova-related changes.
---

# Add Nova Cleanup Comments

Add `@nova-cleanup` comments to Firefox newtab code following Project Nova implementation strategy.

## Context

Project Nova uses a parallel development approach where classic newtab stays untouched and Nova changes live in isolated directories/conditionals. Cleanup comments serve as instructions for a future automated pass: when Nova ships, Claude will find all `@nova-cleanup` markers and execute the described cleanup autonomously. Write descriptions as direct, unambiguous instructions that Claude can act on without engineer input.

## Comment Format

```
// @nova-cleanup(action): Instruction for Claude to execute during cleanup
```

## Actions

- `remove-directory` - Delete entire classic directory
- `move-directory` - Move Nova/ up one level
- `merge-styles` - Move styles from nova/ to component locations
- `remove-pref` - Remove pref check
- `remove-conditional` - Remove conditional logic

## Task

1. Read the specified file(s) or all modified files if none specified
2. Enter plan mode to identify Nova-related changes and propose the set of cleanup comments to add:
   - Pref checks for `nova.enabled` or similar
   - Conditionals based on Nova pref
   - Files in `Nova/` directory
   - Files in `styles/nova/` directory
   - Import statements choosing between classic/Nova components
3. After approval, add the cleanup comments:
   - For conditionals: `@nova-cleanup(remove-conditional)` with description
   - For pref checks: `@nova-cleanup(remove-pref)` with description
   - For Nova/ component files: `@nova-cleanup(move-directory)` at top of file
   - For classic component files that have Nova equivalent: `@nova-cleanup(remove-directory)` at top
   - For styles/nova/ files: `@nova-cleanup(merge-styles)` at top
4. Place comments immediately before the relevant code or at top of file for directory-level actions
5. Write descriptions as direct instructions Claude can execute without additional context or engineer guidance

## Examples

```javascript
// Logo.jsx - conditional rendering
const prefs = useSelector(state => state.Prefs.values);
// @nova-cleanup(remove-conditional): Delete novaEnabled and the wordmark div; always render the non-Nova branch
const novaEnabled = prefs[PREF_NOVA_ENABLED];
```

```javascript
// Entry point with component selection
// @nova-cleanup(remove-pref): Delete this line; replace Base with NovaBase everywhere in this file
const Base = prefs["browser.nova.enabled"] ? NovaBase : ClassicBase;
```

```javascript
// Nova/Base/Base.jsx
// @nova-cleanup(move-directory): Move this file to components/Base/Base.jsx and update all imports

export class Base extends React.Component {
  // ...
}
```

```scss
// styles/nova/_card.scss
// @nova-cleanup(merge-styles): Move contents into components/Card/_card.scss and delete this file

.card {
  // nova styles
}
```

## Notes

- Don't add cleanup comments to pure CSS changes or shared components without conditionals
- If uncertain whether a comment is needed, ask the user
- Multiple cleanup comments in the same file are fine if there are multiple Nova-related changes
- Descriptions must be self-contained — Claude should not need to infer intent or ask follow-up questions to execute them
