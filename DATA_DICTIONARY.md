# Data dictionary

All tabular files use UTF-8. CSV files have one header row; JSONL files contain
one JSON object per line. Empty strings represent unavailable or inapplicable
measurements and are never silently imputed.

## Common conventions

| Field pattern | Meaning |
|---|---|
| `KID-###` | Stable public pseudonym for one operational QKD KeyId. Equality is preserved across released files; no reverse map is released. |
| `ACT-######` | Stable public pseudonym for an action, service action, or datagram identifier. |
| `RUN-####` | Stable public pseudonym for a retained run identifier. |
| `*_ms` | Duration in milliseconds. |
| `*_s`, `*_seconds` | Duration or relative offset in seconds. |
| `*_bytes` | Byte count. `MB` fields use the units retained by the accepted analysis. |
| `PASS` / `FAIL` | Outcome under the campaign's declared acceptance rule. |
| Boolean fields | Serialized as `True`/`False`, `YES`/`NO`, or `1`/`0` according to the accepted source. |
| `openweb` | The manuscript's web-fetch workload. |

## Functional data

### `core_functional_metrics.csv` and `sidecar_functional_metrics.csv`

Thirty message, file, and web-fetch actions per placement.

- `run_id`: public run pseudonym.
- `placement`: `core_embedded` or `sidecar`.
- `traffic`: `message`, `file`, or `openweb`.
- `result`: action result.
- `elapsed_ms`: driver-observed action time.
- `application_or_target_bytes`: application payload or requested target size.
- `response_bytes`: returned response size when the workload has one.

### `payload_size_metrics.csv`

Adds `configured_file_bytes` to the functional metric fields above. It contains
ten Core-Embedded file trials at each of 1,024, 4,096, 65,536, and 1,048,576
bytes.

### `functional_perf_alice.jsonl` and `functional_perf_bob.jsonl`

De-identified endpoint checkpoint rows used for protected-envelope medians and
the component-timing figure.

- `service_action_id`, `transport_key_id`: public join identifiers.
- `traffic_type`, `verdict`, `sequence`: workload type, verification outcome,
  and retained action sequence.
- `request_payload_bytes`, `response_payload_bytes`: application bytes.
- `request_qgp_envelope_bytes`, `response_qgp_envelope_bytes`: serialized QGP
  envelope bytes before carrier framing.
- `request_qgp_build_sign_ms`, `response_qgp_build_sign_ms`: envelope build and
  signing checkpoints.
- `request_qgp_verify_ms`, `response_qgp_verify_ms`: verification checkpoints.
- `request_core_encrypt_send_ms`, `response_core_encrypt_send_ms`: carrier
  encryption/send checkpoints.
- `request_core_recv_decrypt_ms`, `response_core_recv_decrypt_ms`: carrier
  receive/decrypt checkpoints.
- `app_roundtrip_ms`: receiver-side application round trip.

Fields not applicable to one endpoint are absent rather than fabricated.

### `functional_qkd_audit.json`

- `qkd_expected`: whether the selected campaign required QKD-sourced carrier keys.
- `transport_key_id_candidate_count`: number of observed candidates.
- `transport_key_id_candidates`: de-identified candidates used to validate the
  checkpoint join.

### `tcp_stream_trials.csv`

- `trial`, `action_id`, `transport_key_id`: trial and public join identifiers.
- `payload_bytes`: application bytes in one stream transfer.
- `stream_chunk_size_limit`: configured maximum application bytes per signed chunk.
- `signed_chunk_count`: signed QGP chunks in the transfer.
- `qgp_envelope_bytes`: aggregate serialized QGP envelope bytes for the transfer.
- `encrypted_frame_bytes`: carrier-frame bytes.
- `sender_verdict`, `receiver_verdict`: endpoint results.

### `udp_profile_trials.csv`

- `trial`, `action_id`, `transport_key_id`: trial and public join identifiers.
- `payload_bytes`, `qgp_envelope_bytes`, `encrypted_frame_bytes`: byte counts.
- `wire_datagrams`: user-space carrier fragments emitted for the protected datagram.
- `qgp_build_sign_ms`, `core_encrypt_ms`, `udp_send_ms`: sender checkpoints.
- `core_decrypt_ms`, `qgp_verify_ms`, `application_udp_send_ms`: receiver checkpoints.
- `result`: joined sender/receiver outcome.

### `udp_boundary_trials.csv`

- `case`, `trial`, `action_id`: condition, repeat, and public action identifier.
- `expected_verified_delivery`: expected complete/incomplete-input outcome.
- `payload_bytes`, `qgp_envelope_bytes`, `encrypted_frame_bytes`: byte counts.
- `total_chunks`, `sent_chunks`, `wire_datagrams_sent`: chunk/datagram counts.
- `dropped_chunk_count`, `duplicated_chunk_count`, `reorder_swap_count`,
  `loss_rate`: applied receiver-boundary perturbation.
- `transport_key_id`: public key identifier.
- `send_error_present`: whether the sender observed an error; error text is removed.
- `verified_delivery_count`, `application_plaintext_count`: observed deliveries.
- `false_verified_delivery`, `false_plaintext_delivery`, `missing_delivery`,
  `duplicate_delivery`: policy-violation flags.
- `trial_result`: complete trial verdict.

### `sidecar_key_coverage.csv`

- `action_index`, `action_id`, `scheduled_offset_seconds`: public action order and
  relative schedule.
- `traffic_type`, `transport_key_id`: workload and public key identifier.
- `sender_pass`, `alice_qgp_pass`, `bob_qgp_pass`, `alice_carrier_pass`,
  `bob_carrier_pass`: agreement checks across the retained Sidecar records.
- `validation_errors`, `result`: validation detail and final outcome.

