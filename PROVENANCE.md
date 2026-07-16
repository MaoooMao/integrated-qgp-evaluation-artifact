# Provenance and public-release boundary

## Selection policy

This artifact is built from the accepted experiment inputs used by the current
manuscript analysis. Inputs are named explicitly in the private build process;
the builder does not recursively discover files, import failed retries, or mix
diagnostic runs into the release. The public numerical and plotting scripts in
this repository likewise name every released input explicitly.

The released experiment families are:

1. heterogeneous message, file, web-fetch, TCP-stream, and UDP-datagram trials;
2. Sidecar/Core-Embedded placement measurements and file-size probes;
3. UDP receiver-boundary conditions;
4. malformed/replayed/forged input, post-signing identity-tamper, and
   valid-signature binding-gate campaigns;
5. concurrency and paired clean/injection experiments;
6. one-hour and matched-interval key-rotation accounting;
7. single-key, multi-key, Sidecar, and retained-event traceability checks.

`provenance/data_manifest.json` records the row count, field list, byte count,
and SHA-256 digest of every released data file. `CHECKSUMS.sha256` covers the
complete versioned public artifact.

## De-identification transformation

Operational key, action, and run identifiers are replaced by stable public
pseudonyms. The same source value receives the same public label wherever it is
needed for a released join, but the reverse mapping is not written to the
artifact. Absolute timestamps are either removed or represented by already
retained relative elapsed time. Operationally unnecessary fields are removed
rather than masked in place.

The transformation removes:

- internal network addresses and ports;
- host and user names;
- private filesystem paths and command transcripts;
- absolute timestamps, nonces, raw message identifiers, and key epochs;
- SSH and key-management request/response metadata;
- raw packet and payload hashes where they are not needed for a released claim;
- raw key-delivery log text, credentials, access tokens, and key material.

The public audit script scans the final repository for UUIDs, IP addresses,
private path patterns, known internal account markers, raw campaign identifiers,
private-key markers, and common credential assignments.

## Deliberately excluded evidence

Raw packet captures, console transcripts, service stdout/stderr, unredacted
key-management records, full packet/payload contents, private topology, and the
private evidence tree are not released. These materials contain operational
identifiers and are not necessary to recompute the paper's released aggregates.

The release therefore supports result verification, not reconstruction of the
laboratory network or replay of the live key-management session. The final
traceability hop is represented by de-identified match/hit outcomes rather than
the original key-management log lines.

## Reproducibility checks

`scripts/reproduce_results.py` validates sample counts, success/failure policy,
cross-file joins, summary statistics, confidence intervals, rotation accounting,
and traceability totals before writing `results/summary.json`.

`scripts/reproduce_figures.py` is adapted from the manuscript's locked figure
generator. It operates only on the public files and writes a figure manifest
with the inputs, outputs, hashes, and scientific boundary of each chart.

The public artifact should be considered a submission snapshot. An archival DOI,
if created after acceptance or upon editorial request, should point to an
immutable release of this repository.
