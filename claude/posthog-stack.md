# PostHog Stack

PostHog-specific patterns for the [posthog](https://github.com/PostHog/posthog), [posthog-js](https://github.com/PostHog/posthog-js), and [posthog.com](https://github.com/PostHog/posthog.com) repos.

## Django migrations

- **Always use `python manage.py makemigrations` to create migrations.** Never create migration files manually — manual files often have wrong dependencies or missing imports.
- **Never edit a migration after it has been committed.** Treat committed migrations as immutable. If you need changes, create a new migration.
  - Exception: not yet shared/deployed — you can roll back, delete, regenerate:
    1. `python manage.py migrate app_name previous_migration_number`
    2. Delete the migration file
    3. Update `app_name/migrations/max_migration.txt` to point to the previous migration
    4. `python manage.py makemigrations`
    5. `python manage.py migrate`
- **Strongly consider splitting migrations into separate PRs.** Migrations can be reviewed and merged quickly on their own, deployed earlier, and reduce risk on the feature PR.
- **Always run safety checks after creating migrations:**
  ```bash
  python manage.py analyze_migration_risk
  python manage.py makemigrations --check --dry-run
  ```
- **Test with environment variables** when migrations use settings or env-dependent defaults:
  ```bash
  CLOUD_DEPLOYMENT=EU python manage.py migrate app_name migration_number
  CLOUD_DEPLOYMENT=US python manage.py migrate app_name migration_number
  ```

## Kea state management

- **Prefer Kea actions for state logic.** When a component needs to manipulate state (especially with conditional logic), implement it as a Kea action rather than calling multiple Kea functions directly from components.
- Benefits:
  - Better separation of concerns (business logic in logic layer, not UI).
  - More testable (actions can be unit tested independently).
  - More maintainable (reusable across components).
  - Clearer intent (action names document behavior).
- Example: instead of calling `toggleFormulaMode()` directly after removing a formula, create one action like `removeFormulaAndToggleModeIfEmpty()` that encapsulates the entire behavior.

## posthog.com (docs site) development

The docs site is at `~/dev/posthog.com`.

```bash
cd ~/dev/posthog.com
pnpm install
pnpm start  # http://localhost:8001
```

- Use `pnpm start` (Gatsby dev). **Do not use `pnpm build`** locally — runs out of memory on this large site.
- **Do not clone/run from `/tmp`** — Gatsby has issues with temp directories.

### Debugging MDX files not appearing

- Gatsby silently skips MDX files with syntax errors — no error in dev server output.
- If a page 404s, check whether Gatsby discovered the file:
  1. Visit `http://localhost:8001/___graphql`
  2. Run `{ allMdx(filter: {fileAbsolutePath: {regex: "/your-path/"}}) { nodes { fileAbsolutePath fields { slug } } } }`
  3. If the file is missing, it likely has an MDX syntax error.
- To see MDX syntax errors, run `pnpm build` — errors appear before it crashes from memory.

### MDX with Tab components

Code blocks inside `<Tab.Panel>` need blank lines before and after:

````mdx
<Tab.Panel>

```js
// code here — blank line above and below required
```

</Tab.Panel>
````

## File organization for working notes

I keep working files in `~/dev/.claude/docs/`, organized by project:

```
docs/
  stripe/          Stripe Projects + Stripe App work
    specs/
    scripts/
    drafts/
    investigations/
  vercel/          Vercel integration work (same structure)
    specs/
    scripts/
    drafts/
    investigations/
    billing/
  specs/           non-project specs (MCP, auth, supabase, …)
  scripts/         non-project utility scripts
  drafts/          non-project message drafts
  investigations/  non-project research notes
  plans/           review feedback, learnings
```

Rules:

- Project-specific files go in their project dir (`stripe/`, `vercel/`).
- General files go in the top-level category dirs.
- Use descriptive filenames (e.g. `test_provisioning_pat.py`, not `test.py`).
- Drafts are ephemeral — clean them up after sending.

This directory is private by default. See its `README.md` for the safety policy.
