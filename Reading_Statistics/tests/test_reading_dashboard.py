import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

from Reading_Dashboard import compute_kpis, data_is_aligned, ensure_enriched
from run_pipeline import build_enriched
from src.metrics import books_per_month, pages_over_time


class ReadingDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.raw = self.directory / "raw.csv"
        self.enriched = self.directory / "enriched.csv"
        self.rows = [
            {"Book Id": "001", "Title": "Cross year", "Author": "A", "Exclusive Shelf": "read",
             "Date Added": "2025/12/29", "Date Read": "2026/01/02", "Number of Pages": "100", "My Rating": "4"},
            {"Book Id": "002", "Title": "Added later", "Author": "B", "Exclusive Shelf": " read ",
             "Date Added": "2027/01/01", "Date Read": "2026/03/01", "Number of Pages": "200", "My Rating": "5"},
            {"Book Id": "003", "Title": "Not read", "Author": "C", "Exclusive Shelf": "to-read",
             "Date Added": "2026/01/01", "Date Read": "", "Number of Pages": "300"},
        ]
        self.write_raw()

    def write_raw(self):
        pd.DataFrame(self.rows).to_csv(self.raw, index=False)

    def test_build_uses_read_date_and_read_shelf_without_network(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network called")):
            df = build_enriched(self.raw, self.enriched)
        self.assertEqual(df["Book Id"].tolist(), ["001", "002"])
        later = df.set_index("Book Id").loc["002"]
        self.assertEqual(later["Date Read"], pd.Timestamp("2026-03-01"))
        self.assertEqual(later["Date Started"], pd.Timestamp("2026-03-01"))
        self.assertTrue(pd.isna(later["average pages read per day"]))
        in_2026 = df.loc[df["Date Read"].dt.year.eq(2026)]
        self.assertEqual(compute_kpis(in_2026)["books_read"], 2)
        self.assertEqual(compute_kpis(in_2026)["total_pages"], 300)
        self.assertEqual(books_per_month(in_2026).sum(), 2)
        self.assertTrue(data_is_aligned(self.raw, self.enriched))
        pages = pages_over_time(df, pd.Timestamp("2025-12-30"), pd.Timestamp("2026-01-03"))
        self.assertGreater(pages.loc["2025-12-30"], 0)
        self.assertGreater(pages.loc["2026-01-01"], 0)

    def test_rebuild_preserves_enrichment_and_recomputes_fallbacks(self):
        df = build_enriched(self.raw, self.enriched)
        df["genre"] = ["Fantasy", "History"]
        df["genre_source"] = ["open_library_isbn", "google_books_isbn"]
        df.loc[df["Book Id"].eq("001"), "Date Started"] = pd.Timestamp("2025-12-20")
        df.to_csv(self.enriched, index=False)
        self.rows[0]["Date Read"] = "2026/01/04"
        self.rows[1]["Date Read"] = "2026/04/01"
        self.write_raw()
        df = build_enriched(self.raw, self.enriched).set_index("Book Id")
        self.assertEqual(df.loc["001", "genre"], "Fantasy")
        self.assertEqual(df.loc["001", "genre_source"], "open_library_isbn")
        self.assertEqual(df.loc["001", "Date Started"], pd.Timestamp("2025-12-20"))
        self.assertEqual(df.loc["001", "Date Finished"], pd.Timestamp("2026-01-04"))
        self.assertEqual(df.loc["002", "Date Started"], pd.Timestamp("2026-04-01"))

    def test_existing_cache_is_merged_without_scraping(self):
        pd.DataFrame([{"title": "Cross year", "author": "A", "key": "cross year a",
                       "date_started": "2025/12/28", "date_finished": "2026/01/02"}]).to_csv(
                           self.directory / "read_dates_cache.csv", index=False)
        with patch("urllib.request.urlopen", side_effect=AssertionError("network called")):
            df = build_enriched(self.raw, self.enriched).set_index("Book Id")
        self.assertEqual(df.loc["001", "Date Started"], pd.Timestamp("2025-12-28"))

    def test_explicit_cache_matching_is_offline_and_missing_cache_is_reported(self):
        with self.assertRaises(FileNotFoundError):
            build_enriched(self.raw, self.enriched, use_read_dates=True)
        pd.DataFrame([{"title": "Cross year", "author": "A", "key": "different key",
                       "date_started": "2025/12/27", "date_finished": "2026/01/02"}]).to_csv(
                           self.directory / "read_dates_cache.csv", index=False)
        with patch("urllib.request.urlopen", side_effect=AssertionError("network called")):
            df = build_enriched(self.raw, self.enriched, use_read_dates=True).set_index("Book Id")
        self.assertEqual(df.loc["001", "Date Started"], pd.Timestamp("2025-12-27"))

    def test_no_read_books_produces_an_empty_aligned_file(self):
        self.rows = [self.rows[2]]
        self.write_raw()
        df = ensure_enriched(self.raw, self.enriched)
        self.assertTrue(df.empty)
        self.assertTrue(data_is_aligned(self.raw, self.enriched))

    def test_alignment_detects_missing_extra_and_duplicate_ids(self):
        build_enriched(self.raw, self.enriched)
        original = pd.read_csv(self.enriched, dtype=str, keep_default_na=False)
        for changed in (original.iloc[:1], pd.concat([original, original.iloc[:1]]),
                        pd.concat([original, pd.DataFrame([{"Book Id": "003"}])])):
            changed.to_csv(self.enriched, index=False)
            self.assertFalse(data_is_aligned(self.raw, self.enriched))
        original.to_csv(self.enriched, index=False)
        self.assertTrue(data_is_aligned(self.raw, self.enriched))

    def test_startup_creates_missing_but_does_not_overwrite_stale_output(self):
        ensure_enriched(self.raw, self.enriched)
        self.assertTrue(self.enriched.exists())
        self.rows.append({"Book Id": "004", "Title": "New", "Author": "D", "Exclusive Shelf": "read"})
        self.write_raw()
        ensure_enriched(self.raw, self.enriched)
        self.assertFalse(data_is_aligned(self.raw, self.enriched))
        ensure_enriched(self.raw, self.enriched, force=True)
        self.assertTrue(data_is_aligned(self.raw, self.enriched))

    def test_dashboard_startup_warning_and_rebuild_button(self):
        wrapper = self.directory / "app.py"
        wrapper.write_text(
            "from pathlib import Path\n"
            "import Reading_Dashboard as app\n"
            f"app.RAW_CSV = Path({str(self.raw)!r})\n"
            f"app.ENRICHED_CSV = Path({str(self.enriched)!r})\n"
            "app.main()\n"
        )
        with patch("urllib.request.urlopen", side_effect=AssertionError("network called")):
            app = AppTest.from_file(str(wrapper), default_timeout=10).run()
            self.assertFalse(app.exception)
            self.assertTrue(self.enriched.exists())
            self.rows.append({"Book Id": "004", "Title": "New", "Author": "D", "Exclusive Shelf": "read",
                              "Date Read": "2026/05/01"})
            self.write_raw()
            app.run()
            self.assertIn("Raw and enriched data are not aligned.", " ".join(w.value for w in app.warning))
            next(button for button in app.button if button.label == "Re-run from raw data").click().run()
            next(button for button in app.button if button.label == "Yes").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(data_is_aligned(self.raw, self.enriched))

    def test_genre_button_starts_worker_and_shows_completion(self):
        wrapper = self.directory / "app.py"
        wrapper.write_text(
            "from pathlib import Path\n"
            "import Reading_Dashboard as app\n"
            f"app.RAW_CSV = Path({str(self.raw)!r})\n"
            f"app.ENRICHED_CSV = Path({str(self.enriched)!r})\n"
            "app.main()\n"
        )
        process = MagicMock()
        process.poll.return_value = 0
        process.returncode = 0
        with patch("Reading_Dashboard.subprocess.Popen", return_value=process) as launch:
            app = AppTest.from_file(str(wrapper), default_timeout=10).run()
            labels = [button.label for button in app.button]
            self.assertEqual(labels.index("Look up book genres"),
                             labels.index("Extract reading dates from Goodreads") + 1)
            next(button for button in app.button if button.label == "Look up book genres").click().run()
            next(button for button in app.button if button.label == "Look up missing books").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(launch.call_count, 1)
            self.assertIn(str(self.enriched), launch.call_args.args[0])
            self.assertIn("missing", launch.call_args.args[0])

    def test_genre_worker_locks_dashboard_until_finished(self):
        wrapper = self.directory / "app.py"
        wrapper.write_text(
            "from pathlib import Path\n"
            "import Reading_Dashboard as app\n"
            f"app.RAW_CSV = Path({str(self.raw)!r})\n"
            f"app.ENRICHED_CSV = Path({str(self.enriched)!r})\n"
            "app.main()\n"
        )
        process = MagicMock()
        process.poll.return_value = None
        app = AppTest.from_file(str(wrapper), default_timeout=10)
        app.session_state["genre_process"] = process
        progress_path = self.directory / "progress.json"
        progress_path.write_text(json.dumps({"completed": 2, "total": 5, "current": 3}))
        app.session_state["genre_progress_path"] = progress_path
        with patch("Reading_Dashboard.time.sleep"), patch("Reading_Dashboard.st.rerun", side_effect=st.stop):
            app.run()
        self.assertFalse(app.exception)
        self.assertTrue(any("temporarily locked" in item.value for item in app.info))
        self.assertIn("Looking up book 3 of 5", str(app.get("progress")[0].proto))
        self.assertFalse(app.button)

    def test_genre_dialog_all_and_cancel(self):
        wrapper = self.directory / "app.py"
        wrapper.write_text(
            "from pathlib import Path\n"
            "import Reading_Dashboard as app\n"
            f"app.RAW_CSV = Path({str(self.raw)!r})\n"
            f"app.ENRICHED_CSV = Path({str(self.enriched)!r})\n"
            "app.main()\n"
        )
        process = MagicMock()
        process.poll.return_value = 0
        process.returncode = 0
        with patch("Reading_Dashboard.subprocess.Popen", return_value=process) as launch:
            app = AppTest.from_file(str(wrapper), default_timeout=10).run()
            next(button for button in app.button if button.label == "Look up book genres").click().run()
            next(button for button in app.button if button.label == "Cancel").click().run()
            self.assertEqual(launch.call_count, 0)
            next(button for button in app.button if button.label == "Look up book genres").click().run()
            next(button for button in app.button if button.label == "Look up all books").click().run()
            self.assertEqual(launch.call_count, 1)
            self.assertIn("all", launch.call_args.args[0])

    def test_genre_worker_failure_is_visible(self):
        wrapper = self.directory / "app.py"
        wrapper.write_text(
            "from pathlib import Path\n"
            "import Reading_Dashboard as app\n"
            f"app.RAW_CSV = Path({str(self.raw)!r})\n"
            f"app.ENRICHED_CSV = Path({str(self.enriched)!r})\n"
            "app.main()\n"
        )
        process = MagicMock()
        process.poll.return_value = 1
        process.returncode = 1
        process.communicate.return_value = ("", "Lookup crashed")
        app = AppTest.from_file(str(wrapper), default_timeout=10)
        app.session_state["genre_process"] = process
        output = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
        output.write("Lookup crashed")
        app.session_state["genre_output"] = output
        app.run()
        self.assertTrue(any("Genre lookup failed" in item.value for item in app.error))
        self.assertEqual(app.code[0].value, "Lookup crashed")


if __name__ == "__main__":
    unittest.main()
