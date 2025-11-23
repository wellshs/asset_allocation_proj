<!--
SYNC IMPACT REPORT
==================
Version Change: INITIAL → 1.0.0
Rationale: Initial constitution creation for new project

Modified Principles: N/A (initial creation)
Added Sections:
  - Core Principles (3 principles: Test-First Development, Financial Accuracy, Simplicity)
  - Development Workflow
  - Governance

Removed Sections: N/A

Templates Status:
  ✅ spec-template.md - Reviewed, compatible with TDD and user story structure
  ✅ plan-template.md - Reviewed, compatible with constitution check gates
  ✅ tasks-template.md - Reviewed, compatible with test-first workflow
  ✅ checklist-template.md - Not reviewed (optional template)
  ✅ agent-file-template.md - Not reviewed (meta template)

Follow-up TODOs: None
-->

# Asset Allocation Platform Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

Test-Driven Development (TDD) is mandatory for all feature development:

- Tests MUST be written before implementation code
- Tests MUST fail initially (Red phase)
- Implementation follows to make tests pass (Green phase)
- Refactoring occurs only after tests pass (Refactor phase)
- No code may be merged without corresponding tests

**Rationale**: Financial software requires high reliability. TDD ensures correctness through verification-first design, catches edge cases early, and provides regression protection for critical financial calculations.

### II. Financial Data Accuracy (NON-NEGOTIABLE)

All financial calculations, algorithms, and data handling MUST meet rigorous accuracy standards:

- Numerical precision requirements MUST be explicitly documented for each calculation
- Backtesting results MUST be reproducible with documented parameters
- Financial formulas MUST include references to authoritative sources (academic papers, standards)
- Rounding behavior MUST be explicitly defined and tested
- Edge cases (market holidays, corporate actions, missing data) MUST be handled with documented strategies
- Investment tracking MUST maintain audit trails for all portfolio changes

**Rationale**: Financial accuracy is paramount. Incorrect calculations can lead to significant monetary losses, flawed investment decisions, and erosion of trust. Documentation and testing ensure algorithms behave correctly across all scenarios.

### III. Simplicity (Start Simple, Justify Complexity)

Favor simple, direct solutions over complex abstractions:

- Implement the minimal solution that solves the current requirement
- Avoid premature optimization and speculative features (YAGNI principle)
- Use direct implementations over frameworks unless framework necessity is justified
- Prefer explicit code over clever abstractions
- Three similar code blocks are acceptable; premature abstraction is not
- Any complexity (additional libraries, patterns, frameworks) MUST be justified in plan.md Complexity Tracking table

**Rationale**: Monorepo projects supporting backtesting, investment management, and tracking can become complex quickly. Starting simple ensures maintainability, easier debugging, and prevents over-engineering. Complexity should be added only when clearly necessary and justified.

## Development Workflow

### Test-First Workflow

All feature work follows this mandatory sequence:

1. **Specification**: Define user stories and acceptance criteria in spec.md
2. **Planning**: Create implementation plan with test strategy in plan.md
3. **Test Creation**: Write failing tests that verify requirements
4. **User Approval**: Tests reviewed and approved before implementation begins
5. **Implementation**: Write code to make tests pass
6. **Validation**: Verify all tests pass and acceptance criteria met

### Backtesting & Financial Calculations

Special requirements for algorithm and backtesting code:

- Document data sources and their limitations
- Include date ranges and market conditions in test scenarios
- Validate against known historical scenarios when possible
- Document assumptions (transaction costs, slippage, market impact)
- Include performance benchmarks in test suites

## Governance

### Amendment Process

This constitution supersedes all other development practices. To amend:

1. Proposed changes MUST be documented with rationale
2. Changes MUST include migration plan for existing code
3. Version MUST be incremented per semantic versioning:
   - **MAJOR**: Principle removal or incompatible governance changes
   - **MINOR**: New principle added or material expansion
   - **PATCH**: Clarifications, wording improvements
4. Dependent templates MUST be updated for consistency

### Compliance & Enforcement

- All feature specifications MUST reference relevant principles
- All implementation plans MUST include constitution check gates
- Code reviews MUST verify compliance with principles
- Complexity introductions MUST be justified or rejected

**Version**: 1.0.0 | **Ratified**: 2025-11-23 | **Last Amended**: 2025-11-23
