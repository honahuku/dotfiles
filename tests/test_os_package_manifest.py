"""OSパッケージ一覧をRenovateが更新対象として認識できることを検証する。"""

import json
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "os-packages" / "nucbox-g3" / "mise.toml"
RENOVATE_ANNOTATION = "# renovate: datasource=deb versioning=deb depType=apt"


class OsPackageManifestTests(unittest.TestCase):
    def test_nucbox_apt_manifest_is_sorted_and_pinned(self):
        text = MANIFEST.read_text(encoding="utf-8")
        config = tomllib.loads(text)
        packages = config["bootstrap"]["packages"]

        self.assertTrue(packages)
        package_pins = [
            f"{name.removeprefix('apt:')}={version}"
            for name, version in packages.items()
        ]
        self.assertEqual(package_pins, sorted(package_pins, key=str.casefold))
        self.assertTrue(all(name.startswith("apt:") for name in packages))
        self.assertTrue(all(version != "latest" for version in packages.values()))
        self.assertEqual(text.count(RENOVATE_ANNOTATION), len(packages))

    def test_renovate_tracks_nucbox_packages_in_debian_trixie(self):
        config = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        managers = config["customManagers"]
        manager = next(
            item
            for item in managers
            if item["managerFilePatterns"]
            == [r"/^os-packages\/nucbox-g3\/mise\.toml$/"]
        )

        self.assertEqual(manager["customType"], "regex")
        self.assertIn("(?<depName>", manager["matchStrings"][0])
        self.assertIn("(?<datasource>", manager["matchStrings"][0])
        self.assertIn("(?<versioning>", manager["matchStrings"][0])
        self.assertIn("(?<depType>", manager["matchStrings"][0])

        apt_rule = next(
            rule
            for rule in config["packageRules"]
            if rule.get("matchFileNames") == ["os-packages/nucbox-g3/mise.toml"]
        )
        self.assertEqual(apt_rule["matchDepTypes"], ["apt"])
        self.assertEqual(apt_rule["matchDatasources"], ["deb"])
        self.assertEqual(
            apt_rule["minimumReleaseAgeBehaviour"],
            "timestamp-optional",
        )

        registry_urls = apt_rule["registryUrls"]
        self.assertTrue(
            any(
                "suite=trixie" in url and "binaryArch=amd64" in url
                for url in registry_urls
            )
        )
        self.assertTrue(any("suite=trixie-security" in url for url in registry_urls))
