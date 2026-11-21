"""OSパッケージ一覧をRenovateが更新対象として認識できることを検証する。"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "os-packages" / "nucbox-g3" / "apt-packages.txt"
PACKAGE_PATTERN = re.compile(r"(?P<name>[a-z0-9][a-z0-9+.-]*)=(?P<version>\S+)")


class OsPackageManifestTests(unittest.TestCase):
    def test_nucbox_apt_manifest_is_sorted_and_pinned(self):
        packages = [
            line
            for line in MANIFEST.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        ]

        self.assertTrue(packages)
        self.assertEqual(packages, sorted(packages, key=str.casefold))
        self.assertTrue(all(PACKAGE_PATTERN.fullmatch(line) for line in packages))
        self.assertEqual(
            len({line.split("=", maxsplit=1)[0] for line in packages}),
            len(packages),
        )

    def test_renovate_tracks_nucbox_packages_in_debian_trixie(self):
        config = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        managers = config["customManagers"]
        manager = next(
            item
            for item in managers
            if item["managerFilePatterns"]
            == [r"/^os-packages\/nucbox-g3\/apt-packages\.txt$/"]
        )

        self.assertEqual(manager["datasourceTemplate"], "deb")
        self.assertEqual(manager["versioningTemplate"], "deb")
        self.assertEqual(manager["depTypeTemplate"], "apt")

        apt_rule = next(
            rule
            for rule in config["packageRules"]
            if rule.get("matchDepTypes") == ["apt"]
        )
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
