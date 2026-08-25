---
status: Accepted
date: "{{date}}"
topic: accessibility-in-swiftui
tags: [interaction, accessibility, swiftui]
supersedes: []
related: [accessibility-baseline, swiftui-conventions]
---
# {{number}}. Applying the accessibility baseline in SwiftUI

## Context

The accessibility baseline (WCAG 2.1 AA) is mandatory for this UI. SwiftUI is unusually
strong here by default: standard controls ship with labels, traits, and Dynamic Type
support, and VoiceOver reads a view tree the framework builds for you. That default is also
the trap — accessibility regressions arrive through custom drawing, decorative containers,
and fixed-size text, none of which announce themselves. This ADR records the SwiftUI
specifics.

## Decision

- **Standard controls before custom ones.** A `Button` or `Toggle` arrives with a label,
  a trait, and keyboard/switch support; a tappable `Rectangle` arrives with none of it.
- **Label custom and image content** with `accessibilityLabel`, plus `accessibilityValue`
  and `accessibilityHint` where the meaning is not in the label. Mark purely decorative
  imagery as such so it is skipped rather than announced.
- **Combine composite views** with `accessibilityElement(children: .combine)` so a card
  reads as one element instead of five fragments — and use `.ignore` with an explicit label
  where a container should speak for its children.
- **Dynamic Type is required**: text uses semantic font styles and layouts reflow at
  accessibility sizes. No fixed point sizes on body text, and no fixed-height containers
  around text that can grow.
- **Move VoiceOver focus deliberately** with `@AccessibilityFocusState` when a sheet opens
  or an error appears, rather than assuming the framework guesses correctly.
- **Respect the accessibility environment** — `reduceMotion`, `reduceTransparency`, and
  `differentiateWithoutColor`; never encode state in color alone.
- **Touch targets are at least 44×44 pt**, regardless of the visual size of the artwork.
- **Automated verification** in UI tests with `performAccessibilityAudit()`, which catches
  missing labels, clipped Dynamic Type, and undersized hit targets, run in CI.

## Alternatives considered

- **Relying on SwiftUI's defaults** — genuinely good for stock controls, which is what makes
  it persuasive, but defaults cover neither custom-drawn content nor the container structure
  that decides how a screen is chunked for VoiceOver.
- **Building interactive elements from shapes with `onTapGesture`** — total visual control,
  but it produces an element with no trait, no label, and no assistive-technology
  affordances, all of which then have to be reimplemented by hand.
- **`accessibilityElement(children: .ignore)` as the default for containers** — quietens
  noisy output quickly, but it silently drops content when a container gains children later,
  which is why `.combine` is the default here and `.ignore` requires an explicit label.
- **Manual VoiceOver spot-checks instead of an automated audit** — catches nuance a machine
  cannot, and is still worth doing, but it is not repeatable per pull request, so
  regressions land between checks.

## Consequences

- Accessibility is preserved where SwiftUI's defaults do not reach: custom controls,
  composite views, and text that must scale.
- The audit catches a real class of regression in CI, though it checks mechanics rather than
  whether the announced text makes sense, so VoiceOver spot-checks remain valuable.
- Dynamic Type support constrains layout: designs with fixed-height text containers need
  rework, which is cheaper before the design is built than after.
