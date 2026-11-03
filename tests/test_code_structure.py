from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class CodeStructureTests(unittest.TestCase):
    def test_organized_modules_and_compatibility_imports_match(self):
        from pulsecrawl_research.datalake import run_parquet_benchmark as old_dataset
        from pulsecrawl_research.datasets.experiments import run_parquet_benchmark
        from pulsecrawl_research.live.profiles import templates_for
        from pulsecrawl_research.live_profiles import templates_for as old_templates_for
        from pulsecrawl_research.policy.webbench import WebBenchServer
        from pulsecrawl_research.webbench import WebBenchServer as OldWebBenchServer

        self.assertIs(old_dataset, run_parquet_benchmark)
        self.assertIs(old_templates_for, templates_for)
        self.assertIs(OldWebBenchServer, WebBenchServer)

    def test_live_categories_use_public_profiles_and_build_scoped_templates(self):
        from pulsecrawl_research.live.profiles import PROFILE_DEFINITIONS, templates_for

        catalog = json.loads((ROOT / "experiments/live/catalog.json").read_text())
        self.assertEqual(
            set(PROFILE_DEFINITIONS),
            {
                "article",
                "product",
                "job",
                "notice",
                "advisory",
                "alert",
            },
        )
        for category in catalog["categories"]:
            self.assertIn(category["schemaProfile"], PROFILE_DEFINITIONS)
            sites = json.loads(
                (
                    ROOT / "experiments/live" / category["id"] / "input/sites.json"
                ).read_text()
            )
            for site in sites["sites"]:
                templates = templates_for(category["schemaProfile"], site)
                self.assertTrue(templates, site["id"])
                self.assertTrue(
                    all(
                        template["scope"]["hosts"] == site["hosts"]
                        for template in templates
                    )
                )
                self.assertTrue(
                    all(
                        template["scope"]["urlPatterns"] == site["templatePatterns"]
                        for template in templates
                    )
                )

    def test_live_supervisor_uses_every_public_category(self):
        from pulsecrawl_research.live.supervisor import (
            category_experiments,
            worker_command,
        )

        experiments = category_experiments()
        self.assertEqual(len(experiments), 5)
        self.assertIn("live-us-newspapers", experiments)
        command = worker_command(
            experiments[0], Path("/tmp/research-output"), "two-hour"
        )
        self.assertEqual(command[0], "python")
        self.assertEqual(
            command[2:5], ["pulsecrawl_research.cli", "run", experiments[0]]
        )
        self.assertIn("--phase", command)
        self.assertIn("--output-root", command)

    def test_reviewer_code_map_names_every_domain(self):
        guide = (ROOT / "src/pulsecrawl_research/README.md").read_text()
        for domain in (
            "common/",
            "policy/",
            "extraction/",
            "datasets/",
            "live/",
            "comparisons/",
        ):
            self.assertIn(domain, guide)


if __name__ == "__main__":
    unittest.main()
