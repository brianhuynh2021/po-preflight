# AWS deployment

## Recommended MVP topology

- One Ubuntu EC2 instance runs OpenClaw Gateway continuously.
- An encrypted EBS volume stores OpenClaw state and the OrderFlow audit database.
- The security group exposes SSH only to an administrator CIDR.
- Port 18789 remains private; administrators use SSH tunneling or Tailscale.
- Claude and Slack APIs are outbound connections.

## One-time bootstrap

1. Provision EC2 from `infra/terraform`.
2. Install and onboard OpenClaw on the instance.
3. Configure Anthropic and Slack credentials outside Git.
4. Install the Gateway as a persistent service.
5. Configure a dedicated SSH deploy key for the OpenClaw service user.
6. Add the repository secrets listed below.

## GitHub repository secrets

- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`
- `EC2_SSH_PORT` (optional; defaults to 22)

After bootstrap, a push to `main` runs tests, uploads a release archive, installs the skill, restarts the Gateway, and probes its health.

The deployment does not commit or upload runtime databases, customer orders, model credentials, or Slack tokens.
