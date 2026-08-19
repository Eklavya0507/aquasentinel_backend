# Backend Test Results

Validated with FastAPI `TestClient` after the final integration edits.

Passed flows:
- health endpoint
- citizen registration
- profile creation
- medical-history save
- public community report
- government registration
- government report list + review
- doctor registration
- doctor case entries
- B2 surveillance calculation
- B1 environmental model prediction
- hospitals list
- doctors list

B1 sample prediction returned `Giardiasis` with about `0.7915` top confidence for the prefilled Assam/Kamrup environmental sample. This is an environmental model prototype output, not a clinical diagnosis.
