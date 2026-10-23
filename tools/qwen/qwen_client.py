#!/usr/bin/env python3
"""Send a proposal prompt to an OpenAI-compatible chat endpoint.

The host and model come from the environment. This file does not name either.

  QWEN_BASE_URL   API root, including the /v1 prefix (required)
  QWEN_MODEL      model id (required)
  QWEN_API_KEY    optional bearer token

Outputs are proposals. The process does not commit, merge, or write a ROM.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROMPTS = {
    "function-naming": ROOT / "prompts" / "function_naming.md",
    "crash-triage": ROOT / "prompts" / "crash_triage.md",
    "doc-draft": ROOT / "prompts" / "doc_draft.md",
    "test-review": ROOT / "prompts" / "test_output_review.md",
}

BANNER = (
    "PROPOSAL ONLY. Do not merge this output. It has not been verified in-game. "
    "Do not emit ROM bytes or extracted assets.\n\n"
)


def env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(
            f"{name} is not set. Set the OpenAI-compatible base URL and model "
            "in the environment. See tools/qwen/README.md."
        )
    return value


def load_input(path: Path | None) -> str:
    if path is None:
        return sys.stdin.read()
    return path.read_text(encoding="utf-8")


def build_request(task: str, user_text: str) -> dict:
    base = env_required("QWEN_BASE_URL").rstrip("/")
    model = env_required("QWEN_MODEL")
    system = PROMPTS[task].read_text(encoding="utf-8").strip()
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
    }
    url = base + "/chat/completions"
    return {"url": url, "body": body}


def post_chat(url: str, body: dict) -> str:
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("QWEN_API_KEY", "").strip()
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"request to {url} failed: {exc.reason}") from exc
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(f"response from {url} has no choices[0].message.content") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=sorted(PROMPTS))
    parser.add_argument("--input", type=Path, help="text file to send; default stdin")
    parser.add_argument("--out", type=Path, help="write the proposal here; default stdout")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the request JSON and do not contact the endpoint",
    )
    args = parser.parse_args()

    user_text = load_input(args.input)
    if not user_text.strip():
        raise SystemExit("empty input")
    request = build_request(args.task, user_text)
    if args.dry_run:
        text = json.dumps(request, indent=2)
    else:
        text = BANNER + post_chat(request["url"], request["body"])
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
