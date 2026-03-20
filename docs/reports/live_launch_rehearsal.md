# Live Launch Rehearsal Dry Run

## Purpose

Capture the supervised launch workflow that is now expected for a live cut, using the local repo state and the validated CLI/test gates.

## Rehearsal sequence

1. Confirm the repo is clean enough to validate and that the compliance gate blocks by default.
2. Verify launch-readiness requires a funded account, flat broker truth, contradiction-free broker state, and recovery proof.
3. Exercise the CLI launch-readiness path and the operator-facing runtime checks.
4. Validate broker fail-closed behavior for cancel handling and explicit live-account override behavior.
5. Run the repository test suite and capture the result as the evidence set for the launch checklist.

## Evidence captured

- `pytest tests/test_matrix_engine.py tests/test_analysis_regime_packet.py tests/test_topstep_client.py tests/test_compliance_gate.py tests/test_observability_crash_recovery.py -q` -> `189 passed`
- `pytest -q` -> `237 passed`
- `scripts/compliance_gate.py` now exits non-zero unless `COMPLIANCE_GATE_ACK` is explicitly set.
- `build_launch_readiness()` now reports the launch gate as green only when the runtime is healthy, the account is funded/live, broker truth is flat, contradictions are absent, and recovery has been verified.
- `cancel_order()` now fails closed on broker-declared failure instead of assuming transport success is enough.

## Notes

This artifact is a local dry-run rehearsal based on the validated repo state. A real supervised live-account launch still requires the operator to supply live credentials, intentionally enable non-practice account use, and perform the final broker-session signoff.
