# Homelab Master Plan Sync

Source alignment: `C:\Portfilio\MASTERPLAN\ROADMAP.docx` and `C:\Portfilio\IT-ENGINEER-TOOLKIT`.

Last synced: 2026-07-06 UTC

## Current Homelab Position

AI Steve is downstream of the enterprise homelab foundation. It should not become an operations platform until the systems it observes are documented, monitored, backed up, and recoverable.

Current Phase 12 status:

| Phase                                  | Status   | Notes                                                                                                              |
| -------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------ |
| 12.0A LINUX01 practice before INFRA01  | Complete | Baseline, package maintenance, reboot validation, SSH, Docker, containerd, Portainer, and storage checks completed |
| 12.0B INFRA01 production readiness     | Planned  | Start after the LINUX01 practice path through 12.7 unless hardware readiness becomes urgent                        |
| 12.1 Samba baseline                    | Complete | Internal SMB share validated from Windows                                                                          |
| 12.2 NFS baseline                      | Complete | Internal NFS export validated with mount, write, read, delete, unmount, and cleanup                                |
| 12.3 Cron jobs                         | Next     | Scheduled maintenance and report jobs                                                                              |
| 12.4 systemd services                  | Planned  | Custom service lifecycle management and logs                                                                       |
| 12.5 SSH keys                          | Planned  | INFRA01 key auth and sync workflow                                                                                 |
| 12.6 Linux backups                     | Planned  | Config, service data, documentation, and restore validation                                                        |
| 12.7 First self-hosted app decision    | Planned  | Choose one starter app after backup basics are proven                                                              |
| 12.8 Enterprise documentation platform | Planned  | BookStack or Wiki.js, not both at first                                                                            |

## App Placement

Recommended order:

1. Gitea: first app after Linux backups because it proves Git, repos, persistence, updates, and restore testing.
2. Vaultwarden: after backup and security process is proven because it stores secrets.
3. Nextcloud: defer until storage and restore confidence are stronger.
4. Home Assistant: optional if there is a clear hardware or integration goal.
5. Jellyfin: defer because it is storage-heavy and lower priority for the systems-administrator track.

## INFRA01 Guardrail

INFRA01 remains staged until production readiness is complete:

- NVMe HAT
- 1TB NVMe SSD
- Active cooling
- OS updates
- SSH key validation
- Static IP or DHCP reservation
- SSD-backed Docker data path
- Docker Engine and Compose
- Portainer
- Backup plan
- Monitoring expectation
- Rollback documentation

## AI Steve Implication

AI Steve should initially read and summarize:

- Phase tracker
- Server inventory
- Port/service inventory
- SOPs
- Change logs
- Incident reports
- Backup and restore evidence
- Monitoring output once Phase 14 exists

AI Steve should not perform write operations against INFRA01 or hosted services until the relevant system has documented access paths, monitoring, backups, and rollback procedures.
