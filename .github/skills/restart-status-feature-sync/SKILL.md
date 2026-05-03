---
name: restart-status-feature-sync
description: 'Check application status after restart or computer reset, verify health, discover new features in accessible repositories, and apply latest coding-agent findings safely. Use when restarting the app, resuming work, or beginning a new development session.'
argument-hint: 'Provide app name, repo scope (current or accessible repos), and priority area (stability, features, or both).'
user-invocable: true
---

# Restart Status And Feature Sync

## Outcome

Run a repeatable post-restart workflow that:

1. Confirms the app is healthy.
2. Detects regressions quickly.
3. Surfaces new feature opportunities from accessible repositories.
4. Applies latest coding-agent findings in a controlled, test-verified way.

## When To Use

- The application is restarted.
- The computer was reset and development context was lost.
- You are resuming work after a long pause.
- You want a fast status + improvement sweep before coding.

## Inputs

- Application or service name.
- Scope: current repository only, or all accessible repositories.
- Priority: stability first, feature discovery first, or balanced.
- Optional time budget (for example: 15, 30, or 60 minutes).

## Procedure

1. Rebuild execution context.
- Confirm workspace root and active branch.
- Re-activate the expected environment (virtualenv, conda, etc.).
- Load project instructions (README, task files, agent instructions) if not in context.

2. Establish current program status.
- Run quick health checks (lint/test/smoke route checks as available).
- Start services needed for validation.
- Capture baseline status: passing tests, failing tests, startup errors, and warnings.

3. Branch by health result.
- If critical failures exist: stop feature work and fix failures first.
- If only non-critical issues exist: log them and continue if policy allows.
- If fully healthy: proceed directly to feature scan.

4. Discover new feature opportunities.
- Review current repo signals first: TODO/FIXME notes, open API gaps, test TODOs, and missing docs.
- If scope includes accessible repositories, compare patterns that are reusable here (endpoints, workflows, architecture, tests).
- Prioritize candidates by user impact, implementation effort, and regression risk.

5. Integrate latest agent coding findings.
- Use the latest validated findings from prior sessions (bug patterns, test strategy improvements, refactor opportunities).
- Convert findings into concrete changes with acceptance criteria.
- Apply small, reversible increments.

6. Implement and verify.
- Make focused code changes for the top candidate(s).
- Re-run targeted tests, then broader regression tests.
- Validate runtime behavior for affected paths.

7. Produce session handoff.
- Summarize current health status.
- List implemented features and deferred opportunities.
- Record next actions for the next restart/reset cycle.

## Decision Points

- Health gate:
  - Fail: stabilize first.
  - Pass: continue to feature work.
- Scope gate:
  - Current repo only: mine local opportunities.
  - Accessible repos: include cross-repo pattern scan.
- Risk gate:
  - High regression risk: require tests before merge.
  - Low risk: allow fast path with smoke checks.

## Completion Checks

- Environment and services are confirmed running.
- Health checks were executed and results captured.
- At least one feature candidate was evaluated.
- Any implemented change has matching tests or explicit rationale for test deferral.
- A concise status summary and next-step list is produced.

## Output Format

Return results in this structure:

1. Program status: healthy/degraded/failed + evidence.
2. New feature candidates: ranked list with effort and risk.
3. Changes applied: files, tests, and behavioral impact.
4. Remaining issues: blockers and mitigation.
5. Next restart checklist: exact first commands/actions.
