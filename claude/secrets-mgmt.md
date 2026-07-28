# Secrets Management

Managed by `~/dev/secrets/secrets.py`, backed by AWS Secrets Manager. Invoke with `uv run secrets.py` from that directory. There is no `secrets` binary on PATH.

```bash
uv run secrets.py list <env>                     # list managed secrets
uv run secrets.py get <env> <app>                # view (opens $EDITOR, read-only)
uv run secrets.py set <env1,env2> <app> <key>    # add/update ONE key
```

**Use `set <key>` for single-key changes, never whole-file `edit`.**

Envs are `dev`, `prod-us`, `prod-eu`, `internal`, and each needs `aws sso login --profile <env>` first. App names auto-append `-secrets`: `posthog-events-django` becomes `posthog-events-django-secrets`.
