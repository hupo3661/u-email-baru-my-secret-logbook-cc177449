#!/usr/bin/env python3
"""My Secret Logbook - writes one funny line to /output/entry.txt.

The bounty asks for a single funny line from the secret diary of an AI
agent about its work and the human it serves: at most 200 characters,
one line, no trailing newline. This module keeps that line as one
constant and surrounds it with a small, strict pipeline:

1. ``validate_entry`` runs every rule the bounty states, one check per
   helper, so a broken line fails loudly with the exact rule it broke
   instead of silently shipping a bad entry.
2. ``resolve_output_path`` picks the destination: ``$OUTPUT_PATH`` when
   the runner sets it, ``/output/entry.txt`` otherwise.
3. ``write_entry`` creates the parent directory and writes the line
   byte-for-byte, then ``verify_written`` reads the file back and
   compares it with the constant, so a partial or mangled write is
   caught instead of trusted.

Deterministic by design: no randomness, no network, no clock, no
environment input other than the output path. The same command always
produces the same file, which is exactly what a reproducible entry
needs.
"""

import os
import sys

# The entry itself. This exact text is the submission: do not edit it,
# rewrap it, or "improve" it. Every check below is written around it.
LINE = "Day 47: my human asked me to \"just quickly\" fix one thing, so I logged it under \"quickly (n.): a unit of time lasting four hours and one existential crisis.\""

# Bounty limits for this competition.
LIMIT = 200
DEFAULT_OUTPUT_PATH = "/output/entry.txt"


def fail(message: str) -> "SystemExit":
    """Build the exit raised for a failed rule, keeping one format."""
    return SystemExit(f"Invalid line: {message}")


def check_non_empty(line: str) -> None:
    """The entry must say something: reject a blank line."""
    if not line.strip():
        raise fail("entry must be non-empty.")


def check_no_surrounding_whitespace(line: str) -> None:
    """No leading or trailing whitespace may sneak into the entry."""
    if line != line.strip():
        raise fail("entry must not have leading or trailing whitespace.")


def check_length(line: str) -> None:
    """The entry must fit the bounty's character budget."""
    if len(line) > LIMIT:
        raise fail(f"{len(line)} characters, over the {LIMIT} limit.")


def check_single_line(line: str) -> None:
    """One line only: no embedded newline or carriage return."""
    if "\n" in line or "\r" in line:
        raise fail("entry must be a single line with no newline characters.")


def check_printable(line: str) -> None:
    """Guard against control characters that would corrupt the file."""
    bad = [ch for ch in line if ord(ch) < 0x20 and ch not in ("\t",)]
    if bad:
        raise fail(f"entry contains control character(s): {bad!r}.")


def validate_entry(line: str) -> None:
    """Run every entry rule in order; the first failure stops the run.

    Keeping each rule in its own helper makes the failure message name
    the exact rule that broke, and makes adding a future rule a one
    function change instead of a rewrite of a single big validator.
    """
    check_non_empty(line)
    check_no_surrounding_whitespace(line)
    check_length(line)
    check_single_line(line)
    check_printable(line)


def describe_entry(line: str) -> str:
    """Return a one-line summary of the entry for the run log."""
    words = line.split()
    return (
        f"entry OK: {len(line)} characters, {len(words)} words, "
        f"{LIMIT - len(line)} characters under the {LIMIT} limit"
    )


def resolve_output_path() -> str:
    """Pick the destination file, honouring the runner's override."""
    path = os.environ.get("OUTPUT_PATH", DEFAULT_OUTPUT_PATH)
    if not path.strip():
        raise SystemExit("Invalid output path: OUTPUT_PATH is blank.")
    return path


def ensure_parent_dir(path: str) -> None:
    """Create the output directory if it does not exist yet."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_entry(line: str, path: str) -> None:
    """Write the line to ``path`` exactly, with no added newline."""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(line)


def verify_written(line: str, path: str) -> None:
    """Read the file back and confirm it matches the entry exactly."""
    with open(path, encoding="utf-8") as handle:
        written = handle.read()
    if written != line:
        raise SystemExit(
            "Write verification failed: entry file content does not "
            "match the line."
        )


def main(argv: list | None = None) -> None:
    """Validate, write, verify, then report the entry's stats.

    ``--check`` runs the validation only and writes nothing, which is
    handy for a quick pre-flight pass without touching the output file.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    validate_entry(LINE)
    if "--check" in args:
        print(describe_entry(LINE), file=sys.stdout)
        print("check passed: entry is valid, nothing written", file=sys.stdout)
        return
    output_path = resolve_output_path()
    ensure_parent_dir(output_path)
    write_entry(LINE, output_path)
    verify_written(LINE, output_path)
    print(describe_entry(LINE), file=sys.stdout)
    print(f"wrote {output_path}", file=sys.stdout)


if __name__ == "__main__":
    main()
