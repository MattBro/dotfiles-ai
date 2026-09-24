# AWS access

Prod EKS access (kubectl and toolbox pods) needs a temporary grant from the AWS Access Elevator bot in #aws-access. `aws sso login` alone does not give that access.

When you ask me to run `aws sso login --sso-session posthog` for prod EKS work, put these steps in the same message:

1. Request a grant in #aws-access with these values:
   - Account: `production-us` (use `production-eu` for EU)
   - Permission set: `eks-developer`
   - Duration: `1h`
   - Reason: one line that names the task and links the PR or issue
2. Wait for the bot's GRANTED message.
3. Run `! aws sso login --sso-session posthog`.
