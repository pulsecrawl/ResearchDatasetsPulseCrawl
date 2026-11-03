from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "src/pulsecrawl_research/tools" / f"{name}.py"
    )
    value = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


class DatasetTests(unittest.TestCase):
    def test_fictional_inputs_and_live_plan_are_separate(self):
        from urllib.parse import urlsplit
        catalog = json.loads((ROOT / "datasets/site-pattern-html/catalog.json").read_text())
        self.assertTrue(all(s["host"].endswith(".example") for s in catalog["sites"]))
        for line in (ROOT / "datasets/commerce-html/manifest.jsonl").read_text().splitlines():
            row = json.loads(line)
            self.assertTrue(urlsplit(row["scopeUrl"]).hostname.endswith(".example"))
            self.assertTrue(row["storeContext"].startswith("Fictional Store"))
        live = json.loads((ROOT / "experiments/live/catalog.json").read_text())
        self.assertEqual(sum(row["sites"] for row in live["categories"]), 75)
        commerce = json.loads(
            (ROOT / "experiments/live/general-commerce/input/sites.json").read_text()
        )
        self.assertEqual(len(commerce["sites"]), 8)
        self.assertTrue(all(not s["listingUrl"].endswith(".example") for s in commerce["sites"]))

    def test_counts_and_hashes(self):
        verifier = module("verify")
        self.assertEqual(verifier.verify_manifests(), {
            "fixed-html": 60, "site-pattern-html": 100, "commerce-html": 20,
        })
        verifier.privacy_scan()

    def test_research_metadata_and_public_package_pin(self):
        verifier = module("verify")
        metadata = verifier.verify_research_metadata()
        self.assertEqual(metadata["pulsecrawl"], "0.4.0")
        self.assertEqual(metadata["controlledExperiments"], 30)
        self.assertEqual(metadata["families"], [
            "policy-and-recovery", "template-extraction", "versioned-datasets",
        ])

    def test_reviewed_release_is_complete_and_checksum_linked(self):
        verifier = module("verify")
        evidence = verifier.verify_controlled_evidence()
        self.assertEqual(evidence["controlledExecutions"], 116)
        self.assertEqual(evidence["controlledExperimentsWithEvidence"], 27)

    def test_thesis_live_universe_release_is_complete(self):
        verifier = module("verify")
        evidence = verifier.verify_live_release()
        self.assertEqual(evidence["release"], "1.0.0")
        self.assertEqual(evidence["categories"], 5)
        self.assertEqual(evidence["sites"], 75)
        self.assertEqual(evidence["siteExecutions"], 300)
        self.assertEqual(evidence["pagesFetched"], 374395)
        self.assertEqual(evidence["publishedRows"], 68367)

    def test_every_run_has_reviewer_readable_evidence(self):
        controlled = list((ROOT / "experiments/controlled").glob("*/runs/run-*"))
        self.assertEqual(len(controlled), 116)
        for run in controlled:
            self.assertTrue((run / "README.md").is_file(), run)
            self.assertTrue((run / "measurements.csv").is_file(), run)
            resolved = json.loads((run / "resolved-experiment.json").read_text())
            if resolved["family"] == "versioned-datasets":
                self.assertEqual(len(list((run / "readable-output").glob("records*.csv"))), 1)
                self.assertEqual(len(list((run / "readable-output").glob("records*.parquet"))), 1)
        live = list((ROOT / "experiments/live").glob("*/runs/thesis-universe-*"))
        self.assertEqual(len(live), 5)
        for run in live:
            index = json.loads((run / "readable-output/output-index.json").read_text())
            self.assertEqual(
                set(index),
                {"execution-summary", "pages", "records", "site-summary", "suppressed-page-samples"},
            )
            for stem in index:
                self.assertTrue((run / "readable-output" / f"{stem}.csv").is_file(), run)
                self.assertTrue((run / "readable-output" / f"{stem}.parquet").is_file(), run)
            self.assertTrue((run / "readable-output/records-preview.csv").is_file(), run)
            self.assertTrue((run / "readable-output/pages-preview.csv").is_file(), run)

    def test_template_selection_has_a_readable_strategy_comparison(self):
        run = (
            ROOT / "experiments/controlled/url-scoped-template-selection"
            / "runs/run-001"
        )
        comparison = (run / "results-by-strategy.csv").read_text().splitlines()
        self.assertEqual(
            comparison[0],
            "strategy,pages,records,record_coverage,correct_fields,expected_fields,"
            "field_accuracy,wrong_site_records,contamination_rate",
        )
        self.assertEqual(len(comparison), 5)
        self.assertTrue(any(row.startswith("scoped,300,300,1.0,600,600,1.0,0,0.0") for row in comparison))
        self.assertTrue(any(row.startswith("unscoped,300,300,1.0,600,600,1.0,280,") for row in comparison))

        manifest = json.loads((run / "execution-manifest.json").read_text())
        self.assertEqual(manifest["outputs"]["strategyComparison"], "results-by-strategy.csv")
        guide = (run / "README.md").read_text()
        self.assertIn("## Question answered", guide)
        self.assertIn("## Controlled workload", guide)
        self.assertIn("## Result at a glance", guide)
        self.assertIn("no Parquet file is expected", guide)

    def test_release_checksum_index_excludes_test_cache(self):
        checksum_index = (
            ROOT / "experiments/releases/thesis-live-universe-v1.0.0"
            / "checksums.sha256"
        ).read_text()
        self.assertNotIn(".pytest_cache", checksum_index)

    def test_fixed_inputs_regenerate_identically(self):
        generator = module("generate_fixed_html")
        for line in (ROOT / "datasets/fixed-html/manifest.jsonl").read_text().splitlines():
            row = json.loads(line)
            number = int(row["id"].split("-")[1])
            body, engine, mappings, truth = generator.document(row["vertical"], number, row["layout"])
            self.assertEqual(body.encode(), (ROOT / "datasets/fixed-html" / row["path"]).read_bytes())
            self.assertEqual((engine, mappings, truth), (row["engine"], row["mappings"], row["truth"]))

    def test_site_pattern_inputs_regenerate_identically(self):
        generator = module("generate_site_pattern")
        folder = ROOT / "datasets/site-pattern-html"
        sites = {s["id"]: s for s in json.loads((folder / "catalog.json").read_text())["sites"]}
        for line in (folder / "manifest.jsonl").read_text().splitlines():
            row = json.loads(line)
            number = int(row["id"].rsplit("-", 1)[1])
            body, truth = generator.render_fixture(sites[row["siteId"]], number)
            self.assertEqual(body.encode(), (folder / row["path"]).read_bytes())
            self.assertEqual(truth, row["truth"])

    def test_commerce_prices_are_fictional_and_repeat_scopes(self):
        generator = module("generate_commerce")
        folder = ROOT / "datasets/commerce-html"
        entries = [json.loads(line) for line in (folder / "manifest.jsonl").read_text().splitlines()]
        self.assertEqual(len({r["scopeUrl"] for r in entries}), 10)
        sources = {source.sample_url: source for source in generator.SOURCES}
        for row in entries:
            body = generator.product_html(sources[row["scopeUrl"]], row["observation"] - 1)
            self.assertEqual(body.encode(), (folder / row["path"]).read_bytes())
            self.assertFalse(row["liveEnabled"])
            self.assertEqual(row["truth"]["current_price"], 120.0 if row["observation"] == 1 else 99.0)

    def test_storage_sample_and_reference_config(self):
        folder = ROOT / "datasets/storage"
        config = json.loads((folder / "reference-config.json").read_text())
        self.assertEqual(config["totalRows"], 1000000)
        rows = []
        for path in sorted((folder / "sample").glob("*.jsonl")):
            rows.extend(json.loads(line) for line in path.read_text().splitlines())
        self.assertEqual(len(rows), 1000)
        self.assertEqual(len({r["_url_identity"] for r in rows}), 505)
        self.assertEqual(sum(r["_is_new_url"] for r in rows), 505)
        self.assertTrue(all(128 <= len(r["body"]) <= 2048 for r in rows))
        self.assertTrue(all(r["_source_url"].startswith("https://source.example/item/") for r in rows))

    def test_storage_generator_matches_sample(self):
        try:
            import duckdb
        except ImportError:
            self.skipTest("optional pinned storage dependency is not installed")
        generator = module("generate_storage")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "new"
            manifest = generator.generate(output, 1000, 2, format="jsonl")
            self.assertEqual(manifest["expectedDistinctUrlIdentities"], 505)
            for entry in manifest["files"]:
                self.assertEqual((output / entry["path"]).read_bytes(),
                                 (ROOT / "datasets/storage/sample" / entry["path"]).read_bytes())
            with self.assertRaises(FileExistsError):
                generator.generate(output, 1000, 2)

    def test_webbench_uses_loopback_http(self):
        webbench = module("webbench")
        with webbench.WebBenchServer(webbench.WebBenchConfig(items_per_site=2, sites_per_vertical=1)) as server:
            self.assertTrue(server.base_url.startswith("http://127.0.0.1:"))
            with urlopen(server.base_url + "/robots.txt", timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"User-agent:", response.read())

    def test_execution_manifest_is_sanitized_and_checksum_linked(self):
        evidence = module("create_execution_manifest")
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            measurements = temporary_path / "measurements.csv"
            summary = temporary_path / "summary.json"
            measurements.write_text("metric,value\nbudget_violations,0\n")
            summary.write_text('{"status":"completed"}\n')
            output = temporary_path / "execution"
            manifest_path = evidence.create_manifest(
                experiment_id="execution-budget-under-concurrency",
                execution_id="example-run-001",
                output_dir=output,
                measurements=measurements,
                summary=summary,
                command=["pulsecrawl", "run", "registered-job.json"],
                status="completed",
                started_at="2026-10-13T12:00:00Z",
                completed_at="2026-10-13T12:01:00Z",
            )
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["software"]["pulsecrawl"], "0.4.0")
            self.assertEqual(manifest["experimentId"], "execution-budget-under-concurrency")
            self.assertTrue((output / "checksums.sha256").is_file())
            with self.assertRaises(ValueError):
                evidence.ensure_publishable_text(["/" + "Users/example/private/file.json"])


if __name__ == "__main__":
    unittest.main()
