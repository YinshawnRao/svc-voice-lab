#!/usr/bin/env python3
"""Plan named wheels from official PyPI, never download/execute source distributions.

This is NOT a dependency resolver. Offline pip is the final dependency check.
Use explicit name==version for reproducibility; unpinned input selects current PyPI release.
Run with the target venv Python so supported wheel tags match that environment.
"""
import argparse
import json
import urllib.request
from pip._vendor.packaging.tags import sys_tags
from pip._vendor.packaging.utils import parse_wheel_filename
from pip._vendor.packaging.specifiers import SpecifierSet
from pip._vendor.packaging.version import Version, InvalidVersion
import platform
from common import ROOT

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--allow-sdist", action="store_true", help="Plan source archives for separate review; never builds them")
    p.add_argument("packages", nargs="+")
    args = p.parse_args()
    supported = list(sys_tags())
    ranks = {tag: i for i, tag in enumerate(supported)}
    result = []
    for spec in args.packages:
        parts = spec.split("==")
        name = parts[0]
        endpoint = f"https://pypi.org/pypi/{name}/" + (parts[1] + "/" if len(parts) > 1 else "") + "json"
        with urllib.request.urlopen(endpoint, timeout=40) as r:
            data = json.load(r)
        if len(parts) == 1:
            compatible = []
            for version, files in data.get("releases", {}).items():
                try:
                    v = Version(version)
                except InvalidVersion:
                    continue
                if v.is_prerelease or v.is_devrelease:
                    continue
                for f in files:
                    if f["packagetype"] != "bdist_wheel" or f.get("yanked"):
                        continue
                    if f.get("requires_python") and platform.python_version() not in SpecifierSet(f["requires_python"]):
                        continue
                    if parse_wheel_filename(f["filename"])[3].intersection(ranks):
                        compatible.append(v)
                        break
            if not compatible and not args.allow_sdist:
                raise SystemExit(f"No compatible wheel for {name}")
            if compatible:
                endpoint = f"https://pypi.org/pypi/{name}/{max(compatible)}/json"
                with urllib.request.urlopen(endpoint, timeout=40) as r:
                    data = json.load(r)
        info = data["info"]
        candidates = []
        for f in data["urls"]:
            if f["packagetype"] != "bdist_wheel" or f.get("yanked"):
                continue
            if f.get("requires_python") and platform.python_version() not in SpecifierSet(f["requires_python"]):
                continue
            tags = parse_wheel_filename(f["filename"])[3]
            matches = [ranks[t] for t in tags if t in ranks]
            if matches:
                candidates.append((min(matches), f))
        if not candidates and args.allow_sdist:
            for f in data["urls"]:
                if f["packagetype"] == "sdist" and not f.get("yanked") and (
                    not f.get("requires_python") or platform.python_version() in SpecifierSet(f["requires_python"])
                ):
                    candidates.append((100000, f))
        if not candidates:
            raise SystemExit(f"No compatible official wheel for {name}=={info['version']}; source build must be reviewed separately")
        f = min(candidates, key=lambda x: x[0])[1]
        license_name = info.get("license_expression") or info.get("license") or "unknown"
        if len(license_name) > 200:
            classifiers = [x for x in info.get("classifiers", []) if x.startswith("License ::")]
            license_name = "; ".join(classifiers) or f"See PyPI {name} {info['version']} license text"
        result.append({"url": f["url"], "dest": ".cache/wheels/" + f["filename"],
                       "size_bytes": f["size"], "sha256": f["digests"]["sha256"],
                       "license": license_name, "license_source": endpoint,
                       "evidence": args.evidence, "purpose": "isolated preparation environment dependency", "kind": "dependency",
                       "distribution_type": f["packagetype"]})
        path = ROOT / "reports/evidence/pypi" / f"{name}-{info['version']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"info": info, "selected_file": f}, ensure_ascii=False, indent=2) + "\n")
        print(name, info["version"], f["size"], info.get("requires_dist"), flush=True)
    path = ROOT / args.output
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("Planned bytes:", sum(x["size_bytes"] for x in result))

if __name__ == "__main__":
    main()
