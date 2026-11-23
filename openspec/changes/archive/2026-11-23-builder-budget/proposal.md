# The builder may get its own budget

## Why

2026-10-24, convergence: three builds failed on `error_max_budget_usd` at
the builder (demo-core once, gdd-economy twice), at 127 to 138 turns and the
shared $5 per role, while no architect, reviewer or security run cost more
than $1.03. One budget for four roles starves the one that does the work.

## What changes

`dispatch.sh` uses `HABITAT_BUILDER_BUDGET_USD` for the builder role when it
is set; the other roles keep `HABITAT_MAX_BUDGET_USD`. Unset, nothing changes.
