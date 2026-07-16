# Provenance and public-release boundary

## Selection policy

This data release is built from the accepted experiment records used by the
current manuscript analysis. Inputs are named explicitly in the private release
process; it does not recursively import files, failed retries, or diagnostic
runs. The public repository contains the selected de-identified records rather
than the private collection workflow.

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
complete versioned data release.

## De-identification transformation

Operational key, action, and run identifiers are replaced by stable public
pseudonyms. The same source value receives the same public label wherever it is
needed for a released join, but the reverse mapping is not written to the
repository. Absolute timestamps are either removed or represented by retained
relative elapsed time. Operationally unnecessary fields are removed rather than
masked in place.

The transformation removes:

- internal network addresses and ports;
- host and user names;
- private filesystem paths and command transcripts;
- absolute timestamps, nonces, raw message identifiers, and key epochs;
- SSH and key-management request/response metadata;
- raw packet and payload hashes where they are not needed to interpret a record;
- raw key-delivery log text, credentials, access tokens, and key material.

Before publication, the released files were scanned for UUIDs, private-range IP
addresses, private path patterns, known internal account markers, raw campaign
identifiers, private-key markers, and common credential assignments.

## Deliberately excluded evidence

Raw packet captures, console transcripts, service stdout/stderr, unredacted
key-management records, full packet/payload contents, private topology, and the
private evidence tree are not released. These materials contain operational
identifiers and are not necessary for inspecting the paper's released records.

The release supports evidence inspection without enabling reconstruction of the
laboratory network or replay of a live key-management session. The final
traceability hop is represented by de-identified match/hit outcomes rather than
the original key-management log lines.

## Intended use

The repository is a data-access companion, not a software distribution or a
turnkey reproduction environment. Researchers may inspect or analyze the CSV,
JSON, and JSONL records with tools of their choice. The data dictionary defines
the released fields, and the paper-to-file table in `README.md` identifies which
records support each experiment family.

The public data should be treated as a submission snapshot. An archival DOI, if
created after acceptance or upon editorial request, should point to an immutable
release corresponding to the accepted manuscript.
