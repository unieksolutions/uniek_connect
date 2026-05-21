# RUBRICS

Quality gates for every workflow activity. Rubrics define what "good enough" means before output passes to the next activity.

**Human-readable design layer.** Machine-executable form: `config/rubrics.yaml` (generated from this document).
Filled by: **Conductor / Ticketmaster** during the Specify activity. Updated by: agents after each cycle.

---

## What Rubrics Are

A rubric is the scoring contract between an activity and its gate. It answers:
- What criteria must the output satisfy?
- How is each criterion weighted?
- What score must be reached before output passes to the customer?
- How many retries are allowed before escalating?
- What mutation strategies should be tried on failure?

Rubrics are **per activity**, not per project. Each activity in the workflow has its own rubric.

---

## Rubric Structure

```yaml
# config/rubrics.yaml — machine-executable form of this document

{activity_name}:
  threshold: 0.85          # minimum weighted score to pass gate (0.0 – 1.0)
  max_iterations: 5        # retries before escalating to human
  mutation_strategy:
    - critique_feedback    # feed previous output critique back as context
    - model_upgrade        # step up to higher model tier on next attempt
    - prompt_variation     # vary prompt temperature or framing
  criteria:
    - name: {criterion}
      weight: 0.3          # weights must sum to 1.0
      description: >
        {What the agent checks. Must be observable in the output.}
      scoring:
        1.0: {exactly what "perfect" looks like}
        0.5: {what "acceptable but incomplete" looks like}
        0.0: {what "fail" looks like}
```

---

## Activity Rubrics

Fill one section per activity in your workflow.

### Research

```yaml
research:
  threshold: 0.80
  max_iterations: 3
  mutation_strategy: [critique_feedback, prompt_variation]
  criteria:
    - name: completeness
      weight: 0.4
      description: >
        Does the Research Brief cover all relevant parts of the codebase,
        available SPI capabilities, and known constraints?
    - name: specificity
      weight: 0.4
      description: >
        Are findings specific and actionable? No vague summaries.
        Must name actual files, endpoints, models, versions.
    - name: risk_identification
      weight: 0.2
      description: >
        Are risks, blockers, and unknowns explicitly called out?
```

### Specify

```yaml
specify:
  threshold: 0.85
  max_iterations: 4
  mutation_strategy: [critique_feedback, model_upgrade]
  criteria:
    - name: epic_clarity
      weight: 0.3
      description: >
        Is the Epic title and goal unambiguous? Could any engineer
        read it and know what to build?
    - name: story_completeness
      weight: 0.4
      description: >
        Does every Story have a clear actor, action, and acceptance criterion?
        No stories with "TBD" or open-ended scope.
    - name: feasibility
      weight: 0.3
      description: >
        Is the spec achievable with the available tools, models, and
        codebase described in the Research Brief?
```

### Design

```yaml
design:
  threshold: 0.85
  max_iterations: 5
  mutation_strategy: [critique_feedback, model_upgrade, prompt_variation]
  criteria:
    - name: spec_coverage
      weight: 0.35
      description: >
        Does the DesignSpec address every Story in the Epic?
    - name: schema_validity
      weight: 0.25
      description: >
        Is the data schema valid and consistent with existing models?
        No undefined types, no circular dependencies.
    - name: api_contract
      weight: 0.25
      description: >
        Is the OpenAPI or interface contract complete and unambiguous?
    - name: decision_rationale
      weight: 0.15
      description: >
        Are Architecture Decision Records (ADRs) present for
        non-obvious design choices?
```

### Implement

```yaml
implement:
  threshold: 0.80
  max_iterations: 5
  mutation_strategy: [critique_feedback, model_upgrade]
  criteria:
    - name: spec_adherence
      weight: 0.40
      description: >
        Does the code implement the DesignSpec faithfully?
        No missing endpoints, no schema deviations.
    - name: test_coverage
      weight: 0.30
      description: >
        Are unit tests present for all non-trivial logic?
    - name: code_quality
      weight: 0.30
      description: >
        No dead code, no hardcoded values, consistent naming,
        follows CODING_RULES.md standards.
```

### Validate

```yaml
validate:
  threshold: 0.90
  max_iterations: 5
  mutation_strategy: [critique_feedback, model_upgrade]
  criteria:
    - name: test_pass_rate
      weight: 0.50
      description: >
        Percentage of test cases passing. Score = pass_count / total_count.
    - name: coverage_percentage
      weight: 0.30
      description: >
        Code coverage percentage. Target defined in TESTS.md.
    - name: no_critical_failures
      weight: 0.20
      description: >
        Zero failures in tests marked as critical. Any critical failure = 0.0.
        1.0: no critical failures. 0.0: any critical failure present.
```

### Deploy

```yaml
deploy:
  threshold: 0.90
  max_iterations: 3
  mutation_strategy: [critique_feedback]
  criteria:
    - name: health_check
      weight: 0.60
      description: >
        Service responds to health_url within 5 seconds with HTTP 200.
        1.0: healthy. 0.0: unreachable or non-200.
    - name: config_correctness
      weight: 0.40
      description: >
        All required environment variables present, no missing config.
```

### Observe

```yaml
observe:
  threshold: 0.85
  max_iterations: 5
  mutation_strategy: [critique_feedback, prompt_variation]
  criteria:
    - name: latency
      weight: 0.30
      description: >
        p95 response time within threshold defined in project goals.
    - name: error_rate
      weight: 0.40
      description: >
        Error rate (5xx / total) below threshold. Score = 1 - error_rate.
    - name: cost_efficiency
      weight: 0.30
      description: >
        Token/compute cost per operation within budget.
```

---

## BKC Promotion Threshold

Best Known Configuration is promoted when the **full cycle score** (average across all activity scores) meets the promotion threshold.

```yaml
bkc:
  promotion_threshold: 0.90   # overall cycle score to write a Playbook
  min_phases_passing: 6       # all activities must pass their gate
```

---

## Escalation Rubric

When retries are exhausted, the human receives a diagnostic. Define what that must contain:

```yaml
escalation:
  required_fields:
    - activity
    - attempt_history      # list of scores per attempt
    - models_tried         # which model tiers were used
    - last_critique        # the gate's critique on the last attempt
    - suggestion           # what the agent recommends the human do
  options_presented:
    - lower_threshold      # human can set a lower pass score
    - adjust_rubrics       # human can change criteria or weights
    - manual_approve       # human can force-pass this gate
    - abort                # human can cancel the item
```

---

## Notes

- Rubrics evolve. After each cycle, the Conductor may propose rubric adjustments based on observed score distributions.
- Criteria weights must always sum to 1.0 per activity.
- Thresholds should start conservative and be relaxed based on evidence, not assumption.
- A rubric is a **contract**: the agent knows exactly how it will be scored before it starts.
