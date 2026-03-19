---
name: test
description: Run tests with automatic scope detection. Dispatch to api-tester or evidence-collector for specialized testing.
---

# Test

1. **Identify scope** - Determine what to test:
   - Changed files (git diff)
   - Related test files
   - Test configuration

2. **Run tests** - Execute relevant tests:
   ```bash
   # Python
   pytest [path/to/test_file.py]
   pytest --related-tests

   # Run all tests in directory
   pytest
   ```

3. **Analyze** - Report results and failures.

For API/E2E testing, dispatch **api-tester** subagent.
For QA with visual evidence, dispatch **evidence-collector** subagent.

Max 2 subagents at a time.
