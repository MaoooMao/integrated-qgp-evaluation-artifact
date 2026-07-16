# Integrated QGP Evaluation Data

This repository provides the public data companion for the manuscript
*Integrated QGP Protection for Heterogeneous Traffic over Quantum-Keyed
Software Encryptor*. It contains the experimental records used to evaluate
heterogeneous protected traffic, fail-closed verification, performance and
concurrency, key rotation, and KeyId traceability.

## Paper

**Integrated QGP Protection for Heterogeneous Traffic over Quantum-Keyed
Software Encryptor**

The release is organized around the five evaluation questions in the paper.
Citation metadata for the repository are provided in [CITATION.cff](CITATION.cff);
the article DOI can be added there after publication.

## Release contents

- 25 structured CSV, JSON, and JSONL files containing 2,305 experimental,
  event, and evidence-linkage records;
- two primary-evidence datasets containing 425 records sampled from the formal
  Sidecar and attack-panel campaigns;
- one sanitized PCAP containing 78 packet-header records derived from an
  accepted carrier run;
- a data dictionary, provenance notes, a machine-readable manifest, and
  SHA-256 checksums.

No installation is required to inspect the release. The repository is a data
companion rather than a source-code or end-to-end reproduction package.

## Data-to-paper map

| Evaluation question | Released evidence |
|---|---|
| Q1: heterogeneous traffic and placement | `data/functional/`, `data/primary_evidence/sidecar_accepted_trace.jsonl`, `data/packet_capture/` |
| Q2: fail-closed rejection and KeyId consistency | `data/security/`, `data/primary_evidence/attack_panel_receiver_events.jsonl` |
| Q3: processing checkpoints and concurrent load | `data/functional/functional_perf_*.jsonl`, `data/performance/concurrency_*.csv` |
| Q4: normal traffic under injected invalid frames | `data/performance/attack_mix_pairs.csv`, `data/performance/attack_mix_phase_rows.csv` |
| Q5: rotation and post-run traceability | `data/rotation/`, `data/traceability/`, `data/functional/sidecar_key_coverage.csv` |

Exact field definitions and per-file descriptions are available in
[DATA_DICTIONARY.md](DATA_DICTIONARY.md).

## Repository structure

```text
data/
  functional/       heterogeneous traffic, placement, size, and UDP records
  security/         fail-closed, tamper, and KeyId-binding records
  performance/      concurrency and paired attack-mix records
  rotation/         one-hour and matched-rotation records
  traceability/     cross-source linkage and retained-event checks
  primary_evidence/ sampled source-event records
  packet_capture/   sanitized carrier packet-header trace
provenance/
  data_manifest.json
DATA_DICTIONARY.md
PROVENANCE.md
CHECKSUMS.sha256
CITATION.cff
```

## Using the release

CSV files contain one header row. JSONL files contain one JSON object per line.
The PCAP can be opened with Wireshark or another packet-analysis tool. The
manifest records the row count, fields, size, and SHA-256 digest of every data
file.

To verify the release:

```bash
shasum -a 256 -c CHECKSUMS.sha256
```

## Release boundary

Operational KeyIds, action identifiers, and run identifiers in the structured
records are replaced by stable public pseudonyms so that cross-file equality
relationships remain inspectable. Network addresses, absolute timestamps,
nonces, private paths, and key-management metadata are removed from those
records.

The packet trace preserves packet order, direction, TCP flags, original wire
length, segmentation, and relative timing. Addresses and ports are mapped to
documentation-only values, timestamps are shifted, and application payload
bytes are omitted.

Complete packet-capture collections, plaintext-interface captures, KME/SSH
captures, full operational logs, credentials, and key material are not part of
the release. See [PROVENANCE.md](PROVENANCE.md) for the complete selection and
transformation policy.

## Citation and license

Please use [CITATION.cff](CITATION.cff) when citing this dataset. The data and
documentation are released under CC BY 4.0; see [LICENSE](LICENSE).
