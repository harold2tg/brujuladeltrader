# Proposal: Alerts Module

## Intent

Trigger rule-based alerts when trade metrics cross user-defined thresholds. Without this, users must manually check analytics after every upload — low retention.

## Scope

### In Scope
- 5 rule types: max_loss_per_trade, loss_streak, daily_loss_limit, win_rate_drop, rr_below
- Rule CRUD (GET/POST/PUT/DELETE /alerts/rules)
- Paginated alert history (GET /alerts/history)
- Redis hourly dedup: same rule fires ≤1x/hour/user
- Plan enforcement: free = max 3 active rules, pro = unlimited
- Alembic migrations for `alert_rules` + `alert_history` tables

### Out of Scope
- Real-time/streaming alerts (evaluation only on upload ready)
- Email/push notification delivery
- Custom rule types beyond the 5 defined

## Capabilities

### New Capabilities
- `alerts`: Rule-based alert system — CRUD for rules, metric evaluation on upload completion, paginated history with hourly Redis dedup

### Modified Capabilities
None — new module, no existing specs change.

## Approach

**Evaluation**: Parser Celery task marks upload as `ready` → calls `AlertsService.evaluate(upload_id)` → loads user's active rules → checks each against analytics metrics → if triggered, checks Redis dedup key (`alert:{uid}:{rule_id}:{hour}`) with 1h TTL → if not fired in last hour, saves to `alert_history`.

**Rule→metric mapping**: max_loss_per_trade→worst_trade, loss_streak→max_loss_streak, daily_loss_limit→sum net_pnl per day from trades, win_rate_drop→win_rate (threshold as decimal 0.0–1.0), rr_below→rr_ratio (null = below any threshold).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/modules/alerts/` | New | router, service, rules, schemas, models |
| `app/parser/tasks.py` | Modified | Trigger evaluation after upload→ready |
| `app/main.py` | Modified | Register alerts router |
| `alembic/versions/` | New | 2 migrations: alert_rules, alert_history |
| `tests/modules/test_alerts.py` | New | Integration tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Daily loss limit per-upload only | Low | Documented limitation |
| Evaluation blocks parser pipeline | Med | Fire-and-forget via Celery chain; failures logged only |
| Redis key collision | Low | Composite: uid + rule_id + UTC hour |

## Rollback Plan

1. Remove alerts router from `app/main.py`
2. Revert parser task trigger in `app/parser/tasks.py`
3. `alembic downgrade -2` to drop both tables
4. Delete `app/modules/alerts/` and test file

## Dependencies

- `AnalyticsService` — metrics for rule evaluation
- `Upload` model — trade grouping for daily_loss_limit
- Redis — hourly dedup keys
- auth module — `user.plan` for rule count cap

## Success Criteria

- [ ] All 5 CRUD endpoints work per AGENTS.md contracts
- [ ] Free user: POST blocked at 3 active rules (403)
- [ ] Pro user: POST creates rule with no limit
- [ ] Alert fires when upload→ready and metric crosses threshold
- [ ] Same rule fires ≤1x/hour per user (Redis dedup)
- [ ] GET /alerts/history returns paginated, ordered by triggered_at DESC
- [ ] Evaluation never fails parser pipeline — failures logged, not raised
