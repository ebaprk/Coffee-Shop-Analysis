# Verification notes

`PORTFOLIO_AUDIT.md` records the initial November 16, 2026 review. Its references to incorrect original charts and findings describe the version reviewed at that time. The current findings are in the notebooks and `../reports/executive_summary.md`.

From the project root, after installing the [project dependencies](../requirements.txt) in the project environment:

```bash
python audit/verify_dataset.py
python audit/run_clean_kernels.py
```

`verify_dataset.py` reads the original workbook with openpyxl, independently computes revenue using Decimal arithmetic, and reconciles ten aggregation families. It regenerates the financial and coverage reference tables and `verification_results.json`.

`run_clean_kernels.py` executes each notebook in a separate fresh kernel from the project root and checks the resulting kernel variables against those references. It refreshes executed copies, chart images, and `execution_results.json`. A failed notebook or reconciliation produces a nonzero exit code. Add `--write-notebooks` to save successful fresh outputs back into the original notebooks.

The `original_unchanged` result records whether the original notebook bytes stayed unchanged during that run; it is normally false when `--write-notebooks` refreshes outputs. Read `errors` and `reconciliation_outputs` to assess execution and financial checks.

`corrections.py`, `corrected_charts/`, and older chart filenames are retained from the original review. The current five visualization outputs use these paths:

- `charts/03_visualization-cell-04-1.png`: monthly revenue.
- `charts/03_visualization-cell-08-1.png`: store revenue.
- `charts/03_visualization-cell-11-0.png`: top 10 individual products.
- `charts/03_visualization-cell-14-1.png`: hourly transactions by store.
- `charts/03_visualization-cell-17-0.png`: product category revenue share.

`tested_environment.json` describes the environment used for verification. Regenerating these outputs checks internal agreement with the supplied workbook; it does not establish completeness of the original business records.
