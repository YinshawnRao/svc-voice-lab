#!/usr/bin/env python3
"""Small tensor probe, not a model or audio benchmark."""
import json
import time
import argparse
import torch
from common import ROOT

start = time.monotonic()
parser = argparse.ArgumentParser()
parser.add_argument("--output", default="reports/evidence/mps-probe-latest.json")
args = parser.parse_args()
output = (ROOT / args.output).resolve()
if not output.is_relative_to((ROOT / "reports/evidence").resolve()):
    raise SystemExit("Output must stay under reports/evidence/")
result = {"torch": torch.__version__, "mps_built": torch.backends.mps.is_built(),
          "mps_available": torch.backends.mps.is_available(), "cuda_available": torch.cuda.is_available(),
          "cuda_version": torch.version.cuda, "scope": "512x512 fp32 tensor matmul only"}
if result["mps_available"]:
    torch.manual_seed(20261016)
    a = torch.randn((512, 512), device="mps")
    b = a @ a.T
    torch.mps.synchronize()
    result.update(device="mps", finite=bool(torch.isfinite(b).all().item()),
                  current_allocated_bytes=torch.mps.current_allocated_memory(),
                  driver_allocated_bytes=torch.mps.driver_allocated_memory())
else:
    result.update(device="cpu", note="MPS may be hidden by execution sandbox; repeat in authorized host context")
result["elapsed_seconds"] = round(time.monotonic() - start, 3)
output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
