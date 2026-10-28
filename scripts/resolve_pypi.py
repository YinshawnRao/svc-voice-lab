#!/usr/bin/env python3
"""Resolve official PyPI JSON metadata only; artifact downloads are a later audit step.

Run under the target venv. Uses pip's bundled resolvelib/packaging, installs nothing.
Source distribution build dependencies still require review and offline validation.
"""
import argparse
from dataclasses import dataclass
from functools import lru_cache
import json
import platform
import urllib.request
from pathlib import Path
from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.tags import sys_tags
from pip._vendor.packaging.utils import canonicalize_name, parse_wheel_filename
from pip._vendor.packaging.version import Version, InvalidVersion
from pip._vendor.packaging.specifiers import SpecifierSet
from pip._vendor.packaging.markers import default_environment
from pip._vendor.resolvelib import AbstractProvider, BaseReporter, Resolver
from common import ROOT

RANKS = {tag: i for i, tag in enumerate(sys_tags())}
ENV = default_environment()
CACHE = ROOT / "reports/evidence/stage2/pypi-resolution"


@lru_cache(None)
def metadata(name, version=""):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}-{version or 'index'}.json"
    if path.exists():
        return json.loads(path.read_text())
    url = f"https://pypi.org/pypi/{name}/" + (f"{version}/" if version else "") + "json"
    with urllib.request.urlopen(url, timeout=40) as response:
        data = json.load(response)
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n")
    return data


def artifact(files):
    choices = []
    for item in files:
        if item.get("yanked") or (item.get("requires_python") and platform.python_version() not in SpecifierSet(item["requires_python"])):
            continue
        if item["packagetype"] == "bdist_wheel":
            ranks = [RANKS[tag] for tag in parse_wheel_filename(item["filename"])[3] if tag in RANKS]
            if ranks:
                choices.append((min(ranks), item))
        elif item["packagetype"] == "sdist":
            choices.append((100000, item))
    return min(choices, key=lambda pair: pair[0])[1] if choices else None


@dataclass(frozen=True)
class Candidate:
    name: str
    version: Version
    extras: frozenset = frozenset()


class Provider(AbstractProvider):
    def identify(self, requirement_or_candidate):
        return canonicalize_name(requirement_or_candidate.name)

    def get_preference(self, identifier, resolutions, candidates, information, backtrack_causes):
        specs = [str(item.requirement.specifier) for item in information[identifier]]
        return (not any("==" in spec for spec in specs), identifier)

    def find_matches(self, identifier, requirements, incompatibilities):
        reqs = list(requirements[identifier])
        bad = set(incompatibilities[identifier])
        extras = frozenset(extra for req in reqs for extra in req.extras)
        versions = []
        for raw, files in metadata(identifier).get("releases", {}).items():
            try:
                version = Version(raw)
            except InvalidVersion:
                continue
            candidate = Candidate(identifier, version, extras)
            if version.is_prerelease or candidate in bad or not all(version in req.specifier for req in reqs):
                continue
            if artifact(files):
                versions.append(candidate)
        return sorted(versions, key=lambda candidate: candidate.version, reverse=True)

    def is_satisfied_by(self, requirement, candidate):
        return candidate.version in requirement.specifier and requirement.extras.issubset(candidate.extras)

    def get_dependencies(self, candidate):
        data = metadata(candidate.name, str(candidate.version))
        requirements = []
        for raw in data["info"].get("requires_dist") or []:
            req = Requirement(raw)
            if req.url:
                raise ValueError("direct dependency URL requires separate source review")
            if not req.marker or any(req.marker.evaluate({**ENV, "extra": extra}) for extra in candidate.extras | {""}):
                requirements.append(req)
        return requirements


class Reporter(BaseReporter):
    def pinning(self, candidate):
        print(f"PIN {candidate.name}=={candidate.version}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requirements", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    roots = [Requirement(line.strip()) for line in args.requirements.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]
    result = Resolver(Provider(), Reporter()).resolve(roots, max_rounds=3000)
    manifest, lock = [], []
    for name, candidate in sorted(result.mapping.items()):
        data = metadata(name, str(candidate.version))
        item = artifact(data["urls"])
        info = data["info"]
        license_name = info.get("license_expression") or info.get("license") or "unknown"
        if len(license_name) > 200:
            license_name = "; ".join(x for x in info.get("classifiers", []) if x.startswith("License ::")) or f"See PyPI {name} license text"
        manifest.append({"url": item["url"], "dest": ".cache/wheels/" + item["filename"],
                         "size_bytes": item["size"], "sha256": item["digests"]["sha256"],
                         "license": license_name, "license_source": f"https://pypi.org/pypi/{name}/{candidate.version}/json",
                         "evidence": args.evidence, "purpose": "Seed-VC isolated CLI dependency", "kind": "dependency",
                         "distribution_type": item["packagetype"]})
        lock.append(f"{name}=={candidate.version}")
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    args.lock.write_text("\n".join(lock) + "\n")
    print(f"Resolved {len(manifest)} artifacts, {sum(row['size_bytes'] for row in manifest):,} bytes; no artifacts downloaded.")
    print("Source archives requiring offline build review:", [Path(row["dest"]).name for row in manifest if row["distribution_type"] == "sdist"])


if __name__ == "__main__":
    main()
