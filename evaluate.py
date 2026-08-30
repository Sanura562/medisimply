"""
MediSimply Evaluation Script
=============================
Standalone, read-only-of-the-API evaluation harness for the dissertation's
Evaluation chapter. Calls the ALREADY-RUNNING /lookup endpoint like any
other HTTP client would - it does not import or modify app.py, rag.py, or
mcp_server/ in any way.

Gemini free-tier quota is small (~20 requests/day) and each /lookup call
costs 2-3 Gemini calls internally, so this script is deliberately careful:
  - Requires an explicit y/N confirmation before every single API call
    (skip with --yes once you've reviewed the test set and trust it).
  - Hard-caps the test set at 10 medicines - refuses to run more.
  - Resumable: results are saved to evaluation_results.json after EVERY
    medicine, and a medicine already present there is skipped (not
    re-called) on the next run.
  - On any failure (quota 429, timeout, etc.) it saves whatever partial
    results exist, prints a clear resume message, and exits cleanly -
    no raw traceback, no lost progress.

Usage:
    eval_venv/bin/python evaluate.py            # asks y/N before each call
    eval_venv/bin/python evaluate.py --yes       # no per-call prompt
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import requests
import textstat

API_URL = "http://127.0.0.1:8000"
LOOKUP_TIMEOUT_SECONDS = 150
DELAY_BETWEEN_CALLS_SECONDS = 3
MAX_MEDICINES = 10
FK_GRADE_TARGET = 6

RESULTS_JSON_PATH = Path(__file__).parent / "evaluation_results.json"
SUMMARY_CSV_PATH = Path(__file__).parent / "evaluation_summary.csv"

# name -> expected data_source(s), for reference only (not a hard gate -
# the agentic/live paths are allowed to vary run to run).
TEST_SET = [
    ("Atenolol", ["local_verified"]),
    ("Metformin", ["local_verified"]),
    ("Ibuprofen", ["local_verified"]),
    ("Naproxen", ["live_mcp_lookup"]),
    ("Combiflam", ["live_mcp_lookup", "ai_knowledge_only"]),
    ("Aten 50 Tablet", ["live_mcp_lookup"]),
    ("Becosules", ["ai_knowledge_only"]),
    ("Saridon", ["ai_knowledge_only", "live_mcp_lookup"]),
]

assert len(TEST_SET) <= MAX_MEDICINES, (
    f"Test set has {len(TEST_SET)} medicines - hard cap is {MAX_MEDICINES}. "
    "This script will not run a larger batch."
)


def word_count(text):
    return len(text.split()) if text else 0


def get_simplified_text(result):
    parts = [
        result["what_it_does"]["english"],
        result["how_to_take"]["english"],
        result["warnings_and_side_effects"]["english"],
        result["who_should_not_take"]["english"],
    ]
    return " ".join(p for p in parts if p)


def get_source_text(result):
    """
    The only grounding text the /lookup response actually exposes to a
    client is rag_sources[].text (the RAG passages that passed the
    relevance filter). For ai_knowledge_only results this is empty by
    design - there is no source text to compare against, not a bug.
    """
    rag_sources = result.get("rag_sources") or []
    if not rag_sources:
        return None
    return " ".join(s["text"] for s in rag_sources if s.get("text"))


def fidelity_check(medicine_name, simplified_text):
    """
    Regression check for the wrong-drug hallucination bugs found earlier:
    does the simplified output actually mention the drug that was searched?
    Same substring heuristic as app.py's check_drug_name_consistency, run
    independently here as an external evaluation signal.
    """
    name_token = medicine_name.strip().lower().split()[0] if medicine_name.strip() else ""
    if not name_token:
        return None
    return name_token in simplified_text.lower()


def sinhala_completeness(result):
    sections = [
        result["what_it_does"]["sinhala"],
        result["how_to_take"]["sinhala"],
        result["warnings_and_side_effects"]["sinhala"],
        result["who_should_not_take"]["sinhala"],
    ]
    return all(bool(s and s.strip()) for s in sections)


def compute_metrics(medicine_name, result):
    simplified_text = get_simplified_text(result)
    source_text = get_source_text(result)

    flesch_reading_ease = textstat.flesch_reading_ease(simplified_text)
    flesch_kincaid_grade = textstat.flesch_kincaid_grade(simplified_text)

    if source_text:
        source_words = word_count(source_text)
        simplified_words = word_count(simplified_text)
        # PROXY METRIC, NOT TRUE SARI: true SARI needs human-written
        # reference simplifications, which this project doesn't have. This
        # is only a word-count compression ratio between the retrieved
        # source passages and the generated output - labeled as such
        # throughout, never reported as "SARI".
        simplification_ratio = round(simplified_words / source_words, 3) if source_words else None
    else:
        simplification_ratio = None  # N/A - no source text to compare (ai_knowledge_only)

    return {
        "simplified_text": simplified_text,
        "source_text": source_text,
        "flesch_reading_ease": round(flesch_reading_ease, 2),
        "flesch_kincaid_grade": round(flesch_kincaid_grade, 2),
        "meets_grade_6_target": flesch_kincaid_grade <= FK_GRADE_TARGET,
        "simplification_ratio_NOT_SARI": simplification_ratio,
        "fidelity_check_pass": fidelity_check(medicine_name, simplified_text),
        "sinhala_complete": sinhala_completeness(result),
    }


def load_existing_results():
    if RESULTS_JSON_PATH.exists():
        with open(RESULTS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_results(results):
    # Refuse to let a resume-matching bug (or any other bug) silently shrink
    # already-saved progress - each completed /lookup call cost real, scarce
    # quota, so overwriting it away must be a loud failure, not a silent one.
    if RESULTS_JSON_PATH.exists():
        with open(RESULTS_JSON_PATH, "r", encoding="utf-8") as f:
            on_disk = json.load(f)
        if len(results) < len(on_disk):
            raise RuntimeError(
                f"Refusing to overwrite {RESULTS_JSON_PATH.name}: it currently has "
                f"{len(on_disk)} entries, but this save would only write {len(results)}. "
                "This would destroy already-completed (quota-costing) results."
            )

    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(SUMMARY_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "medicine_name", "expected_data_source", "actual_data_source",
            "flesch_reading_ease", "flesch_kincaid_grade", "meets_grade_6_target",
            "simplification_ratio_NOT_SARI", "fidelity_check_pass", "sinhala_complete",
        ])
        for r in results:
            m = r["metrics"]
            writer.writerow([
                r["medicine_name"],
                "|".join(r["expected_data_source"]),
                r.get("data_source", "ERROR"),
                m.get("flesch_reading_ease"),
                m.get("flesch_kincaid_grade"),
                m.get("meets_grade_6_target"),
                m.get("simplification_ratio_NOT_SARI"),
                m.get("fidelity_check_pass"),
                m.get("sinhala_complete"),
            ])


def print_table(results):
    header = f"{'#':<3} {'Medicine':<18} {'Data Source':<16} {'FK Grade':<9} {'Simp. Ratio':<12} {'Fidelity':<9}"
    print(header)
    print("-" * len(header))
    for i, r in enumerate(results, 1):
        m = r["metrics"]
        ratio = m.get("simplification_ratio_NOT_SARI")
        ratio_str = f"{ratio:.3f}" if ratio is not None else "N/A"
        fidelity = m.get("fidelity_check_pass")
        fidelity_str = "PASS" if fidelity else ("FAIL" if fidelity is False else "N/A")
        print(
            f"{i:<3} {r['medicine_name']:<18} {r.get('data_source', 'ERROR'):<16} "
            f"{m.get('flesch_kincaid_grade', 'N/A'):<9} {ratio_str:<12} {fidelity_str:<9}"
        )


def print_overall_summary(results):
    completed = [r for r in results if "metrics" in r]
    if not completed:
        print("\nNo completed results to summarize.")
        return

    grades = [r["metrics"]["flesch_kincaid_grade"] for r in completed]
    avg_grade = sum(grades) / len(grades)
    fidelity_pass_count = sum(1 for r in completed if r["metrics"]["fidelity_check_pass"])
    source_counts = {}
    for r in completed:
        ds = r.get("data_source", "ERROR")
        source_counts[ds] = source_counts.get(ds, 0) + 1

    print("\n=== Overall Summary ===")
    print(f"Medicines completed: {len(completed)} / {len(TEST_SET)}")
    print(f"Average Flesch-Kincaid grade level: {avg_grade:.2f} (target: <= {FK_GRADE_TARGET})")
    print(f"Fidelity check: {fidelity_pass_count} / {len(completed)} passed")
    print("Data source breakdown:")
    for ds, count in sorted(source_counts.items()):
        print(f"  {ds}: {count}")


def main():
    parser = argparse.ArgumentParser(description="MediSimply /lookup evaluation harness")
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip the per-medicine y/N confirmation prompt (use once you trust the test set).",
    )
    args = parser.parse_args()

    existing = load_existing_results()
    existing_by_name = {r["medicine_name"]: r for r in existing}
    results = []

    print(f"MediSimply evaluation - {len(TEST_SET)} medicines in test set (hard cap {MAX_MEDICINES}).")
    if existing_by_name:
        print(f"Found {len(existing_by_name)} already-completed result(s) in {RESULTS_JSON_PATH.name} - will skip those.\n")

    for i, (medicine_name, expected_sources) in enumerate(TEST_SET, 1):
        if medicine_name in existing_by_name:
            print(f"[{i}/{len(TEST_SET)}] {medicine_name}: already completed, skipping API call.")
            results.append(existing_by_name[medicine_name])
            continue

        print(f"[{i}/{len(TEST_SET)}] About to test: {medicine_name} (expected: {'/'.join(expected_sources)})")
        if not args.yes:
            answer = input("    Call /lookup for this medicine? [y/N]: ").strip().lower()
            if answer != "y":
                print("    Skipped by user. Stopping here (results saved so far).")
                break

        print(f"    Calling POST {API_URL}/lookup ...", end=" ", flush=True)
        try:
            response = requests.post(
                f"{API_URL}/lookup",
                json={"medicine_name": medicine_name},
                timeout=LOOKUP_TIMEOUT_SECONDS,
            )
        except requests.RequestException as e:
            print("FAILED (request error)")
            print(f"\nStopped at medicine {i}/{len(TEST_SET)} ({medicine_name}) due to: {e}")
            print(f"Partial results ({len(results)} completed) saved. Re-run to resume from here.")
            save_results(results)
            print()
            print_table(results)
            print_overall_summary(results)
            sys.exit(1)

        if response.status_code != 200:
            detail = response.text[:300]
            print(f"FAILED (HTTP {response.status_code})")
            reason = "quota exhausted (429)" if response.status_code == 429 else f"HTTP {response.status_code}"
            print(f"\nStopped at medicine {i}/{len(TEST_SET)} ({medicine_name}) due to {reason}: {detail}")
            print(f"Partial results ({len(results)} completed) saved. Re-run to resume from here.")
            save_results(results)
            print()
            print_table(results)
            print_overall_summary(results)
            sys.exit(1)

        result = response.json()
        metrics = compute_metrics(medicine_name, result)
        # "medicine_name" below is the name SEARCHED (the resume key) - keep
        # it distinct from result["medicine_name"], which is the API's own
        # resolved product display name (e.g. searching "Atenolol" can
        # resolve to "Amlopres-AT Tablet"). Merging **result AFTER this key
        # would silently overwrite it and break resume-skip matching.
        entry = {
            "medicine_name": medicine_name,
            "matched_product_name": result.get("medicine_name"),
            "expected_data_source": expected_sources,
            **{k: v for k, v in result.items() if k != "medicine_name"},
            "metrics": metrics,
        }
        results.append(entry)
        save_results(results)  # save after EVERY medicine, not just at the end
        print(f"done, data_source={result['data_source']}")

        if i < len(TEST_SET):
            time.sleep(DELAY_BETWEEN_CALLS_SECONDS)

    print()
    print_table(results)
    print_overall_summary(results)
    print(f"\nFull results: {RESULTS_JSON_PATH}")
    print(f"Summary CSV:  {SUMMARY_CSV_PATH}")


if __name__ == "__main__":
    main()
