# Examples

Generated ADR sets showing what the toolkit emits for representative stacks. These are
**generated, not hand-written** — regenerate them with [`../bin/gen-examples.sh`](../bin/gen-examples.sh),
and CI fails if they drift from the current packs.

| Example | Selected packs (universal is always included) | ADRs |
|---|---|---|
| [`orders-service`](orders-service/docs/adr/) | `kotlin spring-boot service observability` | 16 |
| [`recipes-web`](recipes-web/docs/adr/) | `react web-frontend d3 i18n` | 18 |
| [`feed-cli`](feed-cli/docs/adr/) | `python cli` | 11 |
| [`dashboard-web`](dashboard-web/docs/adr/) | `plain-js d3` | 13 |
| [`desktop-app`](desktop-app/docs/adr/) | `native-ui compose` | 14 |
| [`ledger-service`](ledger-service/docs/adr/) | `java spring-boot service observability privacy` | 17 |

Each shows the composition rules at work — e.g. `orders-service` auto-pulls the `jvm`
base under Kotlin and emits the `observability-in-spring-boot` interaction; `recipes-web`
pulls `js-ts` under React and the shared `accessibility` baseline under web-frontend, then
fires the `a11y-react`, `d3-with-react`, and `i18n-in-js-ts` interactions. `dashboard-web`
shows the no-framework path (`d3-with-plain-dom`); `desktop-app` pulls the shared
`accessibility` baseline under native UI and fires `accessibility-in-compose`; `ledger-service`
combines a Java Spring service with the opt-in `privacy` concern.
