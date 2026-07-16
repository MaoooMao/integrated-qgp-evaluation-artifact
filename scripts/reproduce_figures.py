#!/usr/bin/env python3
"""Generate the quantitative paper figures from locked, accepted evidence.

The script deliberately names every canonical input.  It never searches the
evidence tree recursively, so failed retries and diagnostic summaries cannot
silently enter a paper figure.  Each run also writes a provenance manifest
with input/output hashes and the scientific boundary of every chart.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import re
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


CS_ROOT = Path(__file__).resolve().parents[1]
DATA = CS_ROOT / "data"
OUT = CS_ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "s1_summary": DATA / "performance" / "concurrency_summary.csv",
    "s1_raw": DATA / "performance" / "concurrency_trials.csv",
    "s2_pairs": DATA / "performance" / "attack_mix_pairs.csv",
    "s2_rows": DATA / "performance" / "attack_mix_phase_rows.csv",
    "rotation_summary": DATA / "rotation" / "rotation_summary.csv",
    "rotation_actions": DATA / "rotation" / "rotation_actions.csv",
    "longrun_timeline": DATA / "rotation" / "one_hour_timeline.csv",
    "sidecar_actions": DATA / "functional" / "sidecar_key_coverage.csv",
    "binding_probe": DATA / "security" / "valid_signature_binding_trials.csv",
    "functional_perf_alice": DATA / "functional" / "functional_perf_alice.jsonl",
    "functional_perf_bob": DATA / "functional" / "functional_perf_bob.jsonl",
    "functional_qkd_audit": DATA / "functional" / "functional_qkd_audit.json",
    "attack_panel": DATA / "security" / "fail_closed_trials.csv",
    "udp_boundary": DATA / "functional" / "udp_boundary_trials.csv",
}


# Restrained journal palette.  Blue is the primary quantitative series;
# gold is reserved for an explicit comparator.  Neutrals carry raw evidence.
INK = "#242A31"
MUTED = "#68717B"
GRID = "#D9DEE3"
BLUE = "#2B648E"
BLUE_DARK = "#163F5C"
BLUE_LIGHT = "#DCEAF3"
GOLD = "#C58A2B"
GOLD_DARK = "#795117"
GRAY = "#9AA2AA"
GRAY_LIGHT = "#EEF1F3"
WHITE = "#FFFFFF"

TRAFFIC = {
    "message": (BLUE, "o", "Message"),
    "file": (GOLD, "s", "File"),
    "openweb": (MUTED, "^", "Web fetch"),
}

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8.2,
        "axes.titlesize": 8.4,
        "axes.labelsize": 8.2,
        "axes.edgecolor": INK,
        "axes.linewidth": 0.65,
        "xtick.labelsize": 7.4,
        "ytick.labelsize": 7.4,
        "xtick.color": INK,
        "ytick.color": INK,
        "legend.fontsize": 7.4,
        "legend.frameon": False,
        "lines.linewidth": 1.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "mathtext.fontset": "dejavusans",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.025,
    }
)


_INPUT_MANIFEST: dict[str, dict] = {}
_OUTPUT_MANIFEST: dict[str, dict] = {}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_rows(name: str, required: set[str] | None = None) -> list[dict[str, str]]:
    path = SOURCES[name]
    if "_failed_attempts" in path.parts:
        raise ValueError(f"failed-attempt input is forbidden: {path}")
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"empty input: {path}")
    columns = list(rows[0])
    missing = (required or set()).difference(columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")
    _INPUT_MANIFEST[name] = {
        "path": str(path.relative_to(CS_ROOT)),
        "rows": len(rows),
        "columns": columns,
        "sha256": sha256(path),
    }
    return rows


def load_jsonl_rows(name: str, required: set[str] | None = None) -> list[dict]:
    path = SOURCES[name]
    if "_failed_attempts" in path.parts:
        raise ValueError(f"failed-attempt input is forbidden: {path}")
    if not path.is_file():
        raise FileNotFoundError(path)
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{name}:{line_number} is not a JSON object")
            rows.append(row)
    if not rows:
        raise ValueError(f"empty input: {path}")
    columns = sorted(set().union(*(row.keys() for row in rows)))
    missing = (required or set()).difference(columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")
    _INPUT_MANIFEST[name] = {
        "path": str(path.relative_to(CS_ROOT)),
        "rows": len(rows),
        "columns": columns,
        "sha256": sha256(path),
    }
    return rows


def load_json_object(name: str, required: set[str] | None = None) -> dict:
    path = SOURCES[name]
    if "_failed_attempts" in path.parts:
        raise ValueError(f"failed-attempt input is forbidden: {path}")
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{name} is not a JSON object")
    missing = (required or set()).difference(value)
    if missing:
        raise ValueError(f"{name} missing fields: {sorted(missing)}")
    _INPUT_MANIFEST[name] = {
        "path": str(path.relative_to(CS_ROOT)),
        "rows": 1,
        "columns": sorted(value),
        "sha256": sha256(path),
    }
    return value


def as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "pass"}


def style_axis(ax, *, grid: str | None = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=2.5, width=0.55)
    ax.set_axisbelow(True)
    if grid:
        ax.grid(True, axis=grid, color=GRID, linestyle=":", linewidth=0.5)


def panel_title(ax, label: str, title: str) -> None:
    ax.set_title(f"({label}) {title}", loc="left", pad=4, color=INK, fontweight="semibold")


def deterministic_jitter(n: int, seed: int, width: float = 0.11) -> np.ndarray:
    """Natural-looking but reproducible jitter, independent of measured value."""
    rng = np.random.default_rng(seed)
    return rng.uniform(-width, width, n)


def first_seen_indices(values: list[str]) -> tuple[list[int], dict[str, int]]:
    mapping: dict[str, int] = {}
    indices = []
    for value in values:
        if value not in mapping:
            mapping[value] = len(mapping) + 1
        indices.append(mapping[value])
    return indices, mapping


def mean_ci95(values: list[float]) -> tuple[float, float, float]:
    arr = np.asarray(values, dtype=float)
    if len(arr) != 6:
        raise ValueError("paired C&S result expects exactly six pairs")
    t_critical_df5 = 2.570581835636314
    mean = float(np.mean(arr))
    half = t_critical_df5 * float(np.std(arr, ddof=1)) / math.sqrt(len(arr))
    return mean, mean - half, mean + half


def save_figure(fig, filename: str, contract: dict) -> None:
    path = OUT / filename
    fig.savefig(path)
    plt.close(fig)
    _OUTPUT_MANIFEST[filename] = {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        **contract,
    }
    print(f"wrote {filename}")


def figure_fail_closed() -> None:
    attacks = load_rows(
        "attack_panel",
        {
            "case",
            "trial",
            "action_id",
            "expected_accept",
            "accepted_by_response",
            "bob_qgp_reason",
            "appserver_b_plaintexts_for_attack_send",
            "app_plaintext_policy_ok",
            "trial_result",
        },
    )
    if (
        len(attacks) != 400
        or len({(row["case"], row["trial"]) for row in attacks}) != 400
        or len({row["action_id"] for row in attacks}) != 400
        or any(row["trial_result"] != "PASS" or not as_bool(row["app_plaintext_policy_ok"]) for row in attacks)
    ):
        raise ValueError("attack panel must contain 400 PASS trials")

    case_order = [
        "honest_baseline",
        "raw_no_qgp",
        "payload_flip",
        "payload_bytes_mutation",
        "truncation",
        "timestamp_shift",
        "nonce_replay",
        "unsupported_algorithm",
        "traffic_type_mutation",
        "signature_flip",
        "forged_signature",
    ]
    case_labels = {
        "honest_baseline": "Honest baseline",
        "payload_flip": "Payload flip",
        "payload_bytes_mutation": "Byte-count mutation",
        "truncation": "Envelope truncation",
        "nonce_replay": "Nonce replay",
        "timestamp_shift": "Timestamp shift",
        "raw_no_qgp": "Raw non-QGP input",
        "unsupported_algorithm": "Unsupported algorithm",
        "traffic_type_mutation": "Traffic-type mutation",
        "signature_flip": "Signature flip",
        "forged_signature": "Forged signature",
    }
    stage_for_case = {
        "honest_baseline": "Delivered",
        "raw_no_qgp": "Parser",
        "payload_flip": "Payload/integrity",
        "payload_bytes_mutation": "Payload/integrity",
        "truncation": "Payload/integrity",
        "nonce_replay": "Freshness/replay",
        "timestamp_shift": "Freshness/replay",
        "unsupported_algorithm": "Algorithm policy",
        "traffic_type_mutation": "Signature",
        "signature_flip": "Signature",
        "forged_signature": "Signature",
    }
    stages = [
        "Parser",
        "Payload/integrity",
        "Freshness/replay",
        "Algorithm policy",
        "Signature",
        "Delivered",
    ]
    grouped_attacks = defaultdict(list)
    for row in attacks:
        grouped_attacks[row["case"]].append(row)
    if set(grouped_attacks) != set(case_order):
        raise ValueError("attack cases changed")

    # Use one single-column annotated matrix for the central fail-closed result.
    fig, ax_a = plt.subplots(figsize=(3.50, 3.55), layout="constrained")

    attack_matrix = np.full((len(case_order), len(stages)), np.nan)
    attack_plaintext = []
    for y, case in enumerate(case_order):
        rows = grouped_attacks[case]
        n = len(rows)
        stage = stage_for_case[case]
        x = stages.index(stage)
        accepted = sum(as_bool(row["accepted_by_response"]) for row in rows)
        plaintext = sum(int(row["appserver_b_plaintexts_for_attack_send"]) for row in rows)
        if case == "honest_baseline":
            if accepted != n or plaintext != n:
                raise ValueError("honest attack-panel baseline changed")
        else:
            if accepted != 0 or plaintext != 0:
                raise ValueError(f"attack unexpectedly accepted: {case}")
        attack_matrix[y, x] = n
        attack_plaintext.append((plaintext, n))

    # Conventional annotated outcome matrix: the filled cell is the terminal
    # receiver stage, and its annotation gives the observed count.  This is
    # intentionally a heatmap rather than a sparse marker grid.
    for y, case in enumerate(case_order):
        for x in range(len(stages)):
            active = not np.isnan(attack_matrix[y, x])
            if active:
                fill = BLUE_LIGHT if case == "honest_baseline" else GRAY_LIGHT
                edge = BLUE_DARK if case == "honest_baseline" else MUTED
            else:
                fill, edge = WHITE, GRID
            ax_a.add_patch(plt.Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor=fill, edgecolor=edge, linewidth=0.55))
            if active:
                n = int(attack_matrix[y, x])
                ax_a.text(x, y, f"{n}/{n}", ha="center", va="center", fontsize=7.2, color=INK, fontweight="semibold")

    # Keep the application-delivery count inside the matrix instead of
    # leaving it as a visually detached text column.
    plaintext_x = len(stages)
    for y, (plaintext, n) in enumerate(attack_plaintext):
        fill = BLUE_LIGHT if plaintext else WHITE
        edge = BLUE_DARK if plaintext else GRID
        ax_a.add_patch(
            plt.Rectangle(
                (plaintext_x - 0.5, y - 0.5),
                1,
                1,
                facecolor=fill,
                edgecolor=edge,
                linewidth=0.55,
            )
        )
        ax_a.text(
            plaintext_x,
            y,
            f"{plaintext}/{n}",
            ha="center",
            va="center",
            fontsize=7.2,
            color=INK,
            fontweight="semibold" if plaintext else "normal",
        )
    ax_a.axvline(len(stages) - 0.48, color=INK, linewidth=0.7)

    ax_a.set_xlim(-0.52, len(stages) + 0.52)
    ax_a.set_ylim(len(case_order) - 0.48, -0.52)
    ax_a.set_xticks(range(len(stages) + 1))
    ax_a.set_xticklabels(
        ["Parse", "Payload", "Fresh.", "Policy", "Sig.", "Deliver", "App B\nplain."],
        fontsize=7.2,
    )
    ax_a.xaxis.tick_top()
    ax_a.tick_params(axis="x", labeltop=True, labelbottom=False, pad=2)
    ax_a.set_yticks(range(len(case_order)))
    ax_a.set_yticklabels([case_labels[c] for c in case_order])
    ax_a.set_title("Terminal receiver stage", loc="left", pad=22, color=INK, fontweight="semibold")
    ax_a.tick_params(length=0)
    for spine in ax_a.spines.values():
        spine.set_visible(False)

    save_figure(
        fig,
        "fig_fail_closed_coverage.pdf",
        {
            "question": "Where does malformed, replayed, or forged traffic terminate before application delivery?",
            "takeaway": "All 370 tested negative inputs terminate before delivery, while all 30 honest baselines reach AppServer B.",
            "boundary": "Implementation-path coverage only; the forgery trials do not estimate a cryptographic security bound.",
        },
    )


def figure_performance_profile() -> None:
    alice_perf = load_jsonl_rows(
        "functional_perf_alice",
        {
            "service_action_id",
            "traffic_type",
            "transport_key_id",
            "verdict",
            "request_payload_bytes",
            "request_qgp_envelope_bytes",
            "request_qgp_build_sign_ms",
            "request_core_encrypt_send_ms",
            "response_core_recv_decrypt_ms",
            "response_qgp_verify_ms",
        },
    )
    bob_perf = load_jsonl_rows(
        "functional_perf_bob",
        {
            "service_action_id",
            "traffic_type",
            "transport_key_id",
            "verdict",
            "request_payload_bytes",
            "request_core_recv_decrypt_ms",
            "request_qgp_verify_ms",
            "app_roundtrip_ms",
            "response_payload_bytes",
            "response_qgp_envelope_bytes",
            "response_qgp_build_sign_ms",
            "response_core_encrypt_send_ms",
            "sequence",
        },
    )
    qkd_audit = load_json_object(
        "functional_qkd_audit", {"qkd_expected", "transport_key_id_candidates"}
    )
    # The formal message campaign consists of the 30 22/23-byte actions.  The
    # 55-byte rows are service-health probes and are deliberately excluded.
    alice_formal = [
        row
        for row in alice_perf
        if row["traffic_type"] == "message"
        and int(row["request_payload_bytes"]) in {22, 23}
        and row["verdict"] == "PASS"
    ]
    if len(alice_formal) != 30:
        raise ValueError(f"expected 30 formal live-QKD message actions, got {len(alice_formal)}")
    alice_by_action = {row["service_action_id"]: row for row in alice_formal}
    if len(alice_by_action) != 30:
        raise ValueError("formal Alice message action identifiers are not unique")
    bob_by_action = {row["service_action_id"]: row for row in bob_perf}
    if len(bob_by_action) != len(bob_perf):
        raise ValueError("Bob performance action identifiers are not unique")
    if any(action not in bob_by_action for action in alice_by_action):
        raise ValueError("a formal Alice message action has no Bob performance row")
    joined = [(alice_by_action[action], bob_by_action[action]) for action in alice_by_action]

    if not qkd_audit["qkd_expected"]:
        raise ValueError("functional checkpoint source is not marked QKD-expected")
    audited_key_ids = set(qkd_audit["transport_key_id_candidates"])
    for alice_row, bob_row in joined:
        if alice_row["transport_key_id"] != bob_row["transport_key_id"]:
            raise ValueError("Alice/Bob checkpoint KeyId mismatch")
        key_id = alice_row["transport_key_id"]
        if not re.fullmatch(r"KID-\d{3}", key_id):
            raise ValueError(f"unexpected public KeyId pseudonym: {key_id}")
        if key_id not in audited_key_ids:
            raise ValueError(f"checkpoint KeyId absent from QKD audit: {key_id}")

    checkpoint_fields = [
        ("Alice QGP build+sign", 0, "request_qgp_build_sign_ms"),
        ("Alice core encrypt+send request", 0, "request_core_encrypt_send_ms"),
        ("Bob core receive+decrypt request", 1, "request_core_recv_decrypt_ms"),
        ("Bob QGP verify request", 1, "request_qgp_verify_ms"),
        ("Bob app roundtrip", 1, "app_roundtrip_ms"),
        ("Bob QGP build+sign response", 1, "response_qgp_build_sign_ms"),
        ("Bob core encrypt+send response", 1, "response_core_encrypt_send_ms"),
        ("Alice core receive+decrypt response", 0, "response_core_recv_decrypt_ms"),
        ("Alice QGP verify response", 0, "response_qgp_verify_ms"),
    ]
    checkpoints = []
    for component, side, field in checkpoint_fields:
        values = [float(pair[side][field]) for pair in joined]
        ordered = sorted(values)
        checkpoints.append(
            {
                "component": component,
                "runs": len(values),
                "mean_ms": statistics.mean(values),
                "median_ms": statistics.median(values),
                "p95_ms": ordered[math.ceil(0.95 * len(ordered)) - 1],
                "min_ms": ordered[0],
                "max_ms": ordered[-1],
                "stdev_ms": statistics.stdev(values),
                "values_ms": values,
            }
        )

    # Guard the manuscript's Table 4 against mixing smoke rows, carrier-frame
    # bytes, or request/response directions.  These are the formal 30-run rows.
    file_formal = [
        row
        for row in alice_perf
        if row["traffic_type"] == "file"
        and int(row["request_payload_bytes"]) in {4334, 4335}
        and row["verdict"] == "PASS"
    ]
    web_formal = [
        row
        for row in bob_perf
        if row["traffic_type"] == "openweb_http_request"
        and int(row["sequence"]) >= 69
        and row["verdict"] == "PASS"
    ]
    if len(file_formal) != 30 or len(web_formal) != 30:
        raise ValueError("Table 4 sources must contain 30 formal file and web rows")
    table4_contract = {
        "message_request_envelope_median_bytes": int(
            statistics.median(int(row["request_qgp_envelope_bytes"]) for row in alice_formal)
        ),
        "message_application_payload_median_bytes": int(
            statistics.median(int(row["request_payload_bytes"]) for row in alice_formal)
        ),
        "file_request_envelope_median_bytes": int(
            statistics.median(int(row["request_qgp_envelope_bytes"]) for row in file_formal)
        ),
        "file_application_payload_bytes": 4096,
        "web_response_envelope_median_bytes": int(
            statistics.median(int(row["response_qgp_envelope_bytes"]) for row in web_formal)
        ),
        "web_response_payload_median_bytes": int(
            statistics.median(int(row["response_payload_bytes"]) for row in web_formal)
        ),
    }
    expected_table4 = {
        "message_request_envelope_median_bytes": 7742,
        "message_application_payload_median_bytes": 23,
        "file_request_envelope_median_bytes": 12050,
        "file_application_payload_bytes": 4096,
        "web_response_envelope_median_bytes": 329918,
        "web_response_payload_median_bytes": 321885,
    }
    if table4_contract != expected_table4:
        raise ValueError(f"Table 4 envelope contract changed: {table4_contract}")

    fig_checkpoints, ax_cp = plt.subplots(figsize=(3.50, 3.18), layout="constrained")

    cp_labels = {
        "Alice QGP build+sign": "Alice: QGP build + sign",
        "Alice core encrypt+send request": "Alice: encrypt + send request",
        "Bob core receive+decrypt request": "Bob: receive + decrypt request",
        "Bob QGP verify request": "Bob: QGP verify request",
        "Bob app roundtrip": "Bob: application round trip",
        "Bob QGP build+sign response": "Bob: QGP build + sign response",
        "Bob core encrypt+send response": "Bob: encrypt + send response",
        "Alice core receive+decrypt response": "Alice: receive + decrypt response",
        "Alice QGP verify response": "Alice: QGP verify response",
    }
    y = np.arange(len(checkpoints))
    for idx, row in enumerate(checkpoints):
        median = float(row["median_ms"])
        p95 = float(row["p95_ms"])
        raw = np.asarray(row["values_ms"], dtype=float)
        ax_cp.scatter(
            raw,
            idx + deterministic_jitter(len(raw), 310 + idx, width=0.10),
            s=7,
            marker="o",
            facecolor=WHITE,
            edgecolor=GRAY,
            linewidth=0.35,
            alpha=0.7,
            zorder=1,
        )
        ax_cp.hlines(idx, median, p95, color=BLUE_DARK, linewidth=0.8, zorder=2)
        ax_cp.scatter(median, idx, s=18, marker="o", facecolor=WHITE, edgecolor=BLUE_DARK, linewidth=0.8, zorder=3)
        ax_cp.scatter(p95, idx, s=26, marker="|", color=BLUE_DARK, linewidth=1.25, zorder=3)
    ax_cp.set_xscale("log")
    ax_cp.set_yticks(y)
    ax_cp.set_yticklabels([cp_labels[row["component"]] for row in checkpoints])
    ax_cp.invert_yaxis()
    ax_cp.set_xlabel("Checkpoint duration (ms, log scale)")
    style_axis(ax_cp, grid="x")
    ax_cp.legend(
        handles=[
            Line2D([], [], marker="o", markerfacecolor=WHITE, markeredgecolor=GRAY, linestyle="none", markersize=3.5, label="Raw"),
            Line2D([], [], marker="o", markerfacecolor=WHITE, markeredgecolor=BLUE_DARK, linestyle="none", label="Median"),
            Line2D([], [], marker="|", color=BLUE_DARK, linestyle="none", markersize=7, label="P95"),
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=3,
        columnspacing=0.9,
        handletextpad=0.4,
    )

    save_figure(
        fig_checkpoints,
        "fig_component_checkpoints.pdf",
        {
            "question": "What local checkpoint ranges are observed for 30 joined live-QKD message actions?",
            "takeaway": "QGP construction and verification fall in the low-millisecond range, while application and receive/decrypt intervals are the longest and most variable.",
            "boundary": "Checkpoint rows are overlapping instrumentation ranges and must not be added to reconstruct end-to-end latency.",
        },
    )


def figure_service_path_envelope() -> None:
    summary = load_rows(
        "s1_summary",
        {"clients", "repeats", "pass", "verified_ok", "verified_fail", "verified_rps_mean", "verified_rps_sd"},
    )
    raw = load_rows(
        "s1_raw",
        {
            "run_id",
            "expected_key_source",
            "measurement_semantics",
            "clients",
            "repeat_index",
            "result",
            "attempted",
            "verified_ok",
            "verified_fail",
            "verified_request_per_second",
        },
    )
    pairs = load_rows(
        "s2_pairs",
        {
            "pair_index",
            "baseline_verified_rps",
            "attack_verified_rps",
            "throughput_change_pct",
            "achieved_attack_fraction",
            "attack_responses",
            "attack_errors",
            "result",
        },
    )
    pair_rows = load_rows(
        "s2_rows",
        {
            "pair_index",
            "phase",
            "honest_attempted",
            "honest_verified_ok",
            "honest_verified_fail",
            "attack_sent",
            "attack_responses",
            "attack_errors",
        },
    )

    accepted_clients = [1, 2, 5, 10, 20, 30, 50]
    all_clients = [int(row["clients"]) for row in summary]
    if all_clients != accepted_clients or len(raw) != 35:
        raise ValueError("S1 must be the accepted 7 x 5 matrix")
    if len({row["run_id"] for row in raw}) != 35:
        raise ValueError("S1 run identifiers are not unique")
    if any(row["expected_key_source"] != "qkd" for row in raw):
        raise ValueError("S1 contains a non-QKD row")
    if any(int(row["verified_ok"]) + int(row["verified_fail"]) != int(row["attempted"]) for row in raw):
        raise ValueError("S1 attempted count does not reconcile")
    if Counter(int(row["clients"]) for row in raw) != Counter({c: 5 for c in all_clients}):
        raise ValueError("S1 repeat counts changed")
    if len(pairs) != 6 or any(row["result"] != "PASS" for row in pairs):
        raise ValueError("S2 must contain six accepted pairs")
    if any(int(row["attack_responses"]) or int(row["attack_errors"]) for row in pairs):
        raise ValueError("S2 includes an attack response or injector error")
    if len(pair_rows) != 12 or len({(row["pair_index"], row["phase"]) for row in pair_rows}) != 12:
        raise ValueError("S2 phase rows must be six unique clean/attack pairs")
    if sum(int(row["honest_verified_ok"]) for row in pair_rows) != 32609:
        raise ValueError("S2 honest verified total changed")
    if sum(int(row["honest_verified_fail"]) for row in pair_rows) != 0:
        raise ValueError("S2 includes an honest failure")
    attack_rows = [row for row in pair_rows if row["phase"] == "attack_mix"]
    malformed_offered = sum(int(row["attack_sent"]) for row in attack_rows)
    honest_during_injection = sum(int(row["honest_verified_ok"]) for row in attack_rows)
    if malformed_offered != 7049:
        raise ValueError("S2 attack-offer total changed")
    if honest_during_injection != 16381:
        raise ValueError("S2 injection-phase honest total changed")
    if any(int(row["attack_responses"]) or int(row["attack_errors"]) for row in attack_rows):
        raise ValueError("S2 attack stream produced a response or error")

    raw_by_client = defaultdict(list)
    for row in raw:
        raw_by_client[int(row["clients"])].append(float(row["verified_request_per_second"]))

    # The accepted dataset retains the full seven-level stress sweep as a
    # validation gate.  The paper figure focuses on the levels needed to
    # establish the all-PASS range and its first observed transition point.
    clients = [1, 2, 5, 10]
    summary_by_client = {int(row["clients"]): row for row in summary}
    display_summary = [summary_by_client[client] for client in clients]

    # As in the reference article's principal comparison plots, retain a full
    # single column for the main experiment and stack its two linked views.
    # S2 remains a separate single-column figure because it is a distinct run.
    fig_scaling = plt.figure(figsize=(3.50, 3.90), layout="constrained")
    scaling_gs = fig_scaling.add_gridspec(2, 1, hspace=0.14)
    ax_rate = fig_scaling.add_subplot(scaling_gs[0, 0])
    ax_fail = fig_scaling.add_subplot(scaling_gs[1, 0])
    pos = np.arange(len(clients))

    for x, client in enumerate(clients):
        values = raw_by_client[client]
        ax_rate.scatter(
            x + deterministic_jitter(len(values), 310 + x, 0.10),
            values,
            s=11,
            facecolor=WHITE,
            edgecolor=GRAY,
            linewidth=0.5,
            zorder=2,
        )
    means = [float(row["verified_rps_mean"]) for row in display_summary]
    sds = [float(row["verified_rps_sd"]) for row in display_summary]
    ax_rate.errorbar(
        pos,
        means,
        yerr=sds,
        fmt="o",
        color=BLUE_DARK,
        markerfacecolor=BLUE,
        markeredgecolor=BLUE_DARK,
        markersize=3.8,
        elinewidth=0.8,
        capsize=2.2,
        zorder=4,
    )
    ax_rate.axvline(2.5, color=GRAY, linestyle="--", linewidth=0.7, zorder=0)
    ax_rate.set_xticks(pos)
    ax_rate.set_xticklabels([str(c) for c in clients])
    ax_rate.set_ylim(0, 30)
    ax_rate.set_xlabel("Concurrent clients")
    ax_rate.set_ylabel("Verified rate (req/s)")
    panel_title(ax_rate, "a", "Verified service rate")
    style_axis(ax_rate)
    ax_rate.text(2.42, 28.8, "highest all-PASS:\n5 clients", ha="right", va="top", fontsize=7.2, color=MUTED)

    success_rates = []
    for row in display_summary:
        ok = int(row["verified_ok"])
        fail = int(row["verified_fail"])
        success_rates.append(100.0 * ok / (ok + fail))
    ax_fail.bar(
        pos,
        success_rates,
        width=0.62,
        color=BLUE_LIGHT,
        edgecolor=BLUE_DARK,
        linewidth=0.75,
    )
    for x, rate in zip(pos, success_rates):
        label = f"{rate:.1f}" if rate < 100 else "100"
        ax_fail.text(x, rate + 1.8, label, ha="center", va="bottom", fontsize=7.2)
    ax_fail.axvline(2.5, color=GRAY, linestyle="--", linewidth=0.7, zorder=0)
    ax_fail.set_xticks(pos)
    ax_fail.set_xticklabels([str(c) for c in clients])
    ax_fail.set_ylim(0, 112)
    ax_fail.set_yticks([0, 25, 50, 75, 100])
    ax_fail.set_xlabel("Concurrent clients")
    ax_fail.set_ylabel("Verified-delivery success rate (%)")
    panel_title(ax_fail, "b", "Verified-delivery success")
    style_axis(ax_fail)

    fig_attack = plt.figure(figsize=(3.50, 3.15), layout="constrained")
    attack_gs = fig_attack.add_gridspec(2, 1, height_ratios=[1.25, 1.0], hspace=0.16)
    ax_outcomes = fig_attack.add_subplot(attack_gs[0, 0])
    ax_ci = fig_attack.add_subplot(attack_gs[1, 0])

    panel_title(ax_outcomes, "a", "Observed outcomes during injection")
    ax_outcomes.set_xlim(0, 1)
    ax_outcomes.set_ylim(-0.08, 1.0)
    ax_outcomes.axis("off")
    column_x = [0.15, 0.50, 0.85]
    columns = zip(column_x, ["Offered\ninput", "Receiver\noutcome", "Application\noutcome"])
    for x, label in columns:
        ax_outcomes.text(x, 0.87, label, ha="center", va="center", fontsize=7.2, color=MUTED, linespacing=1.05)

    outcome_rows = [
        {
            "y": 0.62,
            "color": GOLD,
            "labels": [
                f"{malformed_offered:,} malformed\nframes",
                f"{malformed_offered:,} FAIL\n(all rejected)",
                "0 application\nresponses",
            ],
            "terminal_hollow": True,
        },
        {
            "y": 0.20,
            "color": BLUE,
            "labels": [
                f"{honest_during_injection:,} honest\nactions",
                f"{honest_during_injection:,} PASS\n(zero failures)",
                f"{honest_during_injection:,} verified\ndeliveries",
            ],
            "terminal_hollow": False,
        },
    ]
    for row in outcome_rows:
        y = row["y"]
        color = row["color"]
        for start, end in [(0.24, 0.41), (0.59, 0.76)]:
            ax_outcomes.annotate(
                "",
                xy=(end, y),
                xytext=(start, y),
                arrowprops={"arrowstyle": "-|>", "color": color, "linewidth": 1.0, "shrinkA": 0, "shrinkB": 0},
            )
        for idx, (x, label) in enumerate(zip(column_x, row["labels"])):
            hollow = bool(row["terminal_hollow"] and idx == 2)
            ax_outcomes.scatter(
                [x],
                [y],
                s=22,
                marker="o",
                facecolor=WHITE if hollow else color,
                edgecolor=color,
                linewidth=0.8,
                zorder=3,
            )
            ax_outcomes.text(x, y - 0.13, label, ha="center", va="top", fontsize=7.2, color=INK, linespacing=1.18)

    throughput_changes = [float(row["throughput_change_pct"]) for row in pairs]
    throughput_mean, throughput_low, throughput_high = mean_ci95(throughput_changes)
    ax_ci.scatter(
        throughput_changes,
        1 + deterministic_jitter(len(throughput_changes), 410, 0.12),
        s=14,
        facecolor=WHITE,
        edgecolor=GRAY,
        linewidth=0.55,
        zorder=2,
    )
    ax_ci.hlines(0, throughput_low, throughput_high, color=BLUE_DARK, linewidth=1.15, zorder=3)
    ax_ci.vlines([throughput_low, throughput_high], -0.08, 0.08, color=BLUE_DARK, linewidth=0.8, zorder=3)
    ax_ci.scatter(
        throughput_mean,
        0,
        s=26,
        marker="s",
        facecolor=BLUE,
        edgecolor=INK,
        linewidth=0.35,
        zorder=4,
    )
    ax_ci.text(
        0.995,
        0.28,
        f"{throughput_mean:+.1f}% [{throughput_low:+.1f}, {throughput_high:+.1f}]",
        ha="right",
        va="center",
        fontsize=7.2,
        color=INK,
        transform=ax_ci.get_yaxis_transform(),
        bbox={"facecolor": WHITE, "edgecolor": "none", "pad": 0.4, "alpha": 0.88},
    )
    ax_ci.axvline(0, color=INK, linestyle="--", linewidth=0.75)
    ax_ci.set_yticks([1, 0])
    ax_ci.set_yticklabels(["Six paired runs", "Mean and 95% CI"])
    ax_ci.set_ylim(-0.45, 1.45)
    ax_ci.set_xlim(-3, 6)
    ax_ci.set_xticks([-3, 0, 3, 6])
    ax_ci.set_xlabel("Clean-to-injection throughput change (%)")
    panel_title(ax_ci, "b", "Honest-throughput change")
    style_axis(ax_ci, grid="x")

    save_figure(
        fig_scaling,
        "fig_service_path_scaling.pdf",
        {
            "question": "Where is the verified operating range before the first observed concurrency instability?",
            "takeaway": "The four reported levels show all-PASS operation through five clients and the first instability at ten.",
            "boundary": "This is a complete service-path boundary, not isolated QGP, QKD, cryptographic, or application capacity.",
        },
    )
    save_figure(
        fig_attack,
        "fig_attack_mix_effects.pdf",
        {
            "question": "Are malformed frames rejected while honest traffic retains verified delivery and throughput at the demonstrated two-client point?",
            "takeaway": "All 7,049 malformed frames were rejected, all 16,381 injection-phase honest actions reached verified delivery, and mean honest-throughput change was +0.8%.",
            "boundary": "The paired result applies to six tested two-client, 300-second clean and injection blocks.",
        },
    )


def contiguous_runs(values: list[int]) -> list[tuple[int, int, int]]:
    if not values:
        return []
    runs = []
    start = 0
    current = values[0]
    for idx, value in enumerate(values[1:], start=1):
        if value != current:
            runs.append((start, idx - 1, current))
            start = idx
            current = value
    runs.append((start, len(values) - 1, current))
    return runs


def figure_rotation_accounting() -> None:
    summary = load_rows(
        "rotation_summary",
        {
            "rotation_seconds",
            "actions",
            "pass",
            "unique_key_ids",
            "actions_per_key_id",
            "application_payload_MB_per_key_id",
            "encrypted_frame_MB_per_key_id",
        },
    )
    actions = load_rows(
        "rotation_actions",
        {"source", "rotation_seconds", "action_index", "traffic", "result", "evidence_match", "transport_key_id", "app_elapsed_ms"},
    )
    timeline = load_rows("longrun_timeline", {"sample", "elapsed_s", "traffic", "result", "app_elapsed_ms"})
    if [int(row["rotation_seconds"]) for row in summary] != [60, 30, 10]:
        raise ValueError("rotation summary changed")
    if len(actions) != 360 or any(row["result"] != "PASS" or row["evidence_match"] != "PASS" for row in actions):
        raise ValueError("rotation accounting must contain 360 joined PASS actions")
    if len(timeline) != 240 or any(row["result"] != "PASS" for row in timeline):
        raise ValueError("one-hour timeline must contain 240 PASS rows")
    missing_latency_samples = [int(row["sample"]) for row in timeline if not row["app_elapsed_ms"].strip()]
    if missing_latency_samples != [35]:
        raise ValueError(f"unexpected longrun latency missingness: {missing_latency_samples}")

    by_source = defaultdict(list)
    for row in actions:
        by_source[row["source"]].append(row)
    expected_counts = {"one_hour_anchor": 240, "rotation_30s": 60, "rotation_10s": 60}
    if {k: len(v) for k, v in by_source.items()} != expected_counts:
        raise ValueError("rotation action source counts changed")
    for rows in by_source.values():
        rows.sort(key=lambda row: int(row["action_index"]))

    timeline.sort(key=lambda row: int(row["sample"]))
    anchor = by_source["one_hour_anchor"]
    for old, canonical in zip(timeline, anchor):
        if int(old["sample"]) != int(canonical["action_index"]) or old["traffic"] != canonical["traffic"]:
            raise ValueError("longrun timeline does not align with canonical accounting")
    elapsed_min = [float(row["elapsed_s"]) / 60.0 for row in timeline]
    anchor_key_indices, anchor_key_map = first_seen_indices([row["transport_key_id"] for row in anchor])
    if len(anchor_key_map) != 59:
        raise ValueError("one-hour canonical accounting must contain 59 KeyIds")

    # The one-hour run is a historical stability anchor, whereas the 30/10 s
    # rows are a workload-matched accounting experiment.  Use one native
    # single-column figure per experiment family.
    fig_stability = plt.figure(figsize=(3.50, 2.05))
    stability_gs = fig_stability.add_gridspec(
        1,
        1,
        left=0.16,
        right=0.99,
        bottom=0.20,
        top=0.94,
    )
    ax_lat = fig_stability.add_subplot(stability_gs[0, 0])

    fig_key_use = plt.figure(figsize=(3.50, 1.72))
    key_use_gs = fig_key_use.add_gridspec(
        1,
        1,
        left=0.16,
        right=0.99,
        bottom=0.23,
        top=0.92,
    )
    ax_raster = fig_key_use.add_subplot(key_use_gs[0, 0])

    neutral_traffic = {
        "message": (INK, "o", "Message"),
        "file": (MUTED, "s", "File"),
        "openweb": (GRAY, "^", "Web fetch"),
    }
    for traffic in ["message", "file", "openweb"]:
        color, marker, label = neutral_traffic[traffic]
        xs, ys = [], []
        for old in timeline:
            if old["traffic"] == traffic and old["app_elapsed_ms"].strip():
                xs.append(float(old["elapsed_s"]) / 60.0)
                ys.append(float(old["app_elapsed_ms"]))
        ax_lat.scatter(xs, ys, s=8, marker=marker, facecolor=WHITE, edgecolor=color, linewidth=0.45, alpha=0.9, label=label)
    ax_lat.set_yscale("log")
    ax_lat.set_xlim(0, 60)
    ax_lat.set_ylim(8, 1600)
    ax_lat.set_ylabel("Latency (ms, log)")
    ax_lat.set_xlabel("Elapsed time (min)")
    ax_lat.set_xticks([0, 15, 30, 45, 60])
    ax_lat.set_title("Action latency over one hour", loc="left", pad=4, color=INK, fontweight="semibold")
    style_axis(ax_lat)
    # The latency bands leave a large empty log-scale interval; putting the
    # legend there avoids covering the Web-fetch observations or adding a
    # detached legend band above the figure.
    ax_lat.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 0.82),
        ncol=3,
        columnspacing=0.65,
        handletextpad=0.25,
        fontsize=7.8,
    )
    ax_lat.tick_params(labelsize=7.8)

    save_figure(
        fig_stability,
        "fig_rotation_stability.pdf",
        {
            "question": "Does the one-hour live-QKD workload remain verified across many QKD KeyIds?",
            "takeaway": "All 240 actions verify across 59 observed-and-used KeyIds, with stable traffic-specific latency bands.",
            "boundary": "One file latency is missing from the historical timeline and is not imputed; the complete 240-action canonical sequence contains 59 unique observed-and-used KeyIds.",
        },
    )

    summary_by_rotation = {int(row["rotation_seconds"]): row for row in summary}
    expected_accounting = {
        30: {
            "keys": 17,
            "actions_per_key_id": "3.53",
            "application_payload_MB_per_key_id": "0.384",
            "encrypted_frame_MB_per_key_id": "0.441",
        },
        10: {
            "keys": 34,
            "actions_per_key_id": "1.76",
            "application_payload_MB_per_key_id": "0.192",
            "encrypted_frame_MB_per_key_id": "0.221",
        },
    }
    for rotation, expected in expected_accounting.items():
        row = summary_by_rotation[rotation]
        observed = {
            "keys": int(row["unique_key_ids"]),
            "actions_per_key_id": f'{float(row["actions_per_key_id"]):.2f}',
            "application_payload_MB_per_key_id": f'{float(row["application_payload_MB_per_key_id"]):.3f}',
            "encrypted_frame_MB_per_key_id": f'{float(row["encrypted_frame_MB_per_key_id"]):.3f}',
        }
        if int(row["actions"]) != 60 or int(row["pass"]) != 60 or observed != expected:
            raise ValueError(f"{rotation}-second accounting values changed: {observed}")

    raster_sources = [
        ("rotation_30s", "30 s", 17, MUTED, "-", "o"),
        ("rotation_10s", "10 s", 34, BLUE_DARK, "--", "s"),
    ]
    for source, label, expected_keys, color, linestyle, marker in raster_sources:
        rows = by_source[source]
        key_indices, key_map = first_seen_indices([row["transport_key_id"] for row in rows])
        if len(key_map) != expected_keys:
            raise ValueError(f"{source} KeyId count changed")
        action_index = np.arange(1, len(key_indices) + 1)
        cumulative_keys = np.maximum.accumulate(np.asarray(key_indices))
        ax_raster.step(action_index, cumulative_keys, where="post", color=color, linestyle=linestyle, linewidth=1.15)
        ax_raster.plot(
            action_index[::10],
            cumulative_keys[::10],
            linestyle="none",
            marker=marker,
            markersize=2.6,
            markerfacecolor=WHITE,
            markeredgecolor=color,
            markeredgewidth=0.7,
        )
        ax_raster.text(
            60.2,
            expected_keys + (0.9 if source == "rotation_10s" else -1.0),
            f"{label} ({expected_keys})",
            ha="right",
            va="center",
            fontsize=7.8,
            color=color,
            bbox={"facecolor": WHITE, "edgecolor": "none", "pad": 0.4, "alpha": 1.0},
        )
    ax_raster.set_xlim(1, 61)
    ax_raster.set_ylim(0, 37)
    ax_raster.set_yticks([0, 10, 20, 30])
    ax_raster.set_xticks([1, 30, 60])
    ax_raster.set_xlabel("Action")
    ax_raster.set_ylabel("Cumulative KeyIds")
    ax_raster.set_title("KeyId accumulation (60 actions per probe)", loc="left", pad=4, color=INK, fontweight="semibold")
    style_axis(ax_raster)
    ax_raster.tick_params(labelsize=7.8)

    save_figure(
        fig_key_use,
        "fig_rotation_key_use.pdf",
        {
            "question": "How does matched rotation timing change observed KeyId accumulation?",
            "takeaway": "Across 60 matched actions, the 10 s probe observes 34 KeyIds compared with 17 at 30 s.",
            "boundary": "Exact per-KeyId action and byte values are validated from the same input and reported in text; these are operational, not entropy-consumption, measurements.",
        },
    )


def figure_key_binding() -> None:
    sidecar = load_rows(
        "sidecar_actions",
        {
            "action_index",
            "traffic_type",
            "transport_key_id",
            "sender_pass",
            "alice_qgp_pass",
            "bob_qgp_pass",
            "alice_carrier_pass",
            "bob_carrier_pass",
            "result",
        },
    )
    binding = load_rows(
        "binding_probe",
        {"case", "index", "expected", "case_result", "accepted_by_response", "key_source", "signed_top_level_key_id", "signed_transport_key_id", "frame_transport_key_id"},
    )
    if len(sidecar) != 90 or any(row["result"] != "PASS" for row in sidecar):
        raise ValueError("Sidecar accounting must contain 90 PASS actions")
    role_columns = ["sender_pass", "alice_qgp_pass", "bob_qgp_pass", "alice_carrier_pass", "bob_carrier_pass"]
    if any(not all(as_bool(row[col]) for col in role_columns) for row in sidecar):
        raise ValueError("Sidecar role agreement changed")
    if len(binding) != 15 or any(row["case_result"] != "PASS" or row["key_source"] != "qkd" for row in binding):
        raise ValueError("binding probe must contain 15 live-QKD PASS cases")

    sidecar.sort(key=lambda row: int(row["action_index"]))
    _, key_map = first_seen_indices([row["transport_key_id"] for row in sidecar])
    if len(key_map) != 5:
        raise ValueError("Sidecar run must contain five KeyIds")
    counts = {idx: Counter() for idx in range(1, 6)}
    for row in sidecar:
        counts[key_map[row["transport_key_id"]]][row["traffic_type"]] += 1
    expected_totals = [16, 19, 19, 19, 17]
    if [sum(counts[idx].values()) for idx in range(1, 6)] != expected_totals:
        raise ValueError("Sidecar per-KeyId action counts changed")

    # Plot the Sidecar coverage result. The Core binding campaign is retained
    # below as a hard evidence gate, but its five uniform 3/3 outcomes are more
    # informative as exact prose than as a redundant bar chart.
    fig_sidecar, ax_side = plt.subplots(figsize=(3.50, 2.38), layout="constrained")

    x = np.arange(5)
    bottoms = np.zeros(5)
    traffic_styles = {
        # Keep traffic composition neutral and distinguishable in grayscale.
        "message": (MUTED, INK, "", "Message"),
        "file": (WHITE, GOLD_DARK, "///", "File"),
        "openweb": (GRAY_LIGHT, MUTED, "", "Web fetch"),
    }
    for traffic in ["message", "file", "openweb"]:
        values = np.asarray([counts[idx][traffic] for idx in range(1, 6)])
        color, edge, hatch, label = traffic_styles[traffic]
        ax_side.bar(x, values, bottom=bottoms, width=0.62, color=color, edgecolor=edge, linewidth=0.65, hatch=hatch, label=label)
        bottoms += values
    for idx, total in enumerate(expected_totals):
        ax_side.text(idx, total + 0.45, str(total), ha="center", va="bottom", fontsize=7.2, color=INK)
    ax_side.set_xticks(x)
    ax_side.set_xticklabels([f"Key {idx}" for idx in range(1, 6)])
    ax_side.set_ylim(0, 24)
    ax_side.set_ylabel("Verified actions")
    ax_side.set_title("Sidecar coverage (90/90 IDs agreed)", loc="left", pad=4, color=INK, fontweight="semibold")
    style_axis(ax_side)
    ax_side.legend(loc="upper center", bbox_to_anchor=(0.5, 0.99), ncol=3, columnspacing=0.8, handletextpad=0.35)

    binding_order = [
        "clean_binding",
        "clean_recovery",
        "signed_top_level_frame_mismatch",
        "signed_metadata_frame_mismatch",
        "signed_both_qgp_ids_frame_mismatch",
    ]
    grouped = defaultdict(list)
    for row in binding:
        grouped[row["case"]].append(row)
    if set(grouped) != set(binding_order) or any(len(grouped[case]) != 3 for case in binding_order):
        raise ValueError("binding case composition changed")
    if sum(as_bool(row["accepted_by_response"]) for case in binding_order[:2] for row in grouped[case]) != 6:
        raise ValueError("binding clean/recovery acceptance changed")
    if sum(as_bool(row["accepted_by_response"]) for case in binding_order[2:] for row in grouped[case]) != 0:
        raise ValueError("a validly signed mismatch was accepted")

    save_figure(
        fig_sidecar,
        "fig_sidecar_key_coverage.pdf",
        {
            "question": "Does the Sidecar campaign cover every traffic type across multiple delivered QKD KeyIds?",
            "takeaway": "All 90 actions agree across four KeyId-bearing records, and every observed KeyId covers message, file, and web-fetch traffic.",
            "boundary": "This is observed identity agreement in the Sidecar campaign, joined to the sender action ledger.",
        },
    )


def write_manifest() -> None:
    manifest = {
        "schema": "paper-experiment-figures-v1",
        "source_policy": {
            "canonical_paths_only": True,
            "recursive_discovery": False,
            "failed_attempts_forbidden": True,
            "diagnostic_phase6_summary_used": False,
        },
        "inputs": _INPUT_MANIFEST,
        "outputs": _OUTPUT_MANIFEST,
        "generator_sha256": sha256(Path(__file__)),
    }
    path = OUT / "experiment_figure_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote experiment_figure_manifest.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=OUT,
        help="output directory (default: the manuscript Figures directory)",
    )
    parser.add_argument(
        "--only",
        default="all",
        help="comma-separated subset: fail-closed,performance,service,rotation,binding (default: all)",
    )
    return parser.parse_args()


def main() -> None:
    global OUT
    args = parse_args()
    OUT = args.outdir.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    generators = {
        "fail-closed": figure_fail_closed,
        "performance": figure_performance_profile,
        "service": figure_service_path_envelope,
        "rotation": figure_rotation_accounting,
        "binding": figure_key_binding,
    }
    selected = list(generators) if args.only == "all" else [item.strip() for item in args.only.split(",") if item.strip()]
    unknown = sorted(set(selected).difference(generators))
    if unknown:
        raise SystemExit(f"unknown --only value(s): {', '.join(unknown)}")
    for name in selected:
        generators[name]()
    write_manifest()
    print("done")


if __name__ == "__main__":
    main()
