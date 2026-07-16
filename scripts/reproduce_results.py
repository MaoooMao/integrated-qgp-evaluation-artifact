#!/usr/bin/env python3
"""Validate the released inputs and reproduce manuscript-facing aggregates."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"


def read_csv(relative: str) -> list[dict[str, str]]:
    with (DATA / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(relative: str) -> list[dict[str, Any]]:
    rows = []
    with (DATA / relative).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "pass"}


def nearest_rank_p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def mean_ci95_six(values: list[float]) -> tuple[float, float, float]:
    if len(values) != 6:
        raise ValueError("the paired attack-mix experiment must contain six pairs")
    t_critical_df5 = 2.570581835636314
    mean = statistics.mean(values)
    half = t_critical_df5 * statistics.stdev(values) / math.sqrt(len(values))
    return mean, mean - half, mean + half


def metric(rows: list[dict[str, str]], field: str) -> dict[str, float]:
    values = [float(row[field]) for row in rows]
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p95": nearest_rank_p95(values),
    }


def q1_functional() -> dict[str, Any]:
    core = read_csv("functional/core_functional_metrics.csv")
    sidecar = read_csv("functional/sidecar_functional_metrics.csv")
    payload = read_csv("functional/payload_size_metrics.csv")
    tcp = read_csv("functional/tcp_stream_trials.csv")
    udp_profile = read_csv("functional/udp_profile_trials.csv")
    udp_boundary = read_csv("functional/udp_boundary_trials.csv")
    sidecar_keys = read_csv("functional/sidecar_key_coverage.csv")
    alice = read_jsonl("functional/functional_perf_alice.jsonl")
    bob = read_jsonl("functional/functional_perf_bob.jsonl")

    by_placement: dict[str, Any] = {}
    for name, rows in [("core_embedded", core), ("sidecar", sidecar)]:
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["traffic"]].append(row)
        assert set(grouped) == {"message", "file", "openweb"}
        assert all(len(items) == 30 and all(row["result"] == "PASS" for row in items) for items in grouped.values())
        by_placement[name] = {
            traffic: {
                "success": sum(row["result"] == "PASS" for row in items),
                "trials": len(items),
                "elapsed_ms": metric(items, "elapsed_ms"),
            }
            for traffic, items in grouped.items()
        }

    payload_groups = defaultdict(list)
    for row in payload:
        payload_groups[int(row["configured_file_bytes"])].append(row)
    assert set(payload_groups) == {1024, 4096, 65536, 1048576}
    assert all(len(rows) == 10 and all(row["result"] == "PASS" for row in rows) for rows in payload_groups.values())

    assert len(tcp) == 30
    assert all(row["sender_verdict"] == "PASS" and row["receiver_verdict"] == "PASS" for row in tcp)
    assert {int(row["signed_chunk_count"]) for row in tcp} == {8}
    assert {int(row["payload_bytes"]) for row in tcp} == {4096}
    assert len(udp_profile) == 30 and all(row["result"] == "PASS" for row in udp_profile)

    message = [
        row
        for row in alice
        if row["traffic_type"] == "message"
        and int(row["request_payload_bytes"]) in {22, 23}
        and row["verdict"] == "PASS"
    ]
    files = [
        row
        for row in alice
        if row["traffic_type"] == "file"
        and int(row["request_payload_bytes"]) in {4334, 4335}
        and row["verdict"] == "PASS"
    ]
    web = [
        row
        for row in bob
        if row["traffic_type"] == "openweb_http_request"
        and int(row["sequence"]) >= 69
        and row["verdict"] == "PASS"
    ]
    assert len(message) == len(files) == len(web) == 30
    envelope_medians = {
        "message_request_bytes": int(statistics.median(int(row["request_qgp_envelope_bytes"]) for row in message)),
        "file_request_bytes": int(statistics.median(int(row["request_qgp_envelope_bytes"]) for row in files)),
        "web_response_bytes": int(statistics.median(int(row["response_qgp_envelope_bytes"]) for row in web)),
    }
    assert envelope_medians == {
        "message_request_bytes": 7742,
        "file_request_bytes": 12050,
        "web_response_bytes": 329918,
    }

    complete_cases = {"clean_baseline", "reorder_5pct", "duplicate_chunk"}
    complete = [row for row in udp_boundary if row["case"] in complete_cases]
    incomplete = [row for row in udp_boundary if row["case"] not in complete_cases]
    assert len(complete) == len(incomplete) == 15
    assert all(int(row["verified_delivery_count"]) == 1 and int(row["application_plaintext_count"]) == 1 for row in complete)
    assert all(int(row["verified_delivery_count"]) == 0 and int(row["application_plaintext_count"]) == 0 for row in incomplete)

    assert len(sidecar_keys) == 90 and all(row["result"] == "PASS" for row in sidecar_keys)
    observed_sidecar_keys = sorted({row["transport_key_id"] for row in sidecar_keys})
    assert len(observed_sidecar_keys) == 5
    assert all(
        {row["traffic_type"] for row in sidecar_keys if row["transport_key_id"] == kid}
        == {"message", "file", "openweb"}
        for kid in observed_sidecar_keys
    )

    tcp_envelopes = [int(row["qgp_envelope_bytes"]) for row in tcp]
    udp_envelopes = [int(row["qgp_envelope_bytes"]) for row in udp_profile]
    return {
        "shared_profiles_by_placement": by_placement,
        "file_size_trials": {str(size): {"success": 10, "trials": 10} for size in sorted(payload_groups)},
        "tcp_stream": {
            "success": 30,
            "trials": 30,
            "payload_bytes": 4096,
            "signed_chunks_per_transfer": 8,
            "qgp_envelope_bytes_median": int(statistics.median(tcp_envelopes)),
            "qgp_envelope_bytes_range": [min(tcp_envelopes), max(tcp_envelopes)],
        },
        "udp_profile": {
            "success": 30,
            "trials": 30,
            "qgp_envelope_bytes_median": int(statistics.median(udp_envelopes)),
            "qgp_envelope_bytes_range": [min(udp_envelopes), max(udp_envelopes)],
        },
        "functional_table_envelope_medians": envelope_medians,
        "sidecar_multi_key": {"success": 90, "trials": 90, "used_key_ids": 5},
        "udp_receiver_boundary": {
            "complete_input_exact_once": 15,
            "complete_input_trials": 15,
            "incomplete_input_verified_deliveries": 0,
            "incomplete_input_plaintext_deliveries": 0,
            "incomplete_input_trials": 15,
        },
    }


def q2_security() -> dict[str, Any]:
    attacks = read_csv("security/fail_closed_trials.csv")
    honest = [row for row in attacks if row["case"] == "honest_baseline"]
    negatives = [row for row in attacks if row["case"] != "honest_baseline"]
    assert len(attacks) == 400 and len(honest) == 30 and len(negatives) == 370
    assert all(as_bool(row["accepted_by_response"]) for row in honest)
    assert sum(int(row["appserver_b_plaintexts_for_attack_send"]) for row in honest) == 30
    assert not any(as_bool(row["accepted_by_response"]) for row in negatives)
    assert sum(int(row["appserver_b_plaintexts_for_attack_send"]) for row in negatives) == 0
    assert all(row["trial_result"] == "PASS" for row in attacks)

    tamper = read_csv("security/post_signing_key_tamper_trials.csv")
    main = [row for row in tamper if row["campaign"] == "main"]
    recovery = [row for row in tamper if row["campaign"] == "postclean_recovery"]
    baseline = [row for row in main if row["case"] == "clean_baseline"]
    mutations = [row for row in main if row["case"] != "clean_baseline"]
    assert len(baseline) == 30 and sum(as_bool(row["accepted_by_response"]) for row in baseline) == 30
    assert len(mutations) == 150 and not any(as_bool(row["accepted_by_response"]) for row in mutations)
    assert len(recovery) == 1 and as_bool(recovery[0]["accepted_by_response"])
    mutation_counts = Counter(row["case"] for row in mutations)
    assert set(mutation_counts.values()) == {30}

    binding = read_csv("security/valid_signature_binding_trials.csv")
    controls = [row for row in binding if row["case"] in {"clean_binding", "clean_recovery"}]
    mismatches = [row for row in binding if row["case"] not in {"clean_binding", "clean_recovery"}]
    assert len(controls) == 6 and all(as_bool(row["accepted_by_response"]) for row in controls)
    assert len(mismatches) == 9 and not any(as_bool(row["accepted_by_response"]) for row in mismatches)
    assert all(row["case_result"] == "PASS" for row in binding)

    return {
        "fail_closed": {
            "honest_delivered": 30,
            "honest_trials": 30,
            "negative_delivered": 0,
            "negative_plaintext_delivered": 0,
            "negative_trials": 370,
            "negative_case_counts": dict(sorted(Counter(row["case"] for row in negatives).items())),
        },
        "post_signing_tamper": {
            "clean_accepted": 30,
            "clean_trials": 30,
            "mutations_accepted": 0,
            "mutation_trials": 150,
            "mutation_case_counts": dict(sorted(mutation_counts.items())),
            "postclean_recovery": "1/1 PASS",
        },
        "valid_signature_binding": {
            "controls_accepted": 6,
            "control_trials": 6,
            "mismatches_accepted": 0,
            "mismatch_trials": 9,
        },
    }


def q3_q4_performance() -> dict[str, Any]:
    alice = read_jsonl("functional/functional_perf_alice.jsonl")
    bob = read_jsonl("functional/functional_perf_bob.jsonl")
    alice_formal = [
        row
        for row in alice
        if row["traffic_type"] == "message"
        and int(row["request_payload_bytes"]) in {22, 23}
        and row["verdict"] == "PASS"
    ]
    bob_by_action = {row["service_action_id"]: row for row in bob}
    joined = [(row, bob_by_action[row["service_action_id"]]) for row in alice_formal]
    assert len(joined) == 30
    checkpoints = [
        ("alice_qgp_build_sign", 0, "request_qgp_build_sign_ms"),
        ("alice_encrypt_send_request", 0, "request_core_encrypt_send_ms"),
        ("bob_receive_decrypt_request", 1, "request_core_recv_decrypt_ms"),
        ("bob_qgp_verify_request", 1, "request_qgp_verify_ms"),
        ("bob_application_roundtrip", 1, "app_roundtrip_ms"),
        ("bob_qgp_build_sign_response", 1, "response_qgp_build_sign_ms"),
        ("bob_encrypt_send_response", 1, "response_core_encrypt_send_ms"),
        ("alice_receive_decrypt_response", 0, "response_core_recv_decrypt_ms"),
        ("alice_qgp_verify_response", 0, "response_qgp_verify_ms"),
    ]
    checkpoint_result = {}
    for name, side, field in checkpoints:
        values = [float(pair[side][field]) for pair in joined]
        checkpoint_result[name] = {
            "n": 30,
            "median_ms": statistics.median(values),
            "p95_ms": nearest_rank_p95(values),
        }

    raw = read_csv("performance/concurrency_trials.csv")
    summary = read_csv("performance/concurrency_summary.csv")
    assert len(raw) == 35 and len(summary) == 7
    assert Counter(int(row["clients"]) for row in raw) == Counter({1: 5, 2: 5, 5: 5, 10: 5, 20: 5, 30: 5, 50: 5})
    assert all(int(row["attempted"]) == int(row["verified_ok"]) + int(row["verified_fail"]) for row in raw)
    summary_by_clients = {int(row["clients"]): row for row in summary}
    assert all(int(summary_by_clients[c]["pass"]) == 5 for c in [1, 2, 5])
    assert int(summary_by_clients[10]["pass"]) < 5

    placement = {}
    for placement_name, relative in [
        ("sidecar", "functional/sidecar_functional_metrics.csv"),
        ("core_embedded", "functional/core_functional_metrics.csv"),
    ]:
        grouped = defaultdict(list)
        for row in read_csv(relative):
            grouped[row["traffic"]].append(row)
        placement[placement_name] = {
            traffic: {
                "n": len(rows),
                "mean_ms": statistics.mean(float(row["elapsed_ms"]) for row in rows),
                "median_ms": statistics.median(float(row["elapsed_ms"]) for row in rows),
                "p95_ms": nearest_rank_p95([float(row["elapsed_ms"]) for row in rows]),
            }
            for traffic, rows in grouped.items()
        }

    pairs = read_csv("performance/attack_mix_pairs.csv")
    phases = read_csv("performance/attack_mix_phase_rows.csv")
    assert len(pairs) == 6 and len(phases) == 12
    attack_rows = [row for row in phases if row["phase"] == "attack_mix"]
    all_honest = sum(int(row["honest_verified_ok"]) for row in phases)
    honest_injection = sum(int(row["honest_verified_ok"]) for row in attack_rows)
    malformed = sum(int(row["attack_sent"]) for row in attack_rows)
    assert all_honest == 32609 and honest_injection == 16381 and malformed == 7049
    assert sum(int(row["honest_verified_fail"]) for row in phases) == 0
    assert sum(int(row["attack_responses"]) for row in attack_rows) == 0
    assert sum(int(row["attack_errors"]) for row in attack_rows) == 0
    changes = [float(row["throughput_change_pct"]) for row in pairs]
    mean_change, low, high = mean_ci95_six(changes)

    return {
        "component_checkpoints": checkpoint_result,
        "concurrency": {
            "levels": {
                row["clients"]: {
                    "repeats": int(row["repeats"]),
                    "pass_repeats": int(row["pass"]),
                    "verified_ok": int(row["verified_ok"]),
                    "verified_fail": int(row["verified_fail"]),
                    "verified_rps_mean": float(row["verified_rps_mean"]),
                }
                for row in summary
            },
            "highest_tested_all_pass_clients": 5,
            "first_tested_instability_clients": 10,
        },
        "placement": placement,
        "attack_mix": {
            "pairs": 6,
            "honest_verified_all_phases": all_honest,
            "honest_failures_all_phases": 0,
            "malformed_frames_offered": malformed,
            "malformed_application_responses": 0,
            "honest_verified_during_injection": honest_injection,
            "throughput_change_mean_pct": mean_change,
            "throughput_change_ci95_pct": [low, high],
            "achieved_malformed_share_pct_range": [
                100 * min(float(row["achieved_attack_fraction"]) for row in pairs),
                100 * max(float(row["achieved_attack_fraction"]) for row in pairs),
            ],
        },
    }


def q5_rotation_traceability() -> dict[str, Any]:
    timeline = read_csv("rotation/one_hour_timeline.csv")
    actions = read_csv("rotation/rotation_actions.csv")
    summary = read_csv("rotation/rotation_summary.csv")
    assert len(timeline) == 240 and all(row["result"] == "PASS" for row in timeline)
    assert sum(bool(row["app_elapsed_ms"].strip()) for row in timeline) == 239
    anchor = [row for row in actions if row["source"] == "one_hour_anchor"]
    r30 = [row for row in actions if row["source"] == "rotation_30s"]
    r10 = [row for row in actions if row["source"] == "rotation_10s"]
    assert len(anchor) == 240 and len(r30) == len(r10) == 60
    assert all(row["result"] == "PASS" and row["evidence_match"] == "PASS" for row in actions)
    assert len({row["transport_key_id"] for row in anchor}) == 59
    assert len({row["transport_key_id"] for row in r30}) == 17
    assert len({row["transport_key_id"] for row in r10}) == 34

    by_rotation = {int(row["rotation_seconds"]): row for row in summary}
    for rotation, expected_keys in [(30, 17), (10, 34)]:
        row = by_rotation[rotation]
        assert int(row["actions"]) == int(row["pass"]) == 60
        assert int(row["unique_key_ids"]) == expected_keys

    single = read_csv("traceability/core_single_key_linkage.csv")
    multi = read_csv("traceability/core_multi_key_linkage.csv")
    audit = read_csv("traceability/audit_chain_tamper_results.csv")
    assert len(single) == 1 and single[0]["result"] == "PASS" and int(single[0]["qgp_log_rows"]) == 28
    assert len(multi) == 11 and all(row["result"] == "PASS" for row in multi)
    multi_actions = sum(int(row["sender_qgp_event_count"]) for row in multi)
    assert multi_actions == 604
    assert all(int(row["destination_key_retrieval_hits"]) >= 1 for row in multi)
    assert len(audit) == 10 and all(row["detected"] == "YES" and row["verifier_result"] == "FAIL" for row in audit)

    rotation_values = {}
    for rotation in [30, 10]:
        row = by_rotation[rotation]
        rotation_values[str(rotation)] = {
            "verified_actions": int(row["pass"]),
            "used_key_ids": int(row["unique_key_ids"]),
            "actions_per_key_id": float(row["actions_per_key_id"]),
            "application_MB_per_key_id": float(row["application_payload_MB_per_key_id"]),
            "encrypted_frame_MB_per_key_id": float(row["encrypted_frame_MB_per_key_id"]),
        }
    return {
        "one_hour": {
            "verified_actions": 240,
            "used_key_ids": 59,
            "retained_latency_values": 239,
        },
        "matched_rotation_probes": rotation_values,
        "traceability": {
            "core_single_key_actions": 14,
            "core_single_key_qgp_log_rows": 28,
            "core_multi_key_actions": multi_actions,
            "core_multi_key_ids": 11,
            "sidecar_actions": 90,
            "sidecar_key_ids": 5,
            "audit_chain_events": 100,
            "injected_event_modifications_detected": 10,
            "injected_event_modifications": 10,
        },
    }


def flatten(prefix: str, value: Any, rows: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            flatten(f"{prefix}.{key}" if prefix else str(key), child, rows)
    elif isinstance(value, list):
        rows.append({"metric": prefix, "value": json.dumps(value, separators=(",", ":"))})
    else:
        rows.append({"metric": prefix, "value": str(value)})


def main() -> None:
    summary = {
        "Q1_functional_coverage": q1_functional(),
        "Q2_security_effectiveness": q2_security(),
        "Q3_Q4_performance_and_attack_mix": q3_q4_performance(),
        "Q5_rotation_and_traceability": q5_rotation_traceability(),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    flat_rows: list[dict[str, str]] = []
    flatten("", summary, flat_rows)
    with (RESULTS / "manuscript_values.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(flat_rows)
    print("validated all released experiment families")
    print(f"wrote {RESULTS / 'summary.json'}")
    print(f"wrote {RESULTS / 'manuscript_values.csv'}")


if __name__ == "__main__":
    main()