## Security data

### `fail_closed_trials.csv`

- `case`, `trial`, `action_id`: negative-input class, repeat, and public action.
- `expected_accept`, `accepted_by_response`: expected and observed delivery decision.
- `response_bytes`, `frame_bytes`: retained byte counts.
- `send_error_present`: sender-error presence without operational error text.
- `transport_key_id`: public key identifier.
- `bob_qgp_result`, `bob_qgp_reason`: receiver verification result and protocol-level
  reason.
- `appserver_b_plaintexts_for_attack_send`: application plaintext deliveries caused
  by the tested send.
- `app_plaintext_policy_ok`, `trial_result`: policy and whole-trial outcomes.

### `post_signing_key_tamper_trials.csv`

- `campaign`: main 180-trial campaign or post-clean recovery.
- `case`, `index`, `expected`, `accepted_by_response`: condition and outcome.
- `response_bytes`, `frame_bytes`, `send_error_present`: retained transport evidence.
- `transport_key_id`: public key identifier.
- `case_result`: whether observation matched the declared expectation.

### `valid_signature_binding_trials.csv`

- `case`, `index`, `expected`, `case_result`, `accepted_by_response`: condition and
  outcome.
- `response_bytes`, `frame_bytes`, `send_error_present`: retained transport evidence.
- `key_source`: required key-source policy (`qkd`).
- `transport_key_id`, `signed_top_level_key_id`, `signed_transport_key_id`,
  `frame_transport_key_id`: public identifiers used to exercise the consistency gate.

## Performance data

### `concurrency_trials.csv`

- `run_id`: public run pseudonym.
- `expected_key_source`: required source policy.
- `measurement_semantics`: definition of a verified completion.
- `clients`, `repeat_index`, `duration_s`, `message_size`: workload controls.
- `result`, `attempted`, `verified_ok`, `verified_fail`: repeat outcomes.
- `verified_request_per_second`, `verified_payload_MB_per_second`: verified rates.
- `e2e_latency_mean_ms`, `e2e_latency_median_ms`, `e2e_latency_p95_ms`,
  `e2e_latency_p99_ms`: end-to-end latency statistics.

### `concurrency_summary.csv`

- `clients`, `repeats`, `pass`: load level and successful repeats.
- `verified_ok`, `verified_fail`: aggregate action outcomes.
- `verified_rps_mean`, `verified_rps_sd`: mean and sample standard deviation.
- `e2e_p95_ms_mean`: mean of per-repeat P95 latency.

### `attack_mix_pairs.csv`

- `pair_index`: matched clean/injection pair.
- `baseline_verified_rps`, `attack_verified_rps`, `throughput_change_pct`: verified
  throughput comparison.
- `baseline_e2e_p95_ms`, `attack_e2e_p95_ms`, `p95_change_pct`: latency comparison.
- `attack_rate`, `attack_offered_fps`, `achieved_attack_fraction`: injection rate.
- `attack_sent`, `attack_responses`, `attack_errors`, `result`: injector outcomes.

### `attack_mix_phase_rows.csv`

- `pair_index`, `phase`, `run_id`: pair, clean/injection phase, and public run.
- `key_source`, `clients`, `duration_s`: controls.
- `honest_result`, `honest_attempted`, `honest_verified_ok`,
  `honest_verified_fail`, `honest_verified_request_per_second`,
  `honest_e2e_latency_p95_ms`: honest workload outcomes.
- `attack_rate`, `attack_duration_s`, `attack_sent`, `attack_responses`,
  `attack_no_response`, `attack_errors`, `attack_unique_transport_key_ids`:
  injection outcomes. The original identifier list is deliberately omitted.

## Rotation data

### `rotation_actions.csv`

- `source`: one-hour anchor, 30-second probe, or 10-second probe.
- `rotation_seconds`, `action_index`, `traffic`, `result`, `evidence_match`: controls
  and action outcome.
- `transport_key_id`: public key identifier.
- request/response/application and encrypted-frame `*_bytes`: action byte counts.
- `key_fetch_ms`, `app_elapsed_ms`: key-fetch and driver-observed action time.

### `rotation_summary.csv`

- `rotation_seconds`, `actions`, `pass`: setting and success counts.
- `unique_key_ids`, `unique_epochs`: distinct accepted-analysis counts.
- `actions_per_key_id`: verified actions divided by used KeyIds.
- application/encrypted-frame `*_bytes` and `*_MB_per_key_id`: traffic accounting.
- `key_fetch_median_ms`, `key_fetch_p95_ms`: key-fetch checkpoints.
- `traffic_counts`: retained per-traffic action-count dictionary.

### `one_hour_timeline.csv`

- `run_id`, `sample`, `elapsed_s`, `traffic`, `result`: public action and relative time.
- `app_elapsed_ms`: action latency; one missing historical value remains empty.
- `plain_or_target_bytes`, `response_bytes`: workload byte counts.
- Alice/Bob `transport_key_id` and QGP-result fields: endpoint agreement evidence.

## Traceability data

### `core_single_key_linkage.csv`

One detailed KeyId trace. Fields report the number of QGP verification-log rows
and Boolean agreement at sender/receiver logs, workload summary, both retained
backbone observations, source key delivery, and destination key retrieval.

### `core_multi_key_linkage.csv`

One row per public KeyId. `sender_qgp_event_count` and
`receiver_qgp_event_count` count matched events; the remaining fields record
destination key-retrieval hits, sender/receiver backbone agreement, and result.

### `audit_chain_tamper_results.csv`

- `run_id`: public run pseudonym.
- `modified_event_position`: injected modification location in a 100-event chain.
- `detected`, `verifier_result`, `reason`: consistency-check outcome.
