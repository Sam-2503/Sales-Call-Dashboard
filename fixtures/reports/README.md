# Synthetic report fixtures

These files are synthetic examples used by the frontend mocks and acceptance tests.
They are not real calls, customers, or transcripts. Every quote is invented.

- `full_report.json`: a complete review with findings, objections, and a follow-up draft.
- `insufficient_data_report.json`: a call too short to review.

Both were generated from `schemas/call_report.schema.json` for this checkout because the
prompt's expected fixture files were absent. `meta.pipeline_version` starts with
`synthetic-fixture` so they are easy to identify.
