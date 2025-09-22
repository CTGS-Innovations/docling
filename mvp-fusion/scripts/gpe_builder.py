#!/usr/bin/env python3
import argparse
import datetime
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def read_text_file(path: Path) -> List[str]:
    with path.open('r', encoding='utf-8') as f:
        return f.read().splitlines()


def write_text_file(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for line in lines:
            f.write(f"{line}\n")


def slugify(title: str) -> str:
    normalized = title.strip()
    normalized = normalized.replace('&', 'and')
    # Remove surrounding === markers if present
    normalized = re.sub(r'^=+\s*', '', normalized)
    normalized = re.sub(r'\s*=+$', '', normalized)
    # Lowercase alnum + spaces/underscores only
    normalized = normalized.lower()
    normalized = re.sub(r'[^a-z0-9\s_-]+', '', normalized)
    normalized = re.sub(r'\s+', '_', normalized).strip('_')
    return normalized or 'section'


def parse_sections(lines: List[str]) -> Tuple[List[str], List[Tuple[str, List[str]]]]:
    header_lines: List[str] = []
    sections: List[Tuple[str, List[str]]] = []

    section_title: str = ''
    section_buffer: List[str] = []

    header_pattern = re.compile(r'^#\s*=+\s*(.+?)\s*=+\s*$')

    for idx, raw in enumerate(lines):
        match = header_pattern.match(raw)
        if match:
            # flush previous section if any
            if section_title:
                sections.append((section_title, section_buffer))
                section_buffer = []
            # start new section
            section_title = match.group(1).strip()
            continue

        if section_title:
            if raw.strip() == '':
                # preserve blank lines within a section
                section_buffer.append(raw)
            else:
                # skip comment-like lines within section headers (rare)
                section_buffer.append(raw)
        else:
            # before the first section: treat as header comments
            header_lines.append(raw)

    # flush last
    if section_title:
        sections.append((section_title, section_buffer))

    return header_lines, sections


def cmd_split(input_path: Path, outdir: Path) -> None:
    lines = read_text_file(input_path)
    header, sections = parse_sections(lines)

    if not sections:
        raise SystemExit("No sections found to split. Ensure headers are formatted like '# === TITLE ==='.")

    order_filenames: List[str] = []

    for title, content in sections:
        filename = f"{slugify(title)}.txt"
        order_filenames.append(filename)
        target = outdir / filename
        out_lines: List[str] = [f"# === {title} ==="]
        # trim leading/trailing blank lines for cleanliness
        trimmed = list(content)
        while trimmed and trimmed[0].strip() == '':
            trimmed.pop(0)
        while trimmed and trimmed[-1].strip() == '':
            trimmed.pop()
        out_lines.extend(trimmed)
        write_text_file(target, out_lines)

    # Write an order file to preserve section order when rebuilding
    write_text_file(outdir / 'order.txt', order_filenames)

    # Save a header file for reuse when building
    header_clean = [h for h in header if h.strip() != '']
    if header_clean:
        write_text_file(outdir / 'HEADER.txt', header_clean)

    print(f"Wrote {len(order_filenames)} section files to {outdir}")


def discover_section_files(subdir: Path) -> List[Path]:
    files = [p for p in subdir.glob('*.txt') if p.name not in {'order.txt', 'HEADER.txt'}]
    return files


def load_order(subdir: Path, files: List[Path]) -> List[Path]:
    order_path = subdir / 'order.txt'
    if not order_path.exists():
        return sorted(files, key=lambda p: p.name)
    desired_order = [line.strip() for line in read_text_file(order_path) if line.strip()]
    name_to_file: Dict[str, Path] = {p.name: p for p in files}
    ordered: List[Path] = [name_to_file[name] for name in desired_order if name in name_to_file]
    remaining = [p for p in files if p.name not in desired_order]
    ordered.extend(sorted(remaining, key=lambda p: p.name))
    return ordered


def unique_target_path(base_dir: Path, base_name: str) -> Path:
    candidate = base_dir / base_name
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    # prefer _built suffix first
    built = base_dir / f"{stem}_built{suffix}"
    if not built.exists():
        return built
    # increment
    i = 2
    while True:
        numbered = base_dir / f"{stem}_built_{i}{suffix}"
        if not numbered.exists():
            return numbered
        i += 1


def cmd_build(subdir: Path, outdir: Path, date_str: str | None, include_headers: bool, dedupe: bool) -> None:
    files = discover_section_files(subdir)
    if not files:
        raise SystemExit(f"No section files found in {subdir}")

    files = load_order(subdir, files)

    today = datetime.date.today()
    if date_str:
        try:
            # Accept YYYY-MM-DD or YYYY_MM_DD
            cleaned = date_str.replace('_', '-')
            dt = datetime.date.fromisoformat(cleaned)
        except ValueError:
            raise SystemExit("--date must be in YYYY-MM-DD or YYYY_MM_DD format")
    else:
        dt = today

    target_name = f"geopolitical_entities_{dt.year:04d}_{dt.month:02d}_{dt.day:02d}.txt"
    target_path = unique_target_path(outdir, target_name)

    output: List[str] = []

    header_path = subdir / 'HEADER.txt'
    if header_path.exists():
        output.extend(read_text_file(header_path))

    seen: set[str] = set()

    for path in files:
        if include_headers:
            # Synthesize a section header from the first line if present, else from filename
            first_line = ''
            try:
                first_line = read_text_file(path)[0]
            except IndexError:
                first_line = ''
            if first_line.startswith('# ==='):
                output.append('')
                output.append(first_line)
            else:
                title = path.stem.replace('_', ' ').title()
                output.append('')
                output.append(f"# === {title} ===")

        # Append data lines, skipping local headers
        for line in read_text_file(path):
            if line.startswith('# ==='):
                continue
            if dedupe:
                key = line.strip()
                if key == '' or key in seen:
                    continue
                seen.add(key)
                output.append(line)
            else:
                output.append(line)

    write_text_file(target_path, output)
    print(f"Built superset: {target_path}")


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GPE builder: split monolith into subfiles and build superset.")
    sub = parser.add_subparsers(dest='command', required=True)

    p_split = sub.add_parser('split', help='Split a monolithic GPE file into section subfiles')
    p_split.add_argument('--input', required=True, type=Path, help='Path to monolithic input file')
    p_split.add_argument('--outdir', required=True, type=Path, help='Directory to write section files into')

    p_build = sub.add_parser('build', help='Build a dated superset from section subfiles')
    p_build.add_argument('--subdir', required=True, type=Path, help='Directory containing section subfiles')
    p_build.add_argument('--outdir', required=True, type=Path, help='Directory to write the built superset into')
    p_build.add_argument('--date', required=False, type=str, help='Date for output filename (YYYY-MM-DD or YYYY_MM_DD). Defaults to today')
    p_build.add_argument('--include-headers', action='store_true', help='Include section headers in the superset')
    p_build.add_argument('--dedupe', action='store_true', help='De-duplicate lines across all sections')

    return parser


def main(argv: List[str]) -> int:
    parser = build_argparser()
    args = parser.parse_args(argv)

    if args.command == 'split':
        cmd_split(args.input, args.outdir)
        return 0
    if args.command == 'build':
        cmd_build(args.subdir, args.outdir, getattr(args, 'date', None), getattr(args, 'include_headers', False), getattr(args, 'dedupe', False))
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


