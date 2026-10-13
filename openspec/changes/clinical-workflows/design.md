## Context

Free-form text is clinical by default. Administrative adult delegates cannot
see it. Repeat submission does not authorize preparation.

## Goals / Non-Goals

Goals: private outcomes, accountable immutable revisions and explicit follow-up/
repeat decisions. Non-goals: full EMR, chat, diagnosis, auto answers, run-out
inference or auto renewal.

## Decisions

`clinical/models.py` defines clarification responses, visits, instruction
revisions and repeat decisions. Clinical decisions/instruction writes require
doctor MFA; patient missing-information replies and clarification cancellation
require current clinical scope. All clinical reads require current clinical grants.

Clarification outcomes are reply, missing information or consultation required.
Follow-up stays in the same structured authorized request, not an open chat.

Visit follow-up date is nullable and explicit. Instruction revisions contain
medicine/precautions/diet, doctor/time and unique `(visit, revision)`.
Lock visit before allocating the next number. Preserve old revisions and
prohibit their application update/delete paths.

Repeat approve/decline/consultation-required records actor/time under request
lock. Define allowed state transitions before code. No elapsed-time, charge,
past medicine or fulfillment inference authorizes approval.

Administrative selectors use an explicit structured allowlist. Do not supply
clinical text/reasons to administrative templates or rely on HTML hiding.
Audit append shares the decision transaction and references IDs, not payloads.
Logs avoid request bodies and private inputs in URLs/errors.
Exception reports withhold request values, locals and exception payloads
globally rather than relying on individual form annotations.

## Risks / Trade-offs

Historical paper information intentionally remains valid. Revisions store more
text but retain accountable edits. Same household phone may have child clinical
access but no adult clinical access.

## Migration Plan

Create clinical tables and constraints; no fabricated historic visits.

## Verification

Test outcomes, current-grant revocation, revision sequence/history/concurrency,
explicit nullable dates, repeat actor/time, no timeout and privacy projection.
Assert synthetic secret text is absent from admin responses and audit/logs.
