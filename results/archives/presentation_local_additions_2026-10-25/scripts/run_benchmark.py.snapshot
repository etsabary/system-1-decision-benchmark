#!/usr/bin/env python3
"""Replay the recorded Jev questions through OpenRouter Decisions, without answer feedback.

Standard library only. Dry-run by default; --execute makes paid API calls.
The private answer key is used by analyze_comparison.py, never by this runner.
"""
from __future__ import annotations
from repo_layout import repo_file

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import ssl
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.14"


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def packet(question):
    return {
        "state": question["context"],
        "questions": {"decision": {
            "type": "choice",
            "instructions": question["instructions"] + "\n\n" + question["question"],
            "criteria": {str(i): question[f"option_{i}"] for i in range(1, 6)},
        }},
    }


def prepare_tasks(questions_path, baseline_path, model):
    questions = read_csv(questions_path)
    baseline = read_csv(baseline_path)
    by_id = {r["item_id"]: r for r in baseline}
    if len(by_id) != len(baseline) or len({r["item_id"] for r in questions}) != len(questions):
        raise ValueError("Duplicate question or baseline item IDs")
    if {q["item_id"] for q in questions} != set(by_id):
        raise ValueError("Questions and historical results must have identical item IDs")
    tasks = []
    for q in questions:
        old = by_id[q["item_id"]]
        if old.get("normalized_status", old["status"]) != "ok" or old["repeat_index"] != "1":
            raise ValueError("Baseline must contain one successful first response per question")
        content = {k: q[k] for k in ("instructions", "context", "question")}
        content["options"] = [q[f"option_{i}"] for i in range(1, 6)]
        if digest(content) != q["prompt_sha256"]:
            raise ValueError(f"Question text hash mismatch: {q['item_id']}")
        if old["prompt_sha256"] != q["prompt_sha256"]:
            raise ValueError(f"Historical prompt hash mismatch: {q['item_id']}")
        native = packet(q)
        if digest({"model": old["model_requested"], **native}) != old["request_payload_sha256"]:
            raise ValueError(f"Historical native payload mismatch: {q['item_id']}")
        payload = {"model": model, **native}
        tasks.append({"item_id": q["item_id"], "prompt_sha256": q["prompt_sha256"],
                      "request_payload_sha256": digest(payload), "payload": payload})
    return tasks


def api_key(env_path):
    values = {}
    if env_path and Path(env_path).exists():
        for line in Path(env_path).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip().strip("\"'")
    return os.environ.get("OPENROUTER_API_KEY") or values.get("OPENROUTER_API_KEY", "")


def clean(value, key):
    return str(value).replace(key, "[REDACTED_API_KEY]") if key else str(value)


def ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        if Path("/etc/ssl/cert.pem").exists():
            return ssl.create_default_context(cafile="/etc/ssl/cert.pem")
        return ssl.create_default_context()


def send(payload, key, timeout):
    request = urllib.request.Request(ENDPOINT, data=canonical_bytes(payload), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": "Matched-Decision-Benchmark/1.0"})
    started = time.perf_counter()
    header_ms = None
    body = {}
    http_status = 0
    error = ""
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context()) as response:
            header_ms = (time.perf_counter() - started) * 1000
            http_status = response.status
            body = json.loads(clean(response.read().decode(), key))
            if not isinstance(body, dict):
                raise ValueError("Response is not a JSON object")
    except urllib.error.HTTPError as exc:
        http_status = exc.code
        error = f"HTTP {exc.code}: " + clean(exc.read().decode(errors="replace")[:300], key)
    except Exception as exc:
        error = clean(f"{type(exc).__name__}: {exc}", key)
        body = {}
    return {"http_status": http_status, "raw_response": body, "error_message": error,
            "headers_latency_ms": header_ms,
            "latency_ms": (time.perf_counter() - started) * 1000}


