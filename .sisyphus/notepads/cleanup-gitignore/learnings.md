## 2026-05-13 - cleanup-gitignore

### Critical Finding
1,576 tracked files were build artifacts/temp files that should have been ignored from day one. Your `.gitignore` was essentially useless.

### Root Causes
- `build/`, `dist/`, `*.dist/` directories never ignored
- `*.spec` (PyInstaller) never ignored
- Root-level temp scripts (`test_*.py`, `verify_*.py`) never ignored
- `testclaude/` directory tracked entirely
- `.xlsx` generated files not ignored

### New Patterns Added
| Pattern | Matches | Anchored? |
|---------|---------|-----------|
| `*.dist/` | run.dist/, whitelist_gui.dist/, etc. | No (safe) |
| `*.spec` | PyInstaller .spec files | No (safe) |
| `*.xlsx` | output.xlsx, template.xlsx | No (safe) |
| `/test_*.py` | test_pipeline.py, etc. | YES (root only) |
| `/verify_*.py` | verify_eof_bug.py, etc. | YES (root only) |
| `/testclaude/` | testclaude/* | YES (root only) |
| `*.bat` | build_exe.bat | No (safe) |
| `*.iss` | installer.iss | No (safe) |

### Verification Commands Used
```bash
git check-ignore --no-index -v tests/test_putpnginword.py # exit 1 = NOT ignored
git check-ignore --no-index -v output.xlsx              # exit 0 = ignored
git ls-files | Select-String '\.dist/'                   # 0 lines = clean
```

### Files Untracked
- output.xlsx, template.xlsx
- test_pipeline.py, test_removed_case.py, test_whitelist_cases.py, tiny_test.py, verify_eof_bug.py, verify_expected.py
- testclaude/ (12 files)
- *.spec (7 files)
- run.dist/, whitelist_gui.dist/, putpnginword.dist/, putpnginxlsx.dist/, log_stats.dist/
- build_exe.bat, installer.iss

### Key Lesson
Always anchor root-level patterns (`/pattern`) when targeting specific root files to avoid accidentally matching subdirectories like `tests/`.
