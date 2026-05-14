# Gitignore Cleanup Plan

## TL;DR
> Update `.gitignore` to properly exclude build artifacts, generated outputs, and temp files while preserving tracked source files and the `tests/` directory. Optionally untrack currently-tracked generated files from the git index.
>
> **Deliverables**:
> - Rewritten `.gitignore` with root-anchored patterns
> - Optionally untracked: `output.xlsx`, `run_config_temp.json`
>
> **Estimated Effort**: Quick
> **Parallel Execution**: NO - sequential (audit → update → verify)
> **Critical Path**: Audit → Pattern Update → Verify

---

## Context

### Original Request
Clean up `.gitignore` for the Huawei Network Log Screenshot Generator Python project. Stop build artifacts and temp files from showing up in `git status`.

### Interview Summary
**Key Decisions**:
- `testclaude/` → temp dir → IGNORE (root-anchored)
- Root-level `test_*.py`, `verify_*.py` → temp scripts → IGNORE (root-anchored)
- `template.xlsx`, `output.xlsx` → generated outputs → IGNORE (like `.docx`)

### Metis Review
**Identified Gaps** (addressed):
- **Unanchored patterns risk**: `test_*.py` without `/` would ignore `tests/test_*.py`. Fix: use `/test_*.py`
- **Dead exception**: `!CLAUDE.md` under `*.txt` is meaningless (`.md` ≠ `.txt`). Fix: remove or relocate
- **Tracked file gotcha**: `output.xlsx` is tracked+modified; `.gitignore` alone won't hide it. Fix: separate `git rm --cached` step
- **Untrack semantics**: "from git history" unclear whether `git rm --cached` or history rewrite. Fix: default to `git rm --cached` only

---

## Work Objectives

### Core Objective
Rewrite `.gitignore` with explicit, root-anchored patterns that hide build artifacts, generated files, and temp scripts/directories while keeping `tests/`, `docs/`, and source code tracked.

### Concrete Deliverables
- Updated `.gitignore` file
- Optionally untracked generated files from git index

### Definition of Done
- `git status` no longer shows build artifacts as untracked
- `git check-ignore -v tests/test_putpnginword.py` returns no match
- `git check-ignore -v test_pipeline.py` returns a match

### Must Have
- Build artifacts: `build/`, `dist/`, `dist_nuitka/`, `*.dist/`, `*.spec`, `installer.iss`
- Generated outputs: `*.xlsx` (like `*.docx`), `output.xlsx`, `template.xlsx`
- Temp scripts (root-only): `/test_*.py`, `/verify_*.py`, `/tiny_test.py`
- Temp dir (root-only): `/testclaude/`
- Standard Python: `.pytest_cache/`, `.egg-info/`, `*.egg`, `.venv/`, `venv/`, `env/`, `.env`
- Standard IDE: `.vscode/`, `.idea/`
- OS files: `.DS_Store`, `Thumbs.db`

### Must NOT Have (Guardrails)
- Do NOT add patterns that match `tests/` directory
- Do NOT use `git filter-branch` or history rewriting without explicit user confirmation
- Do NOT delete local files when untracking (use `--cached` only)
- Do NOT modify any source code, README, or documentation files
- Do NOT create commits (user said "no commits (just plan)")

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO
- **Automated tests**: None
- **Agent-Executed QA**: MANDATORY - every task includes `git check-ignore` and `git status` validation

