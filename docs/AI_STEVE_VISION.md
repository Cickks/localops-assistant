# AI Steve Vision

AI Steve is not just a chatbot and not only a server assistant.

The long-term goal is to build AI Steve into Michael's personal enterprise operating system: an AI command center for the homelab, documentation, help desk practice, cybersecurity, automation, career growth, portfolio evidence, future business services, and personal productivity.

Current homelab sequencing is tracked in [HOMELAB_MASTERPLAN_SYNC.md](HOMELAB_MASTERPLAN_SYNC.md).

## North Star

AI Steve should eventually be able to answer:

> What is the state of my world, what needs attention, what changed recently, what should I do next, and what can you safely help me do?

That includes infrastructure, projects, tickets, study goals, documentation, business workflows, and personal priorities.

## Core Principle

Build the environment first. Then let AI Steve understand it.

AI Steve should not manage undocumented experiments. It should operate against systems that have:

- Clear names.
- Known IPs and DNS records.
- Documented services.
- Monitoring.
- Logs.
- Backups.
- Rollback plans.
- Approval gates for risky actions.

## Major Layers

| Layer                 | Purpose                                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------------------- |
| Infrastructure Steve  | Understands servers, services, Docker, backups, logs, alerts, and health checks                         |
| Documentation Steve   | Reads and updates SOPs, phase notes, server docs, diagrams, incident reports, and change notes          |
| Help Desk Steve       | Creates tickets, guides troubleshooting, summarizes fixes, and turns issues into portfolio evidence     |
| Security Steve        | Explains alerts, reviews suspicious activity, suggests response steps, and supports SOC-style workflows |
| Automation Steve      | Runs approved scripts, creates reports, performs checks, and schedules safe recurring tasks             |
| Portfolio Steve       | Turns completed work into resume bullets, GitHub notes, case studies, and interview stories             |
| Study Steve           | Supports certification study, mock interviews, quizzes, and weak-area review                            |
| Business Steve        | Helps build client websites, service packages, support workflows, appointment flows, and lead handling  |
| Personal Steve        | Tracks goals, routines, reminders, projects, and priorities                                             |
| Voice/Dashboard Steve | Provides a command center UI and eventually voice interaction for the whole system                      |

## Future Capabilities

AI Steve should eventually support:

- RAG over homelab documentation, SOPs, tickets, notes, and project files.
- Server and service inventory lookup.
- Monitoring status summaries from tools such as Uptime Kuma, Grafana, Prometheus, Loki, and Wazuh.
- Ticket creation, ticket summaries, and incident reports.
- Change-plan generation with rollback steps.
- Safe command suggestions and approved execution.
- Script generation and review.
- Backup and restore reminders.
- Dashboard views for phase status, service status, risks, and next actions.
- Voice input/output after the core system is stable.
- Business workflow automation for future client services.
- Career support: STAR stories, interview walkthroughs, resume bullets, and portfolio packaging.

## Example Future Interaction

```text
Michael:
Steve, what is the state of the homelab?

AI Steve:
Phase 12 is active. LINUX01 is the current Linux/self-hosting practice host.
Samba and NFS are complete. DC01, DHCP01, FILE01, PRINT01, LINUX01, and
INFRA01 are documented. The next recommended task is Phase 12.3 Cron jobs.
Deferred risk: INFRA01 is online but still staging on microSD and needs SSD
storage, Docker data placement, backups, monitoring, and rollback documentation
before becoming an important always-on services host.
```

## Agent Model

AI Steve can grow into a multi-agent system, but each agent should have a clear scope.

| Agent                        | Scope                                                                     |
| ---------------------------- | ------------------------------------------------------------------------- |
| Windows Infrastructure Agent | AD, DNS, DHCP, GPO, file services, print services, Windows health         |
| Linux Infrastructure Agent   | SSH, packages, systemd, cron, storage, logs, Docker hosts                 |
| Networking Agent             | IP plans, DNS, routing, firewall notes, diagrams, connectivity checks     |
| Monitoring Agent             | Uptime, metrics, logs, dashboards, alert summaries                        |
| Security Agent               | SIEM alerts, hardening notes, incident response, vulnerability triage     |
| Automation Agent             | PowerShell, Bash, scheduled jobs, reports, safe execution plans           |
| Documentation Agent          | SOPs, runbooks, phase trackers, changelogs, evidence capture              |
| Career Agent                 | Resume bullets, STAR stories, interview prep, portfolio packaging         |
| Business Agent               | Client workflows, website services, support flows, sales/admin automation |
| Personal Operations Agent    | Goals, routines, reminders, planning, weekly reviews                      |

## Infrastructure Path

AI Steve appears late in the homelab sequence on purpose.

| Phase | Relationship To AI Steve                                                                                                                          |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 12    | Linux/self-hosting foundations on LINUX01: Samba, NFS, cron, systemd, SSH keys, backups, first-app planning, and documentation platform planning  |
| 12.8  | Enterprise documentation platform planning gives AI Steve SOPs, change logs, incidents, rollback notes, and backup/restore evidence to read later |
| 14    | Monitoring and observability provide status data                                                                                                  |
| 15    | ITSM/ticketing gives Steve operational workflows                                                                                                  |
| 16    | SOC/security tooling gives Steve security context                                                                                                 |
| 18    | INFRA01 becomes a real always-on services host after SSD readiness and production-readiness work                                                  |
| 20    | DevOps/IaC gives Steve repeatable deployment context                                                                                              |
| 21    | Databases/APIs/web services give Steve application foundations                                                                                    |
| 22    | AI Steve becomes the primary AI platform project                                                                                                  |
| 23    | AI Steve expands toward business automation and client-facing services                                                                            |
| 25    | AI Steve helps package the whole journey into career evidence                                                                                     |

## INFRA01 Relationship

INFRA01 is part of AI Steve's future, but not the first production host for important AI services.

Current decision:

- LINUX01 is the current practice and staging host.
- INFRA01 is a staged Raspberry Pi infrastructure node.
- INFRA01 should stay light until SSD storage, Docker data placement, backup planning, monitoring, and rollback are ready.
- The current master plan completes LINUX01 practice through Phase 12.7 before starting Phase 12.0B INFRA01 production readiness, unless hardware readiness becomes urgent.
- Gitea is the preferred first self-hosted application after backup basics because it teaches Git, repositories, service ownership, persistence, updates, and restore testing.
- Vaultwarden comes after backup and security handling are proven because it stores secrets.
- Nextcloud and Jellyfin stay deferred until storage and restore confidence are stronger.
- BookStack or Wiki.js belongs in Phase 12.8 as the enterprise documentation platform, with BookStack preferred first for clean SOPs and operational documentation.
- Around Phase 18, INFRA01 can become an always-on Docker/container services host.
- Around Phase 22, AI Steve can observe or manage INFRA01 after monitoring, inventory, logs, backups, and rollback are documented.

## Safety Model

AI Steve should never silently perform risky actions.

Rules:

- Read-only actions come first.
- Suggestions come before execution.
- Command execution requires approval gates.
- Destructive actions require explicit confirmation and rollback awareness.
- Secrets never appear in logs, docs, Git, or prompts.
- Production-style evidence is captured for important actions.
- AI Steve should explain why an action matters in real IT terms.

## Build Philosophy

AI Steve should feel powerful because the foundation is real.

The goal is not to bolt AI onto chaos. The goal is to build a clean enterprise-style lab, then give AI Steve structured access to the documentation, inventory, monitoring, tickets, and automation that already exist.

Short version:

> AI Steve is the AI brain for Michael's infrastructure, career, portfolio, future business, and personal operating system.
