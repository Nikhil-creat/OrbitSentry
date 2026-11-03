# Security

## Controls
- API-key auth (`x-api-key`), per-IP token-bucket rate limiting, CORS allow-list, strict pydantic validation
- Payload deduplication (idempotency), secrets only via environment / Docker secrets, non-root containers
- Vercel: CSP and security headers in `vercel.json`; LLM keys stay server-side in `/api/chat`
- Human-in-the-loop: throttle, isolation and shutdown actions are never executed autonomously

## Known gaps
- Rate limiter and dedupe cache are in-memory (single instance; reset on restart or cold start)
- API keys are static; there is no rotation, RBAC store or audit log yet
- LLM output is untrusted text and must not drive actions without operator approval
- Not flight-qualified; demo data is synthetic

## Reporting
Open a private security advisory on GitHub or email sriramojunikhil66@gmail.com.
