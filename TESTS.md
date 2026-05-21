# TESTS

Test strategy and coverage requirements for this project.

**Human-readable design layer.** Executable form: `test_cmd` in `config/manifest.yaml` + test files in `tests/`.
Filled by: **Tester agent** during the Validate activity. Reviewed by: human and Conductor.

---

## Test Philosophy

Tests are the objective evidence that the Validate activity produces. They are not optional and not aspirational — they are the scoring mechanism for the Validate rubric gate.

Every test maps to an **acceptance criterion** from a Story. If a Story has no test, it has no evidence of completion.

---

## Test Levels

### Unit Tests
- **Scope:** Single function, class, or module in isolation
- **Location:** `tests/unit/`
- **Naming:** `test_{module}_{scenario}.py`
- **Runs with:** `pytest tests/unit/ -v`
- **Coverage target:** {X}% (fill per project)
- **Who writes:** Developer agent (during Implement), refined by Tester agent

### Integration Tests
- **Scope:** Multiple components interacting — API endpoints, DB operations, service calls
- **Location:** `tests/integration/`
- **Naming:** `test_{component}_integration.py`
- **Runs with:** `pytest tests/integration/ -v`
- **Prerequisites:** Service must be running; use test fixtures not production data
- **Who writes:** Tester agent (during Validate)

### End-to-End Tests
- **Scope:** Full user story path from input to observable outcome
- **Location:** `tests/e2e/`
- **Naming:** `test_{story_title}.py`
- **Runs with:** `pytest tests/e2e/ -v`
- **Prerequisites:** Full environment deployed (use staging, not production)
- **Who writes:** Tester agent, mapped from acceptance criteria

### Health Tests
- **Scope:** Service availability and basic response validation
- **Location:** Inline in Monitor activity (health_url check)
- **Runs with:** `GET {health_url}` → expect HTTP 200
- **Who writes:** Deployer agent / Monitor agent

---

## Coverage Requirements

| Level | Target | Minimum to pass gate |
|---|---|---|
| Unit | {X}% | {Y}% |
| Integration | {X}% | {Y}% |
| Critical paths | 100% | 100% |

**Critical paths** = any flow that processes user data, handles auth, or writes to persistent storage. Zero tolerance for missing coverage here.

---

## Test Naming Convention

```
test_{what_is_being_tested}_{scenario}_{expected_outcome}

Examples:
  test_user_login_valid_credentials_returns_200
  test_invoice_create_missing_field_returns_422
  test_pipeline_gate_score_below_threshold_triggers_retry
```

---

## Test Fixtures and Data

- **Test data location:** `tests/fixtures/`
- **No production data in tests** — ever
- **No external service calls in unit tests** — mock everything external
- **Integration tests may call local services** — never production endpoints
- **Fixtures are deterministic** — same input always produces same output

---

## Marking Tests

```python
import pytest

@pytest.mark.critical   # gate failure if this fails — no retry, immediate escalate
@pytest.mark.slow       # excluded from fast test_cmd runs
@pytest.mark.integration  # requires running service
@pytest.mark.e2e        # requires full environment
```

---

## test_cmd Configuration

The `test_cmd` in `manifest.yaml` is what the Tester agent runs. It must:
1. Exit 0 on pass, non-zero on fail
2. Produce parseable output (pytest `-v --tb=short` recommended)
3. Complete within the time budget

```yaml
# manifest.yaml example
validate:
  test_cmd: >
    cd {project_path} &&
    {venv}/bin/pytest tests/unit/ tests/integration/
    -v --tb=short --co -q
    --cov={module} --cov-report=term-missing
    --timeout=60
```

---

## Story → Test Mapping

Every Story's acceptance criterion must have a corresponding test. The Tester agent fills this table:

| Story | Acceptance Criterion | Test File | Test Name | Status |
|---|---|---|---|---|
| {story title} | {criterion} | `tests/{level}/test_{x}.py` | `test_{x}_{y}` | ✅ / ❌ / ⚠️ missing |

---

## Edge Cases to Always Test

For any non-trivial activity, the Tester agent must include tests for:

- [ ] Empty input / null values
- [ ] Input at schema boundary (min/max values)
- [ ] Invalid input types (wrong type, wrong format)
- [ ] Duplicate submission
- [ ] Concurrent access (if applicable)
- [ ] Network/service unavailability (mocked)
- [ ] Partial failure (some steps succeed, some fail)
- [ ] Retry behaviour (does retry produce consistent results?)

---

## Tester Agent Instructions

When the Tester agent runs the Validate activity:

1. Run `test_cmd` from manifest
2. Parse output: extract pass count, fail count, coverage %
3. Map failures back to Stories (which acceptance criterion failed?)
4. Score against Validate rubric (see RUBRICS.md)
5. Write critique: for each failure, explain what failed and suggest fix
6. If gate fails: populate `previous_critique` for Developer agent retry context
7. Output: TestReport artifact with score, coverage, failure map, critique

---

## Notes

- Tests are evidence, not decoration. An untested Story is an incomplete Story.
- The Tester agent does not write production code. It writes tests and reports.
- Test failures are not failures of the Validate activity — they are signals to the Implement activity to retry.
- Coverage numbers without passing tests are meaningless. Pass rate is weighted higher than coverage.
