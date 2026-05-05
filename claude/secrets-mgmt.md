# Secrets Management

Secrets are managed via a small CLI in `~/dev/secrets/`, backed by AWS Secrets Manager.

## Environments

- `dev`
- `prod-us`
- `prod-eu`
- `internal`

## Commands

```bash
secrets list <env>                  # list all managed secrets in an env
secrets get <env> <app-name>        # view a secret (opens in $EDITOR, read-only)
secrets set <env1,env2,...> <app-name>  # add individual keys
secrets edit <env> <app-name>       # edit full secret JSON
```

Requires AWS SSO login first:

```bash
aws sso login --profile <env>
```

App names auto-append a `-secrets` suffix (e.g. `posthog-events-django` → `posthog-events-django-secrets`).
