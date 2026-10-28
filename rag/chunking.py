"""Clause-aware chunking of the GDV AKB 2015 text produced by scripts/fetch_data.py.

The AKB numbers every clause (``A.2.2.1``, ``E.1.1.3`` …). We split on that numbering instead
of fixed windows so every chunk maps to a citable clause id, and we keep the chain of parent
headings so a chunk about "Entwendung" still knows it sits under "A.2 Kaskoversicherung".
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AKB_TXT = REPO_ROOT / "data" / "processed" / "akb_2015.txt"
SOURCE_ID = "gdv_akb_2015"

PAGE_SEPARATOR = re.compile(r"^_{20,}\s*(\d+)\s*$")
SECTION_HEADING = re.compile(r"^([A-Z])\s+(\S.*)$")  # "A Welche Leistungen umfasst …"
CLAUSE_HEADING = re.compile(r"^([A-Z]\.\d+(?:\.\d+)*)\s+(.*)$")  # "A.2.2.1 Wir leisten …"
ANNEX_HEADING = re.compile(r"^(Anhang\s+\d+)[:\s]*(.*)$")
TOC_ENTRY = re.compile(r"\s\d{1,2}\s*$")  # TOC lines end with a page number
BULLETS = ("\uf0b7", "\uf097", "\uf0a7")
MAX_WORDS = 550  # ≈ 800 tokens for German text with the e5 tokenizer


@dataclass
class Chunk:
    clause_id: str
    title: str
    text: str
    parent_id: str | None
    page: int
    heading_chain: list[str] = field(default_factory=list)
    part: int = 1
    source: str = SOURCE_ID

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(
            f"{self.source}|{self.clause_id}|{self.part}|{self.text}".encode()
        ).hexdigest()

    @property
    def embedding_text(self) -> str:
        """What gets embedded: heading chain + clause id + body."""
        chain = " > ".join(self.heading_chain) if self.heading_chain else ""
        head = f"{self.clause_id} {self.title}".strip()
        return "\n".join(part for part in (chain, head, self.text) if part)

    @property
    def citation(self) -> str:
        return f"AKB 2015 {self.clause_id}"


def parent_of(clause_id: str) -> str | None:
    if clause_id.startswith("Anhang"):
        return None
    if "." not in clause_id:
        return None
    head, _, _ = clause_id.rpartition(".")
    return head


def normalise_lines(raw: str) -> list[tuple[int, str]]:
    """Return (page, line) pairs with hyphenated line breaks joined and bullets normalised."""
    out: list[tuple[int, str]] = []
    page = 0
    pending: str | None = None
    for raw_page in raw.split("\f"):
        page += 1
        for line in raw_page.splitlines():
            for bullet in BULLETS:
                line = line.replace(bullet, "•")
            line = line.rstrip()
            sep = PAGE_SEPARATOR.match(line)
            if sep:
                page = int(sep.group(1))
                continue
            if not line.strip():
                continue
            if pending is not None:
                if line[:1].islower() or line[:1] in "äöüß":
                    line = pending + line.lstrip()
                else:
                    line = pending + "-" + line.lstrip()
                pending = None
            if re.search(r"[A-Za-zÄÖÜäöüß]-$", line):
                pending = line[:-1]
                continue
            out.append((page, line))
    if pending is not None:
        out.append((page, pending))
    return out


def _is_body_start(line: str) -> bool:
    return bool(
        SECTION_HEADING.match(line) and line.startswith("A ") and not TOC_ENTRY.search(line)
    )


def _looks_like_subtitle(line: str) -> bool:
    """Un-numbered caption such as 'Vorsatz' that labels the following clause."""
    words = line.split()
    return (
        1 <= len(words) <= 14
        and not line.endswith((".", ":", ";", ","))
        and not line.startswith("•")
    )


def split_clauses(lines: list[tuple[int, str]]) -> list[Chunk]:
    """Walk the normalised lines and emit one chunk per numbered clause that carries text."""
    started = False
    titles: dict[str, str] = {}
    chunks: list[Chunk] = []
    current: Chunk | None = None
    buffer: list[str] = []
    subtitle: str | None = None
    in_annex = False

    def flush() -> None:
        nonlocal current, buffer
        if current is not None:
            current.text = " ".join(buffer).strip()
            if current.text:
                chunks.append(current)
        current, buffer = None, []

    def is_heading(line: str) -> bool:
        return bool(
            CLAUSE_HEADING.match(line) or (SECTION_HEADING.match(line) and len(line.split()) >= 3)
        )

    for i, (page, line) in enumerate(lines):
        if not started:
            if _is_body_start(line):
                started = True
            else:
                continue
        next_line = lines[i + 1][1] if i + 1 < len(lines) else ""

        annex = ANNEX_HEADING.match(line)
        if annex and (in_annex or line.startswith("Anhang 1")) and not TOC_ENTRY.search(line):
            in_annex = True
            flush()
            cid = re.sub(r"\s+", " ", annex.group(1))
            titles[cid] = annex.group(2).strip()
            current = Chunk(cid, titles[cid], "", None, page, [])
            continue
        if in_annex:
            if current is not None:
                buffer.append(line)
            continue

        section = SECTION_HEADING.match(line)
        if section and len(line.split()) >= 3:
            flush()
            titles[section.group(1)] = section.group(2).strip()
            subtitle = None
            continue

        clause = CLAUSE_HEADING.match(line)
        if clause:
            flush()
            cid, rest = clause.group(1), clause.group(2).strip()
            heading_like = rest.endswith("?") or (len(rest.split()) <= 8 and is_heading(next_line))
            if heading_like:
                titles[cid] = rest
            current = Chunk(
                cid,
                subtitle or (rest if heading_like else ""),
                "",
                parent_of(cid),
                page,
                _chain(cid, titles),
            )
            buffer = [rest]
            subtitle = None
            continue

        if _looks_like_subtitle(line) and CLAUSE_HEADING.match(next_line):
            subtitle = line  # un-numbered caption such as "Vorsatz" that labels the next clause
            continue
        if current is not None:
            buffer.append(line)

    flush()
    return _merge_and_split(chunks)


def _chain(cid: str, titles: dict[str, str]) -> list[str]:
    chain = []
    section = cid[0]
    if section in titles:
        chain.append(f"{section} {titles[section]}")
    parts = cid.split(".")
    for i in range(2, len(parts)):
        pid = ".".join(parts[:i])
        if pid in titles:
            chain.append(f"{pid} {titles[pid]}")
    return chain


def _merge_and_split(chunks: list[Chunk]) -> list[Chunk]:
    """Drop heading-only chunks (their titles live in children's chains); split oversize bodies."""
    out: list[Chunk] = []
    seen: set[str] = set()
    for i, chunk in enumerate(chunks):
        nxt = chunks[i + 1].clause_id if i + 1 < len(chunks) else ""
        if nxt.startswith(chunk.clause_id + ".") and len(chunk.text.split()) <= 12:
            continue  # heading-only clause; its title survives in the children's heading_chain
        if chunk.content_hash in seen:
            continue  # the PDF repeats a few clauses verbatim (editorial variants)
        seen.add(chunk.content_hash)
        words = chunk.text.split()
        if len(words) <= MAX_WORDS:
            out.append(chunk)
            continue
        n_parts = -(-len(words) // MAX_WORDS)
        size = -(-len(words) // n_parts)
        for i in range(n_parts):
            piece = " ".join(words[i * size : (i + 1) * size])
            out.append(
                Chunk(
                    chunk.clause_id,
                    chunk.title,
                    piece,
                    chunk.parent_id,
                    chunk.page,
                    chunk.heading_chain,
                    part=i + 1,
                )
            )
    return out


def chunk_akb(path: Path = AKB_TXT) -> list[Chunk]:
    return split_clauses(normalise_lines(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    import sys

    chunks = chunk_akb(Path(sys.argv[1]) if len(sys.argv) > 1 else AKB_TXT)
    print(f"{len(chunks)} chunks")
    for c in chunks:
        words = len(c.text.split())
        print(f"{c.clause_id:<12} p{c.page:<3} {words:>4}w  {c.title[:40]!r:<44} {c.text[:60]!r}")
