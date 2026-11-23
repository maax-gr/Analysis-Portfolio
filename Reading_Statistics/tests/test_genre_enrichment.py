import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

import pandas as pd

from Reading_Dashboard import pages_rating_figure
from src.genre_enrichment import (
    LookupState, _normalize_isbn, enrich_dataframe_genres, enrich_genres_file,
    lookup_genre_for_book, map_subjects_to_genre, remap_saved_genres,
)


class GenreEnrichmentTests(unittest.TestCase):
    def test_isbn10_and_google_isbn_aggregate_matched_results(self):
        isbn = "9780140449136"
        self.assertEqual(_normalize_isbn("0140449132"), isbn)
        self.assertEqual(_normalize_isbn("0140449133"), "")
        self.assertEqual(_normalize_isbn("9780140449137"), "")
        volumes = {"items": [
            {"volumeInfo": {"industryIdentifiers": [{"identifier": isbn}],
                            "categories": ["Science Fiction", "Space / Exploration"]}},
            {"volumeInfo": {"industryIdentifiers": [{"identifier": isbn}],
                            "categories": ["Fantasy", "Science Fiction"]}},
            {"volumeInfo": {"industryIdentifiers": [{"identifier": "9780000000000"}],
                            "categories": ["History"]}},
        ]}
        with patch("src.genre_enrichment._google_books_lookup_by_isbn", return_value=volumes), \
             patch("src.genre_enrichment._open_library_lookup_by_isbn", return_value=None), \
             patch("src.genre_enrichment._open_library_lookup_by_title_author", return_value=None):
            result = lookup_genre_for_book("Title", "Author", "0140449132")
        self.assertEqual(result["genre_raw"], ["Science Fiction", "Space / Exploration", "Fantasy"])
        self.assertEqual(result["genre"], "Fantasy")
        self.assertEqual(result["lookup_status"], "matched")

    def test_fallback_ignores_mismatches_and_uses_open_library(self):
        google = {"items": [{"volumeInfo": {"title": "Wrong", "authors": ["Author"], "categories": ["History"]}}]}
        with patch("src.genre_enrichment._google_books_lookup_by_isbn", return_value={"items": []}) as google_isbn, \
             patch("src.genre_enrichment._google_books_lookup_by_title_author", return_value=google) as google_title, \
             patch("src.genre_enrichment._open_library_lookup_by_isbn", return_value={"subjects": ["Magic", "Dragons"]}):
            result = lookup_genre_for_book("Title", "Author", "9780140449136")
        google_isbn.assert_not_called()
        google_title.assert_not_called()
        self.assertEqual(result["genre_raw"], ["Magic", "Dragons"])
        self.assertEqual(result["genre"], "Fantasy")
        self.assertEqual(result["source"], "open_library_isbn")

    def test_open_library_does_not_accept_unrelated_first_result(self):
        from src.genre_enrichment import _open_library_lookup_by_title_author
        with patch("src.genre_enrichment._fetch_json", return_value={"docs": [
            {"title": "Wrong", "author_name": ["Someone"], "subject": ["Fantasy"]}
        ]}):
            self.assertIsNone(_open_library_lookup_by_title_author("Title", "Author"))

    def test_open_library_simplifies_title_and_requires_correct_author(self):
        from src.genre_enrichment import _open_library_lookup_by_title_author
        cases = [
            ("The Pillars of the Earth (Kingsbridge, #1)", "Ken Follett", "Pillars of the Earth"),
            ("If Anyone Builds It, Everyone Dies: Why Superhuman AI Would Kill Us All",
             "Eliezer Yudkowsky", "If Anyone Builds It, Everyone Dies"),
        ]
        for title, author, candidate_title in cases:
            with self.subTest(title=title):
                docs = {"docs": [
                    {"title": candidate_title, "author_name": ["Wrong Author"], "subject": ["Wrong"]},
                    {"title": candidate_title + " sequel", "author_name": [author], "subject": ["Wrong"]},
                    {"title": candidate_title, "author_name": [author], "subject": ["Correct"]},
                ]}
                with patch("src.genre_enrichment._fetch_json", return_value=docs) as fetch:
                    result = _open_library_lookup_by_title_author(title, author)
                self.assertEqual(result["subject"], ["Correct"])
                params = parse_qs(urlparse(fetch.call_args.args[0]).query)
                self.assertNotIn("kingsbridge", params["title"][0])
                self.assertNotIn("superhuman", params["title"][0])

    def test_open_library_prefers_exact_title_over_simplified_candidate(self):
        from src.genre_enrichment import _open_library_lookup_by_title_author
        docs = {"docs": [
            {"title": "The Story", "author_name": ["Author"], "subject": ["Simplified"]},
            {"title": "The Story: A Tale", "author_name": ["Author"], "subject": ["Exact"]},
        ]}
        with patch("src.genre_enrichment._fetch_json", return_value=docs):
            result = _open_library_lookup_by_title_author("The Story: A Tale", "Author")
        self.assertEqual(result["subject"], ["Exact"])

    def test_google_title_fallback_uses_short_title_and_requires_author(self):
        from src.genre_enrichment import _google_books_lookup_by_title_author, _google_subjects
        with patch("src.genre_enrichment._fetch_json", return_value={}) as fetch:
            _google_books_lookup_by_title_author("The Story: Subtitle (Series #1)", "Author")
        query = parse_qs(urlparse(fetch.call_args.args[0]).query)["q"][0]
        self.assertEqual(query, "intitle:the story inauthor:author")
        volumes = {"items": [
            {"volumeInfo": {"title": "Story", "authors": ["Wrong"], "categories": ["Wrong"]}},
            {"volumeInfo": {"title": "Story", "authors": ["Author"], "categories": ["Correct"]}},
        ]}
        self.assertEqual(_google_subjects(volumes, "The Story: Subtitle", "Author"), ["Correct"])

    def test_title_author_fallback_matches_and_collects_all_subjects(self):
        volumes = {"items": [
            {"volumeInfo": {"title": "Title", "authors": ["Author"], "categories": ["History"]}},
            {"volumeInfo": {"title": "Title", "authors": ["Author"], "categories": ["Travel"]}},
        ]}
        with patch("src.genre_enrichment._google_books_lookup_by_isbn", return_value={"items": []}), \
             patch("src.genre_enrichment._google_books_lookup_by_title_author", return_value=volumes), \
             patch("src.genre_enrichment._open_library_lookup_by_isbn", return_value=None), \
             patch("src.genre_enrichment._open_library_lookup_by_title_author", return_value=None):
            result = lookup_genre_for_book("Title", "Author", "9780140449136")
        self.assertEqual(result["genre_raw"], ["History", "Travel"])
        self.assertEqual(result["source"], "google_books_title_author")

    def test_open_library_title_author_precedes_google(self):
        with patch("src.genre_enrichment._open_library_lookup_by_isbn", return_value=None), \
             patch("src.genre_enrichment._open_library_lookup_by_title_author",
                   return_value={"subjects": ["Fantasy"]}), \
             patch("src.genre_enrichment._google_books_lookup_by_isbn") as google:
            result = lookup_genre_for_book("Title", "Author", "9780140449136")
        self.assertEqual(result["source"], "open_library_title_author")
        google.assert_not_called()

    def test_google_rate_limit_is_skipped_for_rest_of_run_but_errors_retry(self):
        state = LookupState()
        cache = {}
        limit = HTTPError("https://example.test", 429, "rate limited", {}, None)
        with patch("src.genre_enrichment._open_library_lookup_by_isbn", return_value=None), \
             patch("src.genre_enrichment._open_library_lookup_by_title_author", return_value=None), \
             patch("src.genre_enrichment._google_books_lookup_by_isbn", side_effect=limit) as google, \
             patch("src.genre_enrichment._google_books_lookup_by_title_author") as google_title:
            first = lookup_genre_for_book("Title", "Author", "9780140449136", cache=cache, state=state)
            second = lookup_genre_for_book("Other", "Author", cache=cache, state=state)
        self.assertEqual(first["lookup_status"], "error")
        self.assertEqual(second["lookup_status"], "error")
        self.assertEqual(cache, {})
        self.assertTrue(state.google_rate_limited)
        google.assert_called_once()
        google_title.assert_not_called()

    def test_open_library_still_runs_after_google_is_rate_limited(self):
        state = LookupState(google_rate_limited=True)
        with patch("src.genre_enrichment._open_library_lookup_by_isbn",
                   return_value={"subjects": ["Fantasy"]}) as open_lookup, \
             patch("src.genre_enrichment._google_books_lookup_by_isbn") as google:
            result = lookup_genre_for_book("Title", "Author", "9780140449136", state=state)
        self.assertEqual(result["lookup_status"], "matched")
        self.assertEqual(result["source"], "open_library_isbn")
        open_lookup.assert_called_once()
        google.assert_not_called()

    def test_failed_requests_are_errors_not_not_found_and_preserve_existing(self):
        df = pd.DataFrame([{"Title": "Title", "Author": "Author", "Exclusive Shelf": "read",
                            "ISBN13": pd.NA, "ISBN": "0140449132",
                            "genre_raw": '["Existing"]', "genre": "Fantasy", "lookup_status": "error"}])
        with patch("src.genre_enrichment._google_books_lookup_by_isbn", side_effect=URLError("offline")), \
             patch("src.genre_enrichment._google_books_lookup_by_title_author", return_value=None), \
             patch("src.genre_enrichment._open_library_lookup_by_isbn", return_value=None), \
             patch("src.genre_enrichment._open_library_lookup_by_title_author", return_value=None):
            output = enrich_dataframe_genres(df)
        self.assertEqual(output.loc[0, "lookup_status"], "error")
        self.assertEqual(output.loc[0, "genre"], "Fantasy")
        self.assertEqual(output.loc[0, "genre_raw"], '["Existing"]')

    def test_all_books_and_roundtrip(self):
        rows = [{"Book Id": str(i), "Title": f"Book {i}", "Author": "Author", "Exclusive Shelf": "read",
                 "ISBN13": pd.NA, "ISBN": "0140449132", "genre_raw": "", "genre": "", "lookup_status": ""}
                for i in range(12)]
        rows[10]["genre"] = "Already present"
        rows[10]["genre_raw"] = '["Existing"]'
        rows[10]["lookup_status"] = "matched"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "enriched.csv"
            pd.DataFrame(rows).to_csv(path, index=False)
            with patch("src.genre_enrichment.lookup_genre_for_book", return_value={
                "genre_raw": ["Sci-Fi & Fantasy", "Magic"], "genre": "Fantasy", "lookup_status": "matched",
                "source": "open_library_isbn"
            }) as lookup:
                enrich_genres_file(path)
                self.assertEqual(lookup.call_count, 11)
                self.assertEqual(lookup.call_args.args[2], "0140449132")
                enrich_genres_file(path)
                self.assertEqual(lookup.call_count, 11)
            out = pd.read_csv(path, dtype=str, keep_default_na=False)
            self.assertEqual(json.loads(out.loc[0, "genre_raw"]), ["Sci-Fi & Fantasy", "Magic"])
            self.assertEqual(out.loc[9, "genre"], "Fantasy")
            self.assertEqual(out.loc[0, "genre_source"], "open_library_isbn")
            self.assertEqual(out.loc[10, "genre"], "Already present")
            self.assertEqual(out.loc[11, "lookup_status"], "matched")

    def test_cached_matches_retain_source_and_failed_rows_are_retried(self):
        rows = [
            {"Book Id": "1", "Title": "A", "Author": "A", "Exclusive Shelf": "read",
             "lookup_status": "matched", "genre_raw": '["Existing"]', "genre_source": "google_books_isbn"},
            {"Book Id": "2", "Title": "B", "Author": "B", "Exclusive Shelf": "read",
             "lookup_status": "error", "genre_source": ""},
        ]
        with patch("src.genre_enrichment.lookup_genre_for_book", return_value={
            "genre_raw": ["Fantasy"], "genre": "Fantasy", "lookup_status": "matched",
            "source": "open_library_title_author",
        }) as lookup:
            out = enrich_dataframe_genres(pd.DataFrame(rows))
        lookup.assert_called_once()
        self.assertEqual(out.loc[0, "genre_source"], "google_books_isbn")
        self.assertEqual(out.loc[1, "genre_source"], "open_library_title_author")

    def test_previously_not_found_books_are_retried(self):
        rows = [{"Title": "The Story (Series #1)", "Author": "Author",
                 "Exclusive Shelf": "read", "lookup_status": "not_found"}]
        with patch("src.genre_enrichment.lookup_genre_for_book", return_value={
            "genre_raw": ["Fantasy"], "genre": "Fantasy", "lookup_status": "matched",
            "source": "open_library_title_author",
        }) as lookup:
            output = enrich_dataframe_genres(pd.DataFrame(rows))
        lookup.assert_called_once()
        self.assertEqual(output.loc[0, "lookup_status"], "matched")

    def test_mapping_and_plot_axes(self):
        self.assertIsNone(map_subjects_to_genre([]))
        self.assertEqual(map_subjects_to_genre(["Unclassified"]), "Other")
        self.assertEqual(map_subjects_to_genre(["Fantasy", "Crime"]), "Fantasy")
        self.assertEqual(map_subjects_to_genre(["Fantasy", "Science fiction, fantasy, horror"]), "Fantasy")
        self.assertEqual(map_subjects_to_genre(["Fiction, historical, general", "Thriller"]), "Historical Fiction")
        self.assertEqual(map_subjects_to_genre(["history", "biography"]), "Non-fiction: History")
        self.assertEqual(map_subjects_to_genre(["The self", "outer space"]), "Other")
        self.assertEqual(map_subjects_to_genre(["Science fiction", "space travel"]), "Science Fiction")
        frame = pd.DataFrame({"My Rating": [4, 5], "Number of Pages": [300, 1200]})
        for limit in (False, True):
            fig = pages_rating_figure(frame, limit)
            self.assertIsNone(fig.layout.yaxis.scaleanchor)
            self.assertEqual(fig.data[0].marker.opacity, 0.4)
            self.assertIsNone(fig.layout.width)
            self.assertIsNone(fig.layout.height)
            if limit:
                self.assertEqual(fig.layout.yaxis.range[1], 1000)

    def test_remaps_saved_subjects_without_losing_metadata(self):
        frame = pd.DataFrame([
            {"Book Id": "1", "genre_raw": json.dumps(["Fantasy", "Science fiction, fantasy, horror"]),
             "genre": "Science Fiction", "lookup_status": "matched", "genre_source": "open_library_isbn"},
            {"Book Id": "2", "genre_raw": json.dumps(["Historical fiction", "Thriller"]),
             "genre": "Crime / Mystery", "lookup_status": "matched", "genre_source": "open_library_title_author"},
            {"Book Id": "3", "genre_raw": "", "genre": "", "lookup_status": "error", "genre_source": ""},
        ])
        output = remap_saved_genres(frame)
        self.assertEqual(output["genre"].tolist(), ["Fantasy", "Historical Fiction", ""])
        self.assertEqual(output["genre_source"].tolist(), frame["genre_source"].tolist())
        self.assertEqual(output["genre_raw"].tolist(), frame["genre_raw"].tolist())

    def test_bad_saved_subjects_raise_explicit_error(self):
        frame = pd.DataFrame([{"Book Id": "123", "genre_raw": "bad json", "lookup_status": "matched"}])
        with self.assertRaisesRegex(ValueError, "123"):
            remap_saved_genres(frame)

    def test_remap_only_is_offline_and_does_not_overwrite_concurrent_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "books.csv"
            pd.DataFrame([{"Book Id": "1", "Title": "A", "Author": "B", "Exclusive Shelf": "read",
                           "genre_raw": '["Historical fiction"]', "genre": "Other",
                           "lookup_status": "matched"}]).to_csv(path, index=False)
            with patch("src.genre_enrichment.lookup_genre_for_book", side_effect=AssertionError("network")):
                enrich_genres_file(path, remap_only=True)
            self.assertEqual(pd.read_csv(path).loc[0, "genre"], "Historical Fiction")
            def change_file(df):
                path.write_text("changed")
                return df
            with patch("src.genre_enrichment.remap_saved_genres", side_effect=change_file):
                with self.assertRaisesRegex(RuntimeError, "changed during"):
                    enrich_genres_file(path, remap_only=True)
            self.assertEqual(path.read_text(), "changed")

    def test_missing_and_all_modes_and_progress(self):
        rows = [
            {"Book Id": "1", "Title": "A", "Author": "A", "Exclusive Shelf": "read",
             "genre_raw": '["Existing"]', "genre": "Fantasy", "lookup_status": "error"},
            {"Book Id": "2", "Title": "B", "Author": "B", "Exclusive Shelf": "read",
             "genre_raw": "[]", "lookup_status": "matched"},
            {"Book Id": "3", "Title": "C", "Author": "C", "Exclusive Shelf": "read",
             "genre_raw": "", "lookup_status": "not_found"},
            {"Book Id": "4", "Title": "D", "Author": "D", "Exclusive Shelf": "to-read",
             "genre_raw": "", "lookup_status": ""},
        ]
        result = {"genre_raw": ["Fantasy"], "genre": "Fantasy", "lookup_status": "matched",
                  "source": "open_library_title_author"}
        events = []
        with patch("src.genre_enrichment.lookup_genre_for_book", return_value=result) as lookup:
            enrich_dataframe_genres(pd.DataFrame(rows), progress=lambda *args: events.append(args))
            self.assertEqual([call.args[0] for call in lookup.call_args_list], ["B", "C"])
            self.assertEqual(events, [(0, 2, 0), (0, 2, 1), (1, 2, 0), (1, 2, 2), (2, 2, 0)])
            lookup.reset_mock()
            enrich_dataframe_genres(pd.DataFrame(rows), mode="all")
            self.assertEqual([call.args[0] for call in lookup.call_args_list], ["A", "B", "C"])

    def test_all_lookup_does_not_erase_existing_subjects_on_failure(self):
        frame = pd.DataFrame([{"Title": "A", "Author": "A", "Exclusive Shelf": "read",
                               "genre_raw": '["Fantasy"]', "genre": "Fantasy", "lookup_status": "matched"}])
        for status in ("error", "not_found"):
            result = {"genre_raw": [], "genre": None, "lookup_status": status, "source": None}
            with patch("src.genre_enrichment.lookup_genre_for_book", return_value=result):
                row = enrich_dataframe_genres(frame, mode="all").iloc[0]
            self.assertEqual(row["genre_raw"], '["Fantasy"]')
            self.assertEqual(row["genre"], "Fantasy")
            self.assertEqual(row["lookup_status"], "matched")

    def test_checkpoint_survives_interrupted_run_and_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "books.csv"
            pd.DataFrame([{"Book Id": str(i), "Title": str(i), "Author": "A", "Exclusive Shelf": "read"}
                          for i in range(3)]).to_csv(path, index=False)
            result = {"genre_raw": ["Fantasy"], "genre": "Fantasy", "lookup_status": "matched",
                      "source": "open_library_title_author"}
            with patch("src.genre_enrichment.lookup_genre_for_book",
                       side_effect=[result, RuntimeError("interrupted")]):
                with self.assertRaisesRegex(RuntimeError, "interrupted"):
                    enrich_genres_file(path)
            saved = pd.read_csv(path, dtype=str, keep_default_na=False)
            self.assertEqual(saved.loc[0, "genre"], "Fantasy")
            self.assertEqual(saved.loc[1, "genre"], "")
            with patch("src.genre_enrichment.lookup_genre_for_book", return_value=result) as lookup:
                enrich_genres_file(path)
                self.assertEqual(lookup.call_count, 2)

    def test_consecutive_open_library_failures_stop_after_saving(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "books.csv"
            pd.DataFrame([{"Book Id": str(i), "Title": str(i), "Author": "A", "Exclusive Shelf": "read"}
                          for i in range(5)]).to_csv(path, index=False)
            with patch("src.genre_enrichment._open_library_lookup_by_title_author", side_effect=URLError("timeout")), \
                 patch("src.genre_enrichment._google_books_lookup_by_title_author", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "three consecutive books"):
                    enrich_genres_file(path)
            saved = pd.read_csv(path, dtype=str, keep_default_na=False)
            self.assertEqual(saved.lookup_status.tolist(), ["error", "error", "error", "", ""])

    def test_network_retries_timeout_but_not_429(self):
        from src.genre_enrichment import _fetch_json
        with patch("src.genre_enrichment.time.sleep"), \
             patch("src.genre_enrichment.request.urlopen", side_effect=[URLError("timeout"), URLError("timeout")]) as urlopen:
            with self.assertRaises(URLError):
                _fetch_json("https://example.test")
            self.assertEqual(urlopen.call_count, 2)
        with patch("src.genre_enrichment.time.sleep"), \
             patch("src.genre_enrichment.request.urlopen", side_effect=HTTPError("https://example.test", 429, "limit", {}, None)) as urlopen:
            with self.assertRaises(HTTPError):
                _fetch_json("https://example.test")
            self.assertEqual(urlopen.call_count, 1)

    def test_request_rate_includes_retries_and_separate_requests(self):
        from src.genre_enrichment import _fetch_json, REQUEST_DELAY_SECONDS
        self.assertGreater(REQUEST_DELAY_SECONDS, 1.0)
        with patch("src.genre_enrichment.time.sleep") as sleep, \
             patch("src.genre_enrichment.request.urlopen",
                   side_effect=[URLError("timeout"), URLError("timeout"), URLError("timeout"), URLError("timeout")]) as urlopen:
            for _ in range(2):
                with self.assertRaises(URLError):
                    _fetch_json("https://example.test")
            self.assertEqual(urlopen.call_count, 4)
            self.assertEqual(sleep.call_args_list, [call(REQUEST_DELAY_SECONDS)] * 4)

    def test_worker_cli_progress_when_no_books_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "books.csv"
            progress = Path(folder) / "progress.json"
            pd.DataFrame([{"Book Id": "1", "Title": "A", "Author": "B", "Exclusive Shelf": "read",
                           "genre_raw": '["Fantasy"]', "lookup_status": "matched", "genre": "Fantasy"}]).to_csv(
                               path, index=False)
            script = Path(__file__).resolve().parents[1] / "src" / "genre_enrichment.py"
            run = subprocess.run([sys.executable, str(script), str(path), "--mode", "missing",
                                  "--progress-file", str(progress)], capture_output=True, text=True, timeout=20)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(progress.read_text()), {"completed": 0, "total": 0, "current": 0})


if __name__ == "__main__":
    unittest.main()
