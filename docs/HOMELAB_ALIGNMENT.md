# Homelab Alignment

LocalOps Assistant is part of the broader homelab roadmap, but it should remain downstream of the
infrastructure foundation. The assistant should read and summarize reliable documentation before it
is allowed to recommend or perform operational changes.

## Current Homelab Sequence

| Phase | Area                         | Status   | Relationship to LocalOps Assistant                          |
| ----- | ---------------------------- | -------- | ----------------------------------------------------------- |
| 12.1  | Samba                        | Complete | File-sharing and permission evidence for later reference    |
| 12.2  | NFS                          | Complete | Linux storage and mount-validation evidence                 |
| 12.3  | Cron jobs                    | Complete | Scheduled maintenance and reporting patterns                |
| 12.4  | systemd services             | Next     | Service lifecycle, logging, and failure-handling patterns   |
| 12.5  | SSH keys                     | Planned  | Secure remote administration foundation                     |
| 12.6  | Linux backups                | Planned  | Required before automating or advising on operational state |
| 12.7  | First self-hosted app        | Planned  | Practical app-hosting evidence after backups are understood |
| 12.8  | Documentation platform       | Planned  | Future structured source material for assistant retrieval   |
| 12.0B | INFRA01 production readiness | Planned  | Production-style host validation before important services  |

## Data Sources The Assistant Can Use Later

- Roadmap and phase tracker
- Server inventory
- IP address and port records
- SOPs and runbooks
- Troubleshooting guides
- Change logs
- Incident reports
- Backup and restore evidence
- Monitoring output after monitoring exists

## Guardrails

LocalOps Assistant should not perform write operations against lab systems until the affected system
has:

- Documented ownership and purpose
- Known IP address, DNS name, and service ports
- Backup and restore procedure
- Monitoring or health-check path
- Rollback procedure
- Logged change history

## Near-Term Development Order

1. Keep the current API stable.
2. Add persistence only after the schema and retention behavior are documented.
3. Add retrieval only after the documentation source is selected.
4. Add authentication before exposing the service outside a local development network.
5. Add automation only after commands are allowlisted, logged, and recoverable.
