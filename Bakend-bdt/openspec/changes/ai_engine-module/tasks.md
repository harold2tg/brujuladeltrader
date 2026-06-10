# Tasks: AI Engine Module

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 900–1200 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Foundation: worker.py, models, schemas, base provider | PR 1 | base = feature/ai-engine; ~200 lines |
| 2 | Providers + Service + Prompts | PR 2 | base = PR 1 branch; ~350 lines |
| 3 | Router + Celery tasks + Integration | PR 3 | base = PR 2 branch; ~250 lines |
| 4 | Tests + Migration + main.py wiring | PR 4 | base = PR 3 branch; ~300 lines |

## Phase 1: Foundation (Worker, Models, Schemas, ABC)

- [ ] 1.1 Create `app/worker.py` — Celery app bootstrap with Redis broker config
- [ ] 1.2 Create `app/modules/ai_engine/__init__.py` — empty package init
- [ ] 1.3 Create `app/modules/ai_engine/models.py` — `AiCredentials` SQLAlchemy model (UUID PK, user_id FK, provider, api_key_enc, base_url, model_override, is_active, timestamps)
- [ ] 1.4 Create `app/modules/ai_engine/schemas.py` — Pydantic schemas: `AiCredentialsCreate`, `AiCredentialsUpdate`, `AiCredentialsResponse` (masked key), `AiTestRequest`, `AiTestResponse`, `AnalyzeRequest`, `AnalyzeResponse`, `JobStatusResponse`, `InsightsResponse`
- [ ] 1.5 Create `app/modules/ai_engine/providers/__init__.py` — exports `AIProvider`
- [ ] 1.6 Create `app/modules/ai_engine/providers/base.py` — `AIProvider` ABC with `generate()` and `health_check()` abstract methods

## Phase 2: Providers + Service + Prompts

- [ ] 2.1 Create `app/modules/ai_engine/providers/claude.py` — `ClaudeProvider` implementing `AIProvider` using Anthropic AsyncAnthropic SDK
- [ ] 2.2 Create `app/modules/ai_engine/providers/openai.py` — stub `OpenAIProvider` raising `NotImplementedError`
- [ ] 2.3 Create `app/modules/ai_engine/providers/gemini.py` — stub `GeminiProvider` raising `NotImplementedError`
- [ ] 2.4 Create `app/modules/ai_engine/providers/ollama.py` — stub `OllamaProvider` raising `NotImplementedError`
- [ ] 2.5 Create `app/modules/ai_engine/prompts.py` — `SYSTEM_PROMPT` dict (es/en), `ANALYSIS_TYPES` dict, user prompt templates per analysis type
- [ ] 2.6 Create `app/modules/ai_engine/service.py` — `AiService` with: `create_credentials()`, `get_credentials()`, `update_credentials()`, `delete_credentials()`, `test_credentials()`, `analyze()`, `get_job_status()`, `get_insights()`. Include rate limit check (Redis counter), cache lookup (Redis GET/SET 24h), fallback to `InsightGenerator`.

## Phase 3: Router + Celery Tasks + Integration

- [ ] 3.1 Create `app/modules/ai_engine/router.py` — 8 endpoints (5 credentials + 3 analysis) with auth dependency
- [ ] 3.2 Create `app/modules/ai_engine/tasks.py` — Celery task `run_analysis` that calls service, stores result in Redis (job + cache keys)
- [ ] 3.3 Modify `app/main.py` — register `ai_engine.router` with prefix `/ai`
- [ ] 3.4 Modify `pyproject.toml` — add `anthropic` dependency

## Phase 4: Testing + Migration

- [ ] 4.1 Generate Alembic migration: `alembic revision --autogenerate -m "add ai_credentials"`
- [ ] 4.2 Create `tests/modules/test_ai_engine.py` — unit tests for: AIProvider ABC validation, ClaudeProvider.generate() mock, rate limit counter (0/9/10/11 calls), fallback logic, encrypt/decrypt roundtrip
- [ ] 4.3 Integration tests: credentials CRUD endpoints, analyze endpoint (mock Celery), cache hit/miss, full flow (credentials → analyze → poll → result)

## Phase 5: Cleanup

- [ ] 5.1 Verify all endpoints return standard response format `{ success, data, message }`
- [ ] 5.2 Ensure api_key_enc is never logged or returned in plain text
- [ ] 5.3 Update AGENTS.md if any convention changed
