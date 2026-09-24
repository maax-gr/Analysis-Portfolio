# Reading Statistics Dashboard

This project implements a small personal dashboard that visualizes reading statistics from a Goodreads CSV export. This repository follows the project specification in `SPEC_Reading_Dashboard.md` and completes Milestone M1 (repo setup + README + a minimal app that starts with a "hello" page).

## Quick start

1. Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Place your Goodreads export at:

```
data/raw_goodreads_library_export.csv
```

3. Run the Streamlit app:

```bash
streamlit run Reading_Dashboard.py
```

The app currently shows a minimal "Hello — Reading Dashboard" page (M1). Subsequent milestones will add the cleaning/enrichment pipeline and charts.

## Repository structure

- `data/` — input and generated CSVs
- `notebooks/` — exploratory notebooks
- `src/` — pure data-processing functions
- `Reading_Dashboard.py` — Streamlit entry point (UI only)
- `SPEC_Reading_Dashboard.md` — project specification

## Milestone status

- M1: Completed — repo scaffold, README, and minimal Streamlit app.
- M2–M5: Planned — see `SPEC_Reading_Dashboard.md` for details.

## Notes / Next steps

- Implement `src/cleaning.py` and `src/enrichment.py` (M2).
- Add unit tests and sample data for validation.

If you want me to proceed with M2 now, tell me and I'll scaffold the cleaning/enrichment pipeline and start implementing the metrics.
