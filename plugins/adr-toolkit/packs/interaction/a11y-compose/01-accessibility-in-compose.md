---
status: Accepted
date: "{{date}}"
topic: accessibility-in-compose
tags: [interaction, accessibility, compose]
supersedes: []
related: [accessibility-baseline, compose-conventions]
---
# {{number}}. Applying the accessibility baseline in Compose

## Context

The accessibility baseline (WCAG 2.1 AA) is mandatory for this UI. Compose builds its
accessibility tree from a **semantics** layer rather than platform view hierarchies, so the
mechanics differ from both the web and classic Android views. This ADR records the
Compose-specific approach.

## Decision

- **Semantics on every meaningful node** — set `contentDescription` for images/icons, use
  `Modifier.semantics { }` for custom components, and `role` to convey the element's type to
  the screen reader (TalkBack / VoiceOver on Multiplatform targets).
- **Focus and traversal order** — ensure logical traversal, group related content with
  `mergeDescendants`, and manage focus for dialogs and navigation.
- **Touch targets** meet minimum size (≥ 48dp) regardless of visual size.
- **State to assistive tech** — communicate selection, toggle, and progress state via
  semantics (`stateDescription`, `toggleableState`), not color alone.
- **Testing** — assert accessibility with `compose-test` semantics matchers
  (`assertContentDescriptionEquals`, role/state assertions) and use `testTag` for stable
  test hooks; run these in CI.

## Alternatives considered

- **Wrap composables in classic View-based `AccessibilityDelegate` APIs** — rejected because
  it bypasses Compose's own semantics tree, which is what TalkBack and Compose UI tests
  actually read.
- **Set `contentDescription` per leaf node without `mergeDescendants` grouping** — rejected
  because it produces fragmented, noisy announcements instead of one coherent element.
- **Manual/exploratory TalkBack testing only, skipping `compose-test` semantics matchers** —
  rejected because it gives no CI enforcement, so accessibility regressions ship silently.

## Consequences

- The accessibility baseline is met within Compose's semantics model, including custom
  components that would otherwise be opaque to screen readers.
- Accessibility is asserted in Compose UI tests, catching regressions in CI.
- Developers annotate semantics and manage focus explicitly — work Compose does not infer
  automatically for custom UI.
