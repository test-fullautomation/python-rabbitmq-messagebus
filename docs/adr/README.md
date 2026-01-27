# Architecture Decision Records (ADR)

This folder contains Architecture Decision Records for the EventBusClient project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences. ADRs help teams understand why certain decisions were made and provide historical context for future developers.

## ADR Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-000](000-template.md) | Template | - | - |
| [ADR-001](001-standardize-ipc-api.md) | Standardize IPC / Message Bus API | Accepted | 2025-07-01 |
| [ADR-002](002-async-first-api.md) | Async-First Public API with Sync Wrappers | Accepted | 2025-07-05 |
| [ADR-003](003-plugin-strategy-pattern.md) | Plugin-based Strategy Pattern | Accepted | 2025-07-10 |
| [ADR-004](004-configuration-driven-setup.md) | Configuration-Driven Library Setup | Accepted | 2025-07-12 |
| [ADR-005](005-connection-manager.md) | Central ConnectionManager | Accepted | 2025-07-15 |
| [ADR-006](006-exchange-types.md) | Multiple Exchange Types via Handlers | Accepted | 2025-07-18 |
| [ADR-007](007-startup-policy-rendezvous.md) | StartupPolicy and Rendezvous | Accepted | 2025-07-20 |
| [ADR-008](008-subscription-cache.md) | SubscriptionCache for Sync Access | Accepted | 2025-08-01 |
| [ADR-009](009-unroutable-message-handling.md) | Configurable Unroutable Handling | Accepted | 2025-08-05 |

## ADR Summary

### Foundation Decisions

- **ADR-001**: Establishes EventBusClient as the shared IPC library replacing per-project wrappers
- **ADR-002**: Defines async-first API design with sync wrappers for legacy support
- **ADR-003**: Introduces plugin-based strategy pattern for extensibility
- **ADR-004**: Enables configuration-driven setup via JSONP files

### Core Architecture

- **ADR-005**: Centralizes connection lifecycle in ConnectionManager
- **ADR-006**: Provides dedicated ExchangeHandler per exchange type
- **ADR-007**: Enables coordinated startup via composable policies and rendezvous

### Messaging Patterns

- **ADR-008**: Bridges async delivery to sync consumption via SubscriptionCache
- **ADR-009**: Configures handling of unroutable messages

## Creating a New ADR

1. Copy `000-template.md` to `NNN-short-title.md`
2. Fill in all sections following the template
3. Update the index table in this README
4. Submit for review

## ADR Lifecycle

```
Proposed → Accepted → [Deprecated | Superseded]
```

- **Proposed**: Under discussion, not yet decided
- **Accepted**: Decision has been made and approved
- **Deprecated**: No longer valid, kept for historical reference
- **Superseded**: Replaced by another ADR (link to new ADR)

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's article on ADRs](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [Documenting Architecture Decisions](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)
