# Integrated QGP Evaluation Artifact

This repository is the public evaluation companion for the manuscript
*Integrated QGP Protection for Heterogeneous Traffic over Quantum-Keyed
Software Encryptor*. It contains de-identified data supporting the paper's
figures, tables, and reported quantitative results, together with validation
and figure-generation scripts.

The release is designed to make the reported aggregates independently
checkable without exposing operational identifiers from the live testbed. It
does not contain cryptographic keys, credentials, packet captures, raw
key-management logs, or a reverse pseudonym map.

## Quick start

The numerical validation script uses only the Python standard library:

```bash
python3 scripts/reproduce_results.py
```

It validates the released experiment families and writes:

- `results/summary.json`, a structured Q1--Q5 result summary;
- `results/manuscript_values.csv`, a flat list of reproduced values.

To regenerate the data-driven manuscript figures:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/reproduce_figures.py --only fail-closed,performance,service,rotation
```

This command regenerates the five data-driven manuscript figures and also a
derived `fig_rotation_key_use.pdf` visualization of the matched-rotation table;
the latter is provided as a checking aid and is not a numbered manuscript figure.

To verify the public-release boundary and file integrity:

```bash
python3 scripts/audit_public_artifact.py
python3 scripts/checksums.py --verify
```

## Paper-to-file map

The object numbers below follow the current submission manuscript. Stable
descriptions are included so the mapping remains clear if typesetting changes
the final numbering.

| Manuscript result | Released inputs | Reproduction path |
|---|---|---|
| Q1: three shared traffic profiles and placement timing | `data/functional/core_functional_metrics.csv`, `sidecar_functional_metrics.csv` | `reproduce_results.py`; placement table |
| Q1: message/file/web protected-envelope medians (functional table) | `functional_perf_alice.jsonl`, `functional_perf_bob.jsonl`, `functional_qkd_audit.json` | `reproduce_results.py` |
| Q1: 1 KB--1 MB file-size trials | `payload_size_metrics.csv` | `reproduce_results.py` |
| Q1: 30 TCP-stream and 30 UDP-datagram trials | `tcp_stream_trials.csv`, `udp_profile_trials.csv` | `reproduce_results.py` |
| Q1: UDP complete/incomplete receiver boundary | `udp_boundary_trials.csv` | `reproduce_results.py` |
| Q1: Sidecar coverage across five KeyIds | `sidecar_key_coverage.csv` | `reproduce_results.py`; optional binding plot |
| Q2: terminal receiver stage for 30 honest and 370 negative trials (fail-closed figure) | `data/security/fail_closed_trials.csv` | `reproduce_figures.py --only fail-closed` |
| Q2: post-signing identity tampering | `post_signing_key_tamper_trials.csv` | `reproduce_results.py` |
| Q2: valid-signature KeyId consistency gate | `valid_signature_binding_trials.csv` | `reproduce_results.py` |
| Q3: nine component checkpoints (component-timing figure) | de-identified Alice/Bob functional JSONL files and QKD audit | `reproduce_figures.py --only performance` |
| Q3: concurrency operating range (service-scaling figure) | `data/performance/concurrency_trials.csv`, `concurrency_summary.csv` | `reproduce_figures.py --only service` |
| Q4: six clean/injection pairs (attack-mix figure) | `attack_mix_pairs.csv`, `attack_mix_phase_rows.csv` | `reproduce_figures.py --only service` |
| Q5: one-hour stability (rotation-stability figure) | `data/rotation/one_hour_timeline.csv`, `rotation_actions.csv` | `reproduce_figures.py --only rotation` |
| Q5: matched 30 s and 10 s rotation table | `rotation_actions.csv`, `rotation_summary.csv` | `reproduce_results.py` |
| Q5: single-key, multi-key, and Sidecar traceability results | `data/traceability/core_single_key_linkage.csv`, `core_multi_key_linkage.csv`, `data/functional/sidecar_key_coverage.csv` | `reproduce_results.py` |
| Q5: retained-event consistency check | `audit_chain_tamper_results.csv` | `reproduce_results.py` |

The manuscript's traceability-chain figure is a structural explanation of the
runtime gate and post-run joins, not a statistical plot. Its associated
quantitative claims are validated from the traceability files listed above.

## Repository layout

```text
data/
  functional/      heterogeneous traffic, placement, size, and UDP-boundary data
  security/        fail-closed, post-signing tamper, and binding-gate data
  performance/     concurrency and paired attack-mix data
  rotation/        one-hour and matched-rotation accounting data
  traceability/    cross-source linkage and retained-event checks
scripts/           numerical validation, figure generation, audit, checksums
figures/           regenerated data-driven figures
results/           regenerated aggregate values
provenance/        public-file schema, counts, hashes, and release provenance
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
- Raw packet captures and operational logs are excluded because they contain
  internal network identifiers, operational QKD KeyIds, and KME/SSH metadata.
- No symmetric key, signing private key, credential, access token, or raw key
  material is included.

The public derivatives preserve equality relationships needed for joins and
all fields needed to reproduce the released quantitative claims.

## Data availability statement

Suggested manuscript wording after the repository is public:

> The de-identified data supporting the figures, tables, and reported
> quantitative results, together with the analysis and figure-generation
> scripts, data dictionary, and provenance documentation, are available in the
> GitHub repository *Integrated QGP Evaluation Artifact* at
> https://github.com/MaoooMao/integrated-qgp-evaluation-artifact. Raw packet
> captures and operational logs containing internal network identifiers,
> operational QKD KeyIds, and KME/SSH metadata are not publicly released.

No archival DOI is assigned to this submission snapshot. If an archival DOI is
created later, it should identify an immutable release corresponding to the
accepted manuscript.

## Integrity and licensing

`CHECKSUMS.sha256` covers every versioned artifact file except the checksum file
itself. Code is released under the MIT License in [LICENSE](LICENSE). Data and
documentation are released under CC BY 4.0 as described in
[LICENSE-DATA.md](LICENSE-DATA.md).
