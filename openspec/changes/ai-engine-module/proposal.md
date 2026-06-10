# Proposal: ai-engine-module

## Intent

Add AI-powered trading analysis. Users configure their own AI provider (Claude MVP) to get personalized diagnosis, monthly reviews, and improvement plans. Without this, insights are purely deterministic — no natural-language context or actionable tailored recommendations.

## Scope

### In Scope
- AIProvider ABC + ClaudeProvider (Anthropic SDK)
- Credentials CRUD (POST/GET/PUT/DELETE/test) with AES-256-GCM encryption
- Analysis endpoints (POST analyze, GET job status, GET cached insights)
- Redis rate limiting (10/day free) + cache (24h TTL)
- Celery task for async analysis with InsightGenerator fallback
- `app/worker.py` — Celery app bootstrap
- Alembic migration for `ai_credentials` table

### Out of Scope
- OpenAI/Gemini/Ollama providers (stubbed for post-MVP)
- Streaming responses
- Multi-provider auto-failover
- UI/UX for credential form

## Capabilities

### New Capabilities
- `ai-credentials`: CRUD + test for AI provider credentials per user
- `ai-analysis`: Trigger/poll/cache AI analysis over trade metrics

### Modified Capabilities
None — new module, no existing specs change.

## Approach

`AIProvider` ABC → `ClaudeProvider` → Service orchestrates auth, rate-limit check (`redis:ai:daily:{user_id}`), cache lookup (`redis:ai:{uid}:{upload}:{type}:{lang}`) → Celery task runs analysis async → 24h cache → Fallback `InsightGenerator` when no credentials, rate-limited, or provider error.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/modules/ai_engine/` | New | Full module: router, service, models, schemas, prompts, tasks, providers/ |
| `app/worker.py` | New | Celery app config (prerequisite) |
| `app/main.py` | Modified | Register `ai_engine.router` |
| `pyproject.toml` | Modified | Add `anthropic` SDK dependency |
| `alembic/versions/` | New | Migration for `ai_credentials` table |
| `tests/modules/test_ai_engine.py` | New | Test with mock Anthropic SDK |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Anthropic API latency | High | Async Celery task, polling pattern |
| API key leak in logs | Med | Never log api_key_enc, mask in responses |
| Rate limit clock skew | Low | Redis TTL to midnight UTC-5 (fixed, not 24h from now) |
| Claude-only vendor lock | Low | ABC ready for new providers |

## Rollback Plan

1. Remove `ai_engine` router from `app/main.py`
2. Revert `pyproject.toml` SDK additions
3. `alembic downgrade -1` to drop `ai_credentials` table
4. Delete `app/modules/ai_engine/` and `app/worker.py`
5. Delete test file

## Dependencies

- `anthropic` Python SDK (add to pyproject.toml)
- `app/shared/crypto.py` — existing AES-256-GCM
- `app/modules/reports/insights.InsightGenerator` — deterministic fallback
- Redis running (rate limiting + cache + Celery broker)

## Success Criteria

- [ ] All 8 endpoints return correct responses per AGENTS.md contracts
- [ ] POST /ai/credentials → key encrypted, response masked
- [ ] POST /ai/{upload_id}/analyze → returns `{ job_id, status }`, processes async
- [ ] Free plan: >10 calls/day returns fallback, not error
- [ ] Cache hit returns within TTL; cache miss triggers Celery task
- [ ] No credentials → `fallback_used: true` with InsightGenerator output
- [ ] All tests pass (mock Anthropic SDK, zero real API calls)
