## ADDED Requirements

### Requirement: Risk-triggered Standard security review
MASE MUST require deep security review for a Standard change only when a registered attack-surface trigger or an explicit project gate requires it.

#### Scenario: Ordinary non-security Standard change
- **WHEN** a Standard change modifies persistence-neutral internal behavior and declares no security trigger
- **THEN** its plan does not add deep security review solely because the base Profile is Standard

#### Scenario: Untrusted file input
- **WHEN** a Standard change handles untrusted upload or archive parsing
- **THEN** the risk registry adds security review and related attack-surface tests

### Requirement: Independent review stopping condition
Strict independent review SHALL require one review pass and SHALL require another pass only after an objection, candidate input change or stale/invalid review evidence.

#### Scenario: Reviewer has no objection
- **WHEN** the reviewer is shown the subject and evidence and confirms no objection
- **THEN** the independent review gate is satisfied without a mandatory formal report or additional review round
