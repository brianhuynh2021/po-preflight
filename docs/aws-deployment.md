# AWS deployment

## Recommended MVP topology

- One Ubuntu EC2 instance runs the Preflight FastAPI application and workers.
- An encrypted EBS volume stores the Preflight database and audit logs.
- The security group exposes SSH only to an administrator CIDR.
- Port remains private; administrators use SSH tunneling or Tailscale.
- Telegram, Zalo, and Slack APIs use secure outbound webhooks.

## One-time bootstrap

1. Provision EC2 from `infra/terraform`.
2. Configure credentials outside Git.
3. Install FastAPI service as a persistent daemon.
4. Configure a dedicated SSH deploy key.
5. Add the repository secrets listed below.

## GitHub repository secrets

- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`
- `EC2_SSH_PORT` (optional; defaults to 22)

After bootstrap, a push runs tests, uploads a release archive, restarts the service, and probes its health.

The deployment does not commit or upload runtime databases, customer orders, model credentials, or Slack tokens.
