# Contributing

Use a focused branch and include tests for behavior changes. Before opening a
change, run:

```bash
python -m pytest -q
python -m build
```

Do not commit credentials, downloaded filings, benchmark data, model outputs,
virtual environments, or machine-local paths. Keep SEC contact information in
`SEC_USER_AGENT`, and use synthetic/minimal fixtures in tests.

For changes to reported metrics or figures, include the source run identifiers,
configuration, aggregation definition, and a reproducible generation command.
