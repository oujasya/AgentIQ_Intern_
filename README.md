# AgentIQ developer assessment

## Complete integrated solution: all 25 questions

The full runnable solution is in **[assessment_solution](assessment_solution)**.

- [Setup, API commands, and walkthrough](assessment_solution/README.md)
- [Detailed answers and coding explanations for Questions 1-25](assessment_solution/docs/ANSWERS.md)
- [Sample dataset](assessment_solution/data/sample_records.json)
- [Automated tests](assessment_solution/tests)
- [Executed walkthrough evidence](assessment_solution/examples/walkthrough.json)
- [Verification results](assessment_solution/docs/VERIFICATION.md)

```powershell
cd assessment_solution
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m pytest -q
python demo.py
python -m uvicorn agentiq.api:create_app --factory --reload
```

The integrated solution was verified with **59 passing tests**. It includes
validation, normalization, deduplication, analysis, FastAPI, SQLite, pagination,
bounded retries, explainable analysis runs, environment settings, and safe logging.

The original root `Q1.py` through `Q25.py`, JSON files, and `test_solutions.py`
are preserved as earlier exercises. Use the integrated solution's own README and
run its tests from the `assessment_solution` directory.

AI assistance: OpenAI Codex assisted with the integrated implementation,
explanations, tests, and verification. Review and understand the solution before
an assessment walkthrough.
