## ADDED Requirements

### Requirement: The builder's own budget

When `HABITAT_BUILDER_BUDGET_USD` is set, dispatch SHALL run the builder role
with that budget and every other role with `HABITAT_MAX_BUDGET_USD`.

#### Scenario: A builder gets more room than the reviewers

- **WHEN** a chain is dispatched with `HABITAT_BUILDER_BUDGET_USD=10` and `HABITAT_MAX_BUDGET_USD=5`
- **THEN** the builder's `--max-budget-usd` is 10 and the other roles' is 5
