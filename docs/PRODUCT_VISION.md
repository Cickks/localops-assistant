# Product Vision

LocalOps Assistant is a local-first operations assistant for a homelab environment. The current
project is a backend API that talks to Ollama. The long-term direction is to let the assistant read
approved documentation, summarize operational state, and help with troubleshooting workflows after
the supporting infrastructure is documented and recoverable.

## Current Scope

The repository currently provides:

- FastAPI service
- Ollama chat provider
- Streaming and non-streaming chat endpoints
- Health and readiness endpoints
- Structured logging and request IDs
- Docker support
- Automated tests

## Out Of Scope Today

The following ideas are future work and are not implemented yet:

- Persistent conversation memory
- Retrieval over documentation
- Voice input or speech output
- Monitoring integrations
- Ticket creation
- Command execution
- Multi-user authentication
- Frontend dashboard

## Product Direction

The assistant should grow only after the homelab foundation is stable. A useful operations assistant
needs reliable inputs: inventories, diagrams, service owners, port records, SOPs, incidents, change
logs, backup evidence, and monitoring output.

Potential future capabilities:

- Read documented inventories and runbooks
- Summarize recent incidents and lessons learned
- Help generate troubleshooting checklists
- Explain service health based on approved monitoring sources
- Produce portfolio-ready summaries from completed lab work
- Support safe, reviewed automation workflows

## Safety Principles

- Read-only capabilities come before write capabilities.
- Any action that changes infrastructure should require explicit approval.
- The assistant should reference documented sources instead of guessing.
- Systems should have backups, rollback steps, and monitoring before automation touches them.
- Commands should be allowlisted and logged before any command execution feature is added.

## Homelab Relationship

LocalOps Assistant is downstream of the infrastructure work. It should not be treated as the control
plane for the lab until the Linux, backup, documentation, monitoring, and service-management phases
are complete.

See [Homelab alignment](HOMELAB_ALIGNMENT.md) for the current sequencing.
