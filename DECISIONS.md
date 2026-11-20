# Architecture & Engineering Decisions (ADR)

## ADR 001: Recurrence Safety & Occurrence Boundaries
- **Status:** Accepted
- **Context:** Infinite RRULE expressions (e.g. `FREQ=HOURLY` without `COUNT` or `UNTIL`) could cause unbounded memory expansion.
- **Decision:** Cap recurrence expansion at `max_occurrences=100` by default, configurable via settings, and handle malformed strings gracefully.
- **Consequences:** Protects memory and runtime execution from malicious or accidental infinite loops.

## ADR 002: Batching Database Log Inserts
- **Status:** Accepted
- **Context:** Executing single-row SQL inserts per email inside nested loops creates I/O bottlenecks.
- **Decision:** Buffer log records during batch iteration and persist using `executemany` inside a single transaction.
- **Consequences:** Drastically improves dispatch throughput without altering table schema or CSV output.

## ADR 003: Resilient Multi-Format Timestamp Parsing
- **Status:** Accepted
- **Context:** Hardcoded `%Y-%m-%d %H:%M:%S` format failed on ISO 8601 timestamps.
- **Decision:** Support fallback parsing via standard formats and `dateutil.parser`.
- **Consequences:** Eliminates runtime crashes on standard formatted date inputs.
