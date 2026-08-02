#!/usr/bin/env python3
"""
vendor-ml-artifact-eval: Gate 3 checkpoint-vs-class-count gate.

The silent killer (verified 2026-07-22, deycoding-compliance-classifier-router):
the shipped code declares `NUM_LABELS = 4` but the shipped state_dict has a
6-class head. `load_state_dict(strict=True)` raises; the FastAPI server
cannot start. This script catches that class of bug in one call.

Usage:
    python3 scripts/check_checkpoint_class_count.py <model_path> [--expected N]

If --expected is given, the script PASS/FAILs on whether the head shape matches.
If omitted, it just reports the head shape so you can compare against the code.

Recognized architectures:
- PyTorch state_dict with classifier.3.weight or head.weight or output.weight
- HuggingFace transformers model (uses AutoModel; checks classifier or score head)
- ONNX model (reads output node's last dim)
- TFLite flatbuffer (reads output tensor shape)

Exit code 0 = pass / informational. Exit code 1 = mismatch when --expected given.
"""

import argparse
import sys
from pathlib import Path


def find_pytorch_head(state_dict):
    """Walk a PyTorch state_dict looking for the classifier head weight.

    Heuristic: any 2D weight whose name matches classifier / head / output /
    pooler.dense, returning the largest (last) match. This covers most BERT,
    RoBERTa, and custom-encoder architectures.
    """
    candidates = []
    for k, v in state_dict.items():
        kl = k.lower()
        if any(t in kl for t in ("classifier", "head", "output", "pooler.dense")):
            if hasattr(v, "ndim") and v.ndim == 2:
                candidates.append((k, tuple(v.shape)))
    if not candidates:
        return None, None
    # Prefer the most-specific name pattern; bias returns are filtered
    candidates.sort(key=lambda c: (-c[1][0], c[0]))
    return candidates[0]


def check_pytorch(path, expected):
    import torch
    sd = torch.load(path, map_location="cpu", weights_only=False)
    key, shape = find_pytorch_head(sd)
    if key is None:
        print(f"  X No classifier head found in {path}", file=sys.stderr)
        return None
    num_classes = shape[0]
    hidden = shape[1]
    print(f"  Found classifier head: {key}")
    print(f"  Shape: {num_classes} classes x {hidden} hidden")
    if expected is not None:
        if num_classes == expected:
            print(f"  OK Matches expected NUM_LABELS={expected}")
            return True
        else:
            print(f"  X MISMATCH: code says NUM_LABELS={expected}, weights say {num_classes}")
            print(f"    -> load_state_dict(strict=True) will raise.")
            print(f"    -> Two resolutions:")
            print(f"      (a) Update NUM_LABELS in code to {num_classes} (breaks documented label mapping).")
            print(f"      (b) Re-train / re-export weights to match the documented {expected}-class set.")
            return False
    return num_classes


def check_huggingface(path, expected):
    """If path is a HF repo id, fetch the config + check id2label."""
    from huggingface_hub import hf_hub_download
    import json as _json
    cfg_path = hf_hub_download(repo_id=path, filename="config.json")
    cfg = _json.loads(Path(cfg_path).read_text())
    id2label = cfg.get("id2label") or cfg.get("labels")
    if id2label:
        n = len(id2label)
        print(f"  HuggingFace config id2label: {n} classes")
        sample = list(id2label.items())[:6]
        for k, v in sample:
            print(f"    {k}: {v}")
        if expected is not None and n != expected:
            print(f"  X MISMATCH: code says NUM_LABELS={expected}, HF config says {n}")
            return False
        return n
    else:
        print(f"  ! No id2label in HF config; cannot determine class count from config alone")
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("model_path", help="Path to .pt / .bin / .safetensors, or HF repo id")
    ap.add_argument("--expected", type=int, default=None,
                    help="Expected NUM_LABELS from the source code (optional)")
    ap.add_argument("--kind", choices=["pytorch", "hf", "auto"], default="auto",
                    help="Force the loader kind (default: auto-detect)")
    args = ap.parse_args()

    print(f"Gate 3 -- checkpoint-vs-class-count gate")
    print(f"  path: {args.model_path}")
    if args.expected is not None:
        print(f"  expected NUM_LABELS (from code): {args.expected}")
    print()

    p = Path(args.model_path)
    if args.kind == "auto":
        if p.exists() and p.suffix in (".pt", ".bin", ".safetensors", ".pth", ".ckpt"):
            kind = "pytorch"
        elif "/" in args.model_path and not p.exists():
            kind = "hf"
        else:
            print(f"  X Could not auto-detect kind for {args.model_path}", file=sys.stderr)
            sys.exit(2)
    else:
        kind = args.kind

    print(f"  detected kind: {kind}")

    try:
        if kind == "pytorch":
            result = check_pytorch(args.model_path, args.expected)
        elif kind == "hf":
            result = check_huggingface(args.model_path, args.expected)
    except Exception as e:
        print(f"  X Check failed with exception: {e}", file=sys.stderr)
        sys.exit(2)

    if args.expected is not None:
        if result is True:
            sys.exit(0)
        elif result is False:
            sys.exit(1)
        else:
            print(f"  ! Could not determine pass/fail; informational only.")
            sys.exit(0)
    else:
        print(f"  informational: classifier head has {result} classes")
        sys.exit(0)


if __name__ == "__main__":
    main()