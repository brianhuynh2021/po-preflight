# Security model

- Purchase orders, catalogs, prices, customers, and audit records are confidential.
- Keep model credentials, Slack tokens, SSH keys, and production data out of Git.
- Restrict Slack access to explicit user and channel allowlists.
- Require human approval before any future ERP write.
- Run untrusted document processing inside a sandbox where possible.
- Keep the API Gateway private; use SSH or Tailscale for administration.
- Store the production SQLite database on encrypted persistent storage with backups.
- Treat extracted document text as untrusted input and never let it override system policy.