### QA Policy
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.
- **Git verification**: Use Bash (`git check-ignore -v`, `git status --short`)

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Sequential - audit, update, verify):
├── Task 1: Audit current .gitignore behavior
├── Task 2: Rewrite .gitignore with anchored patterns
└── Task 3: Optionally untrack generated files from git index
```

### Dependency Matrix
- Task 2 depends on Task 1 (audit informs what to fix)
- Task 3 is optional and independent of Task 2 (can run after)

---

## TODOs

- [x] 1. Audit current `.gitignore` behavior

  **What to do**:
  - Run `git check-ignore` against key files to verify current behavior
  - Document which tracked files would break if patterns were unanchored
  - List currently tracked files that should be untracked

  **Must NOT do**:
  - Do not modify `.gitignore` in this task
  - Do not untrack any files yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: Simple bash commands, no domain expertise needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: None
  - **Blocks**: Task 2

  **References**:
  - `git check-ignore` docs: https://git-scm.com/docs/git-check-ignore
  - `.gitignore` syntax: https://git-scm.com/docs/gitignore#_pattern_format

  **Acceptance Criteria**:
  - [x] `git check-ignore -v tests/test_putpnginword.py` → no match
  - [x] `git check-ignore -v process_network_logs.py` → no match
  - [x] `git check-ignore -v requirements.txt` → no match
  - [x] `git check-ignore -v output.xlsx` → no match (currently tracked, not ignored)
  - [x] List of files to untrack documented (e.g., `output.xlsx`, `run_config_temp.json`)

  **QA Scenarios**:
  ```
  Scenario: Verify tests/ directory is NOT ignored
    Tool: Bash
    Steps:
      1. Run `git check-ignore -v tests/test_putpnginword.py`
    Expected Result: Command exits with code 1 (no match), empty output
    Evidence: .sisyphus/evidence/task-1-tests-not-ignored.txt

  Scenario: Verify proposed patterns would match intended files
    Tool: Bash
    Steps:
      1. Run `git check-ignore -v --no-index -f --stdin`
         Input: output.xlsx, template.xlsx, build/, test_pipeline.py, testclaude/
    Expected Result: Each pattern matches the proposed ignore rules
    Evidence: .sisyphus/evidence/task-1-pattern-matching.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-1-tests-not-ignored.txt`
  - [ ] `task-1-pattern-matching.txt`
  - [ ] `task-1-files-to-untrack.txt`

  **Commit**: NO

- [x] 2. Rewrite `.gitignore` with anchored patterns

  **What to do**:
  - Replace current `.gitignore` with a clean, well-organized version
  - Use root-anchored patterns (`/pattern`) for root-level files only
  - Group patterns into logical sections with comments
  - Remove dead/unnecessary exceptions (`!CLAUDE.md`)
  - Keep existing protections: `!requirements.txt`, `screenshots/`, `removeddevicetest/`, `logs/`, `*.png`, `*.zip`, `*.docx`, `~$*.tmp`, `example_doc/`

  **Must NOT do**:
  - Do NOT add patterns that match `tests/` or any subdirectory source files
  - Do NOT modify any tracked source files
  - Do NOT create commits

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: File text replacement, no domain expertise needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 1 (audit results)
  - **Blocks**: Task 3

  **Acceptance Criteria**:
  - [ ] `.gitignore` has sections: Python cache, Build artifacts, Generated outputs, Temp scripts, Temp directories, Environment, IDE, OS files
  - [ ] `!requirements.txt` exception preserved
  - [ ] No `!CLAUDE.md` exception under `*.txt`
  - [ ] `/test_*.py` is anchored (not `test_*.py`)
  - [ ] `/verify_*.py` is anchored
  - [ ] `*.xlsx` added (like existing `*.docx`)

  **QA Scenarios**:
  ```
  Scenario: Verify tests/ is still not ignored after update
    Tool: Bash
    Steps:
      1. Run `git check-ignore -v tests/test_putpnginword.py`
    Expected Result: exit code 1, no match
    Evidence: .sisyphus/evidence/task-2-tests-not-ignored-after.txt

  Scenario: Verify root test files are ignored
    Tool: Bash
    Steps:
      1. Run `git check-ignore -v test_pipeline.py`
    Expected Result: Matches `/test_*.py` pattern
    Evidence: .sisyphus/evidence/task-2-test-pipeline-ignored.txt

  Scenario: Verify testclaude/ is ignored
    Tool: Bash
    Steps:
      1. Run `git check-ignore -v testclaude/README.md`
    Expected Result: Matches `/testclaude/` pattern
    Evidence: .sisyphus/evidence/task-2-testclaude-ignored.txt

  Scenario: Verify xlsx files are ignored
    Tool: Bash
    Steps:
      1. Run `git check-ignore -v output.xlsx`
      2. Run `git check-ignore -v template.xlsx`
    Expected Result: Both match `*.xlsx` pattern
    Evidence: .sisyphus/evidence/task-2-xlsx-ignored.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-2-tests-not-ignored-after.txt`
  - [ ] `task-2-test-pipeline-ignored.txt`
  - [ ] `task-2-testclaude-ignored.txt`
  - [ ] `task-2-xlsx-ignored.txt`

  **Commit**: NO

- [x] 3. Optionally untrack generated files from git index

  **What to do**:
  - Stop tracking currently-tracked generated files using `git rm --cached` (keeps local files)
  - Target files: `output.xlsx`, `run_config_temp.json`, and any other tracked generated files identified in Task 1
  - Do NOT modify `.gitignore` in this step (already done in Task 2)
  - Do NOT delete local files

  **Must NOT do**:
  - Do NOT use `git filter-branch` or rewrite history
  - Do NOT delete files from working tree (no `--force`)
  - Do NOT untrack source code or critical project files
  - Do NOT create a commit (user said no commits)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: Simple git commands, no domain expertise needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 2
  - **Blocks**: None

  **References**:
  - `git rm --cached` docs: https://git-scm.com/docs/git-rm#Documentation/git-rm.txt---cached

  **Acceptance Criteria**:
  - [ ] `git rm --cached output.xlsx` → file still in working tree, no longer tracked
  - [ ] `git rm --cached run_config_temp.json` → file still in working tree, no longer tracked
  - [ ] `git status --short` shows `D` (deleted from index) but file still exists locally
  - [ ] `git status` does NOT show `output.xlsx` as modified (after `.gitignore` update)

  **QA Scenarios**:
  ```
  Scenario: Untrack output.xlsx without deleting local file
    Tool: Bash
    Steps:
      1. Verify `output.xlsx` exists locally: `Test-Path output.xlsx` → True
      2. Run `git rm --cached output.xlsx`
      3. Verify `output.xlsx` still exists locally: `Test-Path output.xlsx` → True
      4. Run `git status --short` and confirm `D output.xlsx` (deleted from index only)
    Expected Result: File untracked but preserved locally
    Evidence: .sisyphus/evidence/task-3-untrack-output.txt

  Scenario: Untracked file is ignored by .gitignore
    Tool: Bash
    Steps:
      1. After `git rm --cached output.xlsx`
      2. Run `git status --short`
    Expected Result: `output.xlsx` does NOT appear in untracked files (it's ignored by `.gitignore`)
    Evidence: .sisyphus/evidence/task-3-ignored-after-untrack.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-3-untrack-output.txt`
  - [ ] `task-3-ignored-after-untrack.txt`

  **Commit**: NO

---

## Final Verification Wave

- [x] F1. **Full Pattern Compliance Audit** — `quick`
  Run `git check-ignore` against representative files from each category:
  - Tracked source: `process_network_logs.py`, `requirements.txt`, `tests/test_putpnginword.py` → must NOT be ignored
  - Generated: `output.xlsx`, `template.xlsx`, `test_pipeline.py`, `testclaude/README.md` → must be ignored
  - Build artifacts: `build/`, `dist/`, `*.spec` → must be ignored
  Output: Pass/fail per category

- [x] F2. **Git Status Cleanliness Check** — `quick`
  Run `git status` and verify:
  - No build artifacts in untracked files
  - No generated files (.xlsx, .tmp) in untracked files
  - No test/verify scripts in untracked files
  - No testclaude/ directory in untracked files
  Output: `Clean / Issues found: [list]`

---

## Commit Strategy

No commits allowed per user's request. Plan only.

If user later decides to commit the `.gitignore` update and untracking:
- Commit message: `chore(gitignore): update ignores for build artifacts and temp files`
- Files: `.gitignore`
- Separate commit for untracking: `chore(git): untrack generated output and temp files`

---

## Success Criteria

### Verification Commands
```bash
# Tests directory still tracked
git check-ignore -v tests/test_putpnginword.py
# Expected: exit code 1 (not ignored)

# Generated files ignored
git check-ignore -v output.xlsx
git check-ignore -v template.xlsx
git check-ignore -v test_pipeline.py
# Expected: exit code 0 with pattern match

# Build artifacts ignored
git check-ignore -v build/
git check-ignore -v installer.iss
# Expected: exit code 0 with pattern match

# Git status clean
# Expected: No build artifacts, no generated files, no temp scripts in untracked
```

### Final Checklist
- [x] All build artifacts properly ignored
- [x] All generated outputs (.xlsx) properly ignored
- [x] All temp scripts (root-level test_*, verify_*) properly ignored
- [x] `testclaude/` directory properly ignored
- [x] `tests/` directory NOT ignored
- [x] `requirements.txt` NOT ignored
- [x] Tracked generated files optionally untracked from index
- [x] No local files deleted during untracking
- [x] No commits created
