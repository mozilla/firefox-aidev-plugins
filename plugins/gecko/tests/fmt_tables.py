"""Align the columns of every Markdown table outside code blocks.

Usage: python3 plugins/gecko/tests/fmt_tables.py [--check] FILE...

Without --check, it rewrites the files. With --check, it lists the files that would
change and exits with 1.
"""
import re
import sys


def split_row(line):
    """Cells of a table row; a | inside backticks or after a backslash is not a separator."""
    cells, cur, code, i = [], "", False, 0
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            cur += body[i:i + 2]
            i += 2
            continue
        if ch == "`":
            code = not code
        if ch == "|" and not code:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
        i += 1
    cells.append(cur.strip())
    return cells


def is_sep(cells):
    return all(re.fullmatch(r":?-+:?", c) for c in cells)


def format_table(lines):
    rows = [split_row(l) for l in lines]
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    width = [max(3, *(len(r[i]) for r in rows if not is_sep(r))) for i in range(n)]
    out = []
    for r in rows:
        if is_sep(r):
            out.append("|" + "|".join("-" * (width[i] + 2) for i in range(n)) + "|")
        else:
            out.append("| " + " | ".join(r[i].ljust(width[i]) for i in range(n)) + " |")
    return out


def format_text(text):
    lines = text.split("\n")
    out, i, fence = [], 0, False
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            fence = not fence
        if (not fence and line.lstrip().startswith("|") and i + 1 < len(lines)
                and lines[i + 1].lstrip().startswith("|") and is_sep(split_row(lines[i + 1]))):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            indent = line[:len(line) - len(line.lstrip())]
            out.extend(indent + l for l in format_table(lines[i:j]))
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def main(argv):
    check = "--check" in argv
    changed = []
    for path in (a for a in argv if a != "--check"):
        text = open(path, encoding="utf-8").read()
        new = format_text(text)
        if new != text:
            changed.append(path)
            if not check:
                open(path, "w", encoding="utf-8").write(new)
    for p in changed:
        print(p)
    return 1 if check and changed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
