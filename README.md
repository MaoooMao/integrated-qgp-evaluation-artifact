# Integrated QGP Evaluation Data

This repository contains the de-identified experimental records supporting the
figures and tables in the manuscript *Integrated QGP Protection for
Heterogeneous Traffic over Quantum-Keyed Software Encryptor*.

The release is intentionally data-focused. It provides event-level and
trial-level experimental records, field definitions, paper-to-file mapping, and
provenance needed to inspect the reported evidence with standard CSV/JSON
tools. Two structure-preserving primary-evidence datasets release deterministic
50% samples of the formal Sidecar run and attack-panel campaign without
distributing complete operational logs. The repository does not include project
source code, analysis or plotting scripts, generated figures, or precomputed
result summaries.

## Paper-to-file map

The object numbers below follow the current submission manuscript. The stable
descriptions keep the mapping understandable if final typesetting changes a
number.

| Manuscript evidence | Released records |
|---|---|
| Q1: three shared traffic profiles and placement timing | `data/functional/core_functional_metrics.csv`, `data/functional/sidecar_functional_metrics.csv` |
| Q1: message/file/web protected-envelope medians | `data/functional/functional_perf_alice.jsonl`, `functional_perf_bob.jsonl`, `functional_qkd_audit.json` |
| Q1: 1 KB--1 MB file-size trials | `data/functional/payload_size_metrics.csv` |
| Q1: 30 TCP-stream and 30 UDP-datagram trials | `data/functional/tcp_stream_trials.csv`, `udp_profile_trials.csv` |
| Q1: UDP complete/incomplete receiver boundary | `data/functional/udp_boundary_trials.csv` |
| Q1: Sidecar coverage across five KeyIds | `data/functional/sidecar_key_coverage.csv` |
| Q2: 30 honest and 370 malformed/replayed/forged trials | `data/security/fail_closed_trials.csv` |
| Q2: post-signing identity tampering | `data/security/post_signing_key_tamper_trials.csv` |
| Q2: valid-signature KeyId consistency gate | `data/security/valid_signature_binding_trials.csv` |
| Q1/Q5: 45/90 accepted operations across five cross-process stages | `data/primary_evidence/sidecar_accepted_trace.jsonl` |
| Q2: 200/400 receiver events, sampled at 50% within every attack-panel case | `data/primary_evidence/attack_panel_receiver_events.jsonl` |
| Q3: nine component checkpoints | the de-identified Alice/Bob functional JSONL files and QKD audit above |
| Q3: concurrency operating range | `data/performance/concurrency_trials.csv`, `concurrency_summary.csv` |
| Q4: six clean/injection pairs | `data/performance/attack_mix_pairs.csv`, `attack_mix_phase_rows.csv` |
| Q5: one-hour stability | `data/rotation/one_hour_timeline.csv`, `rotation_actions.csv` |
| Q5: matched 30 s and 10 s rotation comparison | `data/rotation/rotation_actions.csv`, `rotation_summary.csv` |
| Q5: single-key, multi-key, and Sidecar traceability | `data/traceability/core_single_key_linkage.csv`, `core_multi_key_linkage.csv`, and `data/functional/sidecar_key_coverage.csv` |
| Q5: retained-event consistency check | `data/traceability/audit_chain_tamper_results.csv` |

The manuscript's traceability-chain figure is a structural explanation rather
than a statistical plot. Its quantitative evidence is represented by the
traceability records listed above.

## Repository layout

```text
data/
  functional/      heterogeneous traffic, placement, size, and UDP records
  security/        fail-closed, post-signing tamper, and binding-gate records
  performance/     concurrency and paired attack-mix records
  rotation/        one-hour and matched-rotation records
  traceability/    cross-source linkage and retained-event records
  primary_evidence/ 50% samples of accepted source-event records
provenance/
  data_manifest.json   row counts, fields, sizes, and hashes for every data file
```

See [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for field definitions and
[PROVENANCE.md](PROVENANCE.md) for source selection, de-identification, and
exclusion rules.

## De-identification and exclusions

- Operational QKD identifiers are replaced consistently by `KID-###` labels.
- Action and run identifiers are replaced by `ACT-######` and `RUN-####`.
- Absolute timestamps, network addresses and ports, host/user names, private
  paths, nonces, key epochs, and raw key-management text are removed.
- The reverse pseudonym mappings are not retained in this repository.
- Substantial de-identified primary-record samples are included; complete
  packet captures and full operational logs are excluded because they contain
  internal network identifiers, operational QKD KeyIds, and KME/SSH metadata.
- No symmetric key, signing private key, credential, access token, or raw key
  material is included.

The de-identified records preserve equality relationships needed to interpret
the released cross-file joins.

## Data availability statement

Suggested manuscript wording:

> The de-identified event-level and trial-level records supporting the figures
> and tables, together with de-identified primary-evidence samples, a data
> dictionary, and provenance documentation, are available in the GitHub
> repository *Integrated QGP Evaluation Data* at
> https://github.com/MaoooMao/integrated-qgp-evaluation-artifact. Full
> unredacted packet captures and operational logs containing internal network
> identifiers, operational QKD KeyIds, and key-management entity (KME)/SSH
> metadata are not publicly released.

No archival DOI is assigned to this submission snapshot. If an archival DOI is
created later, it should identify an immutable release corresponding to the
accepted manuscript.

## Integrity, citation, and license

`CHECKSUMS.sha256` covers every versioned file except the checksum file itself.
It can be checked with a standard SHA-256 utility, for example:

```bash
shasum -a 256 -c CHECKSUMS.sha256
```

Citation metadata are provided in [CITATION.cff](CITATION.cff). The data and
documentation are released under CC BY 4.0; see [LICENSE](LICENSE).
