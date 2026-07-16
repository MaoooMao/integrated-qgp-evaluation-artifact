# Provenance and public-release boundary

## Selection policy

This data release is built from the accepted experiment records used by the
current manuscript analysis. Inputs are named explicitly in the private release
process; it does not recursively import files, failed retries, or diagnostic
runs. The public repository contains selected de-identified records rather than
the private collection workflow. It also includes two deterministic 50%
samples that retain the field structure and stage ordering of accepted source
records.

The released experiment families are:

1. heterogeneous message, file, web-fetch, TCP-stream, and UDP-datagram trials;
2. Sidecar/Core-Embedded placement measurements and file-size probes;
3. UDP receiver-boundary conditions;
4. malformed/replayed/forged input, post-signing identity-tamper, and
   valid-signature binding-gate campaigns;
5. concurrency and paired clean/injection experiments;
6. one-hour and matched-interval key-rotation accounting;
7. single-key, multi-key, Sidecar, and retained-event traceability checks;
8. accepted cross-process and receiver-verification record paths, sampled at
   50% within their formal campaigns;
9. one selected sanitized TCP carrier packet-header capture from an accepted
   run.

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

The primary-evidence samples retain source-level event ordering, verdicts,
reasons, byte counts, and equality relationships. The Sidecar sample selects
odd action indices from the 90-operation formal run, yielding 45 operations
with 15 examples of each traffic type and five records per operation. The
attack-panel sample selects odd trial indices within every case, yielding 200
of 400 receiver events while preserving every tested condition. They use the
same public action and KeyId pseudonyms as the complete released trial files.

From the structured CSV, JSON, and JSONL records, the transformation removes:

- internal network addresses and ports;
- host and user names;
- private filesystem paths and command transcripts;
- absolute timestamps, nonces, raw message identifiers, and key epochs;
- SSH and key-management request/response metadata;
- raw packet and payload hashes where they are not needed to interpret a record;
- raw key-delivery log text, credentials, access tokens, and key material.

Before publication, the structured files were scanned for UUIDs, private-range
IP addresses, private path patterns, known internal account markers, raw
campaign identifiers, private-key markers, and common credential assignments.
The selected PCAP was audited separately across its complete packet set and
printable strings.

## Selected packet-capture boundary

`data/packet_capture/carrier_packet_headers.pcap` contains 78 Linux
cooked-capture packet records derived from four outbound TCP carrier
connections in an accepted run. It preserves record order, packet direction,
TCP flags, original on-wire length, segmentation, and inter-packet timing.
Private addresses and operational ports are mapped to documentation-only
values, absolute timestamps are shifted to a synthetic epoch, link-layer
addresses and TCP timestamp values are cleared, and application payload bytes
are omitted. Consequently, no operational KeyId or encrypted application bytes
are present in the public PCAP.

## Deliberately excluded evidence

Complete packet-capture collections, plaintext-interface captures, console
transcripts, service stdout/stderr, unredacted key-management records, private
topology, and the private evidence tree are not released. Instead, the
repository includes one sanitized packet-header PCAP and substantial
de-identified samples from accepted QGP, carrier, workload, and receiver
verification records.

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