def parse_answer(response):
    answers = response.get("answers", {})
    answer = answers.get("decision", {}) if isinstance(answers, dict) else {}
    choice = str(answer.get("choice", ""))
    probabilities = answer.get("probabilities", {})
    if choice not in {"1", "2", "3", "4", "5"} or not isinstance(probabilities, dict):
        raise ValueError("Missing or invalid five-option choice")
    probs = {str(i): probabilities.get(str(i)) for i in range(1, 6)}
    if any(isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p)
           or not 0 <= p <= 1 for p in probs.values()):
        raise ValueError("Missing or invalid option probabilities")
    if abs(sum(probs.values()) - 1) > 1e-4:
        raise ValueError("Option probabilities do not sum to one")
    confidence = answer.get("confidence")
    if confidence is not None and (isinstance(confidence, bool) or
        not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1):
        raise ValueError("Invalid confidence")
    if not isinstance(response.get("model"), str) or not response["model"].strip():
        raise ValueError("Missing returned model identity")
    return choice, probs, confidence


def append_json(path, value):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def run(args):
    tasks = prepare_tasks(args.questions, args.baseline, args.model)
    only_items = getattr(args, "only_items", None)
    selected_ids = None
    if only_items:
        selected_rows = read_csv(only_items)
        selected_ids = [r["item_id"] for r in selected_rows]
        if len(set(selected_ids)) != len(selected_ids) or not set(selected_ids) <= {t["item_id"] for t in tasks}:
            raise ValueError("Follow-up selection must contain unique known item IDs")
        tasks = [t for t in tasks if t["item_id"] in set(selected_ids)]
    args.out.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out / "run_manifest.json"
    binding = {"model_requested": args.model, "endpoint": ENDPOINT, "run_id": args.run_id,
               "questions_sha256": hashlib.sha256(args.questions.read_bytes()).hexdigest(),
               "baseline_sha256": hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
               "total_questions": len(tasks), "timeout_seconds": args.timeout,
               "max_attempts_per_item": args.max_attempts, "workers": args.workers,
               "max_http_attempts": args.max_http_attempts, "cost_cap_usd": args.cost_cap,
               "selection": "Exact recorded historical IDs; one first response per item",
               "latency_definition": "latency_ms includes response body; end_to_end_latency_ms includes retries and backoff; headers_latency_ms matches the historical timer boundary"}
    if selected_ids is not None:
        binding["selection"] = "Explicit follow-up subset; original run retained separately"
        binding["selected_item_ids"] = sorted(selected_ids)
    expected_model = getattr(args, "expected_returned_model", None)
    if expected_model:
        binding["required_returned_model"] = expected_model
    if manifest_path.exists():
        if json.loads(manifest_path.read_text()) != binding:
            raise ValueError("Existing run has a different configuration; use a new output directory")
    else:
        if (args.out / "results.jsonl").exists() or (args.out / "attempts.jsonl").exists():
            raise ValueError("Cannot resume result files without a manifest")
        manifest_path.write_text(json.dumps(binding, indent=2) + "\n")
    (args.out / "requests.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in tasks))
    if not args.execute:
        print(f"DRY RUN: verified {len(tasks)} exact historical payloads; no API calls")
        return
    key = api_key(args.env_file)
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not configured")
    previous = read_jsonl(args.out / "results.jsonl")
    by_id = {t["item_id"]: t for t in tasks}
    if len({r["item_id"] for r in previous}) != len(previous):
        raise ValueError("Duplicate saved responses")
    for r in previous:
        if r["item_id"] not in by_id or r["model_requested"] != args.model or r["run_id"] != args.run_id or r["request_payload_sha256"] != by_id[r["item_id"]]["request_payload_sha256"]:
            raise ValueError("Saved response identity or input mismatch")
        if expected_model and r["status"] == "ok" and r["model_returned"] != expected_model:
            raise ValueError("Saved response does not match required model snapshot")
    done = {r["item_id"] for r in previous}
    remaining = [t for t in tasks if t["item_id"] not in done][:args.batch_size]
    attempts = read_jsonl(args.out / "attempts.jsonl")
    count = len(attempts)
    cost = sum(float(a.get("provider_cost_usd") or 0) for a in attempts)
    lock = threading.Lock()
    stopped = threading.Event()
    results = list(previous)

    def worker(task):
        nonlocal count, cost
        started = time.perf_counter()
        item_attempts = []
        final = None
        for number in range(1, args.max_attempts + 1):
            with lock:
                if stopped.is_set() or count >= args.max_http_attempts or cost >= args.cost_cap:
                    stopped.set()
                    break
                count += 1
            response = send(task["payload"], key, args.timeout)
            raw = response["raw_response"]
            reported_cost = raw.get("usage", {}).get("cost")
            attempt = {"item_id": task["item_id"], "attempt": number,
                       "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                       "provider_cost_usd": reported_cost, **response}
            with lock:
                cost += float(reported_cost or 0)
                append_json(args.out / "attempts.jsonl", attempt)
                if response["http_status"] in (400, 401, 402, 403, 404):
                    stopped.set()
            item_attempts.append(attempt)
            final = response
            if response["http_status"] == 200:
                break
            retryable = response["http_status"] in (0, 429, 500, 502, 503, 504, 524, 529)
            if not retryable or number == args.max_attempts or stopped.is_set():
                break
            time.sleep(min(2 ** (number - 1), 4))
        if final is None:
            return
        elapsed_ms = (time.perf_counter() - started) * 1000
        raw = final["raw_response"]
        status = "error"
        choice, probs, confidence = "", {}, None
        error = final["error_message"]
        if final["http_status"] == 200 and not error:
            try:
                if expected_model and raw.get("model") != expected_model:
                    stopped.set()
                    raise ValueError(f"VERSION GUARD: expected {expected_model}; returned {raw.get('model')}")
                choice, probs, confidence = parse_answer(raw)
                status = "ok"
            except ValueError as exc:
                status, error = "invalid_response", str(exc)
        row = {"run_id": args.run_id, "item_id": task["item_id"], "repeat_index": "1",
               "selected_option": choice, "reported_confidence": confidence,
               "status": status, "provider": "openrouter", "upstream_provider": raw.get("provider"),
               "model_requested": args.model, "model_returned": raw.get("model", ""),
               "prompt_mode": "native_choice", "settings_json": json.dumps({"timeout": args.timeout, "max_attempts": args.max_attempts}),
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "latency_ms": final["latency_ms"], "headers_latency_ms": final["headers_latency_ms"],
               "end_to_end_latency_ms": elapsed_ms, "attempt_count": len(item_attempts),
               "input_tokens": raw.get("usage", {}).get("input_tokens"),
               "output_tokens": raw.get("usage", {}).get("output_tokens"),
               "provider_cost_usd": sum(float(a.get("provider_cost_usd") or 0) for a in item_attempts)
                   if all(a.get("provider_cost_usd") is not None for a in item_attempts) else None,
               "http_status": final["http_status"], "api_request_id": raw.get("id", ""),
               "prompt_sha256": task["prompt_sha256"],
               "request_payload_sha256": task["request_payload_sha256"],
               "error_message": clean(error, key), "raw_response_json": json.dumps(raw, ensure_ascii=False)}
        row.update({f"probability_{i}": probs.get(str(i)) for i in range(1, 6)})
        with lock:
            append_json(args.out / "results.jsonl", row)
            results.append(row)
            if len(results) % 25 == 0 or status != "ok" or len(remaining) <= 5:
                print(f"{len(results)}/{len(tasks)} saved; status={status}; reported attempt cost=${cost:.6f}", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, t) for t in remaining]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                stopped.set()
                raise
    if results:
        with (args.out / "results_completed.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0]))
            writer.writeheader()
            writer.writerows(results)
    print(json.dumps({"saved": len(results), "expected": len(tasks),
        "valid": sum(r["status"] == "ok" for r in results), "http_attempts": count,
        "reported_attempt_cost_usd": cost, "stopped": stopped.is_set()}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, default=repo_file("data/questions_1136.csv", root=ROOT))
    parser.add_argument("--baseline", type=Path, default=repo_file("data/results_jev113.csv", root=ROOT))
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--expected-returned-model", default="typesafe/jev-1.14-20261014", help="Stop if a successful response identifies another snapshot")
    parser.add_argument("--run-id", default="jev114_new_replay")
    parser.add_argument("--out", type=Path, default=repo_file("runs/jev114_new_replay", root=ROOT))
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--only-items", type=Path, help="CSV of item_id values for a separately recorded follow-up run")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--batch-size", type=int, default=1136)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--max-http-attempts", type=int, default=2272)
    parser.add_argument("--cost-cap", type=float, default=0.25)
    args = parser.parse_args()
    if min(args.batch_size, args.workers, args.timeout, args.max_attempts, args.max_http_attempts, args.cost_cap) <= 0:
        parser.error("Execution limits must be positive")
    run(args)


if __name__ == "__main__":
    main()
