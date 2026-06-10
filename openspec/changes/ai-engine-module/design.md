# Design: AI Engine Module

## Technical Approach

Multi-provider AI abstraction (`AIProvider` ABC) with ClaudeProvider as MVP. Credentials per user encrypted via existing AES-256-GCM. Analysis runs asynchronously via Celery with Redis-based job polling. Deterministic `InsightGenerator` fallback when no credentials, rate-limited, or provider error. Follows the same module pattern as `ctrader`/`reports`.

## Architecture Decisions

### Decision: Provider package location

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `app/shared/ai_provider.py` | Logical for shared abstraction, but providers are module-scoped | `app/modules/ai_engine/providers/` |
| `app/modules/ai_engine/providers/` | Co-locates ABC + all impls with consumer | ✅ Chosen |

Rationale: The ABC only makes sense within ai_engine. No other module calls it. Keeps the module self-contained.

### Decision: Single vs. multiple credentials per user

| Option | Tradeoff | Decision |
|--------|----------|----------|
| One row per provider per user | Users can configure multiple providers, switch freely | ✅ Chosen |
| Single row with provider column | Simpler but forces provider swap on every config | Rejected |

Rationale: Users may test different providers. `provider` is part of the PK constraint `(user_id, provider)`.

### Decision: Worker.py as separate file

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Celery app in `worker.py` | Clean bootstrap, no circular imports | ✅ Chosen |
| Celery app inline in tasks.py | Tight coupling, hard to reuse across modules | Rejected |

Rationale: Follows established FastAPI+Celery conventions. `worker.py` imports tasks, never the reverse.

### Decision: Rate-limit key design

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Counter + TTL to midnight UTC-5 | Accurate to daily quota, survives midnight reset | ✅ Chosen |
| Counter + fixed 24h TTL | Drifts from calendar day | Rejected |
| Redis sorted set per user | Overkill for a simple counter | Rejected |

Rationale: `expireat` to midnight UTC-5 aligns with the user's trading day (Colombia timezone).

## Data Flow

```
POST /ai/{upload_id}/analyze
  │
  ├─► [service] check credentials exist
  ├─► [service] check rate limit (redis counter)
  ├─► [service] check cache (redis GET)
  │
  ├── HIT ──► return cached result
  │
  └── MISS ──► create job ──► Celery task
                    │
                    ├─► ClaudeProvider.generate()
                    │     └─► Anthropic SDK (async)
                    │
                    ├─► On error/limit ──► InsightGenerator
                    │
                    └─► Store result in Redis (24h TTL, job + cache)
                          └─► Poll via GET /ai/jobs/{job_id}
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/modules/ai_engine/__init__.py` | Create | Package init |
| `app/modules/ai_engine/models.py` | Create | `AiCredentials` SQLAlchemy model |
| `app/modules/ai_engine/schemas.py` | Create | Pydantic request/response schemas |
| `app/modules/ai_engine/prompts.py` | Create | System/user prompt templates (es/en) |
| `app/modules/ai_engine/router.py` | Create | 8 endpoints (5 credentials + 3 analysis) |
| `app/modules/ai_engine/service.py` | Create | `AiService` — orchestrates auth, rate-limit, cache, provider, fallback |
| `app/modules/ai_engine/tasks.py` | Create | Celery tasks for async analysis |
| `app/modules/ai_engine/providers/__init__.py` | Create | Exports `AIProvider` ABC |
| `app/modules/ai_engine/providers/base.py` | Create | `AIProvider` abstract base class |
| `app/modules/ai_engine/providers/claude.py` | Create | `ClaudeProvider` — Anthropic SDK wrapper |
| `app/modules/ai_engine/providers/openai.py` | Create | Stub for post-MVP |
| `app/modules/ai_engine/providers/gemini.py` | Create | Stub for post-MVP |
| `app/modules/ai_engine/providers/ollama.py` | Create | Stub for post-MVP |
| `app/worker.py` | Create | Celery app bootstrap |
| `app/main.py` | Modify | Register `ai_engine.router` |
| `pyproject.toml` | Modify | Add `anthropic` dependency |
| `alembic/versions/` | Create | Migration for `ai_credentials` table |
| `tests/modules/test_ai_engine.py` | Create | Tests with mocked Anthropic SDK |

## Interfaces / Contracts

### AIProvider ABC

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate(
        self, system_prompt: str, user_prompt: str,
        max_tokens: int = 1500, temperature: float = 0.7,
    ) -> str: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
```

### AiCredentials model

```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
provider        VARCHAR(20) NOT NULL         -- claude | openai | gemini | ollama
api_key_enc     TEXT                         -- AES-256-GCM encrypted (null for ollama)
base_url        VARCHAR(500)                 -- ollama server URL
model_override  VARCHAR(100)                 -- optional custom model
is_active       BOOLEAN NOT NULL DEFAULT TRUE
created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
UNIQUE(user_id, provider)
```

### Redis key patterns

| Purpose | Key Pattern | TTL |
|---------|-------------|-----|
| Rate limit counter | `ai:daily:{user_id}:{YYYY-MM-DD}` | Until midnight UTC-5 |
| Cache (analysis result) | `ai:{user_id}:{upload_id}:{type}:{lang}` | 24h |
| Job status | `ai:job:{job_id}` | 24h |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `AIProvider` ABC validation | `pytest` with ABCMeta checks |
| Unit | `ClaudeProvider.generate()` | Mock `anthropic.AsyncAnthropic` — verify SDK call args |
| Unit | Rate limit counter | Inject mock Redis, test `check_rate_limit` at 0, 9, 10, 11 calls |
| Unit | Fallback logic | Mock `ClaudeProvider.generate()` to raise, verify `InsightGenerator` called |
| Unit | Encryption roundtrip | `encrypt()` → `decrypt()` with known key |
| Integration | Credentials CRUD endpoints | HTTP test with test DB + mock Redis |
| Integration | Analyze endpoint | Mock Celery task, verify job created in Redis |
| Integration | Cache hit/miss | Set cache in Redis, verify endpoint returns cached data |
| E2E | Full flow | Test user with credentials → analyze → poll job → get result |

**Mock Anthropic SDK everywhere. Zero real API calls in tests.**

## Migration / Rollout

1. Create `app/worker.py` with Celery app (no impact, no existing worker)
2. Add `anthropic` SDK to `pyproject.toml`, run `poetry install`
3. Generate Alembic migration: `alembic revision --autogenerate -m "add ai_credentials"`
4. Run migration on dev DB
5. Register router in `app/main.py`
6. All 8 endpoints operational once deployed; no data migration needed

## Open Questions

- [ ] Confirm Celery broker URL: same `REDIS_URL` as app cache? Set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` in config.
- [ ] Rate limit reset: is midnight UTC-5 correct, or should it be user-timezone-aware? Proposal says UTC-5.
- [ ] Claude model: `claude-sonnet-4-20250514` or use `claude-sonnet-4-20250514` as default with `haiku` as fast option?
