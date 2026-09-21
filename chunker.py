"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document

# Below this many characters a paragraph in campus_life is an aside rather than
# a fact that stands up on its own — "The good: the location." and the like.
# Only 10 of the corpus's 183 body paragraphs fall under it, so grouping those
# few onto their neighbour costs almost nothing and removes every stub chunk.
MIN_CHUNK = 60

# Sentence boundary, used only when a single paragraph is longer than the
# chunk ceiling. Nothing in campus_life reaches that, but a paragraph that did
# should break between sentences rather than mid-word.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _title_and_body(doc: Document) -> tuple[str, list[str]]:
    """Separate a document's title line from its paragraphs.

    Every document in campus_life opens with a short title on its own line —
    "Innisfree Hall — what it's actually like" — followed by a blank line. All
    88 of them do, which is why this is a rule and not a guess. Anything that
    doesn't match is treated as body text rather than silently mangled.
    """
    blocks = [b.strip() for b in doc.text.split("\n\n") if b.strip()]
    if blocks and "\n" not in blocks[0] and len(blocks[0]) < 80:
        return blocks[0], blocks[1:]
    return "", blocks


def _split_long(text: str, limit: int) -> list[str]:
    """Break an over-long paragraph between sentences, never mid-word."""
    if len(text) <= limit:
        return [text]

    pieces: list[str] = []
    buffer = ""
    for sentence in SENTENCE_END.split(text):
        if buffer and len(buffer) + 1 + len(sentence) > limit:
            pieces.append(buffer)
            buffer = sentence
        else:
            buffer = f"{buffer} {sentence}".strip()
    if buffer:
        pieces.append(buffer)
    return pieces


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    One paragraph per chunk, with the document's title carried along.

    Two things about campus_life drove this. First, the starter's 800-character
    window never fired: the longest document is 549 characters, so all 88 came
    out as one chunk each, and a post covering a building's heating, laundry
    price and noise was a single chunk answering three unrelated questions.
    Paragraphs are where those topics already separate — the corpus averages
    three blocks per document and the authors put one thought in each.

    Second, the title has to travel with every piece. Seven buildings each have
    a laundry paragraph, and stripped of its heading "Machines take $1.50 wash,
    $1.25 dry, coin or card" could belong to any of them. Prepending the title
    costs at most 47 characters and is what makes a chunk identifiable.

    Paragraphs shorter than MIN_CHUNK are grouped onto their neighbour so no
    chunk is a stub, and a paragraph longer than the ceiling breaks between
    sentences. There is no character overlap: every boundary here is already a
    paragraph boundary, so no sentence is cut and no chunk loses the context
    that overlap exists to restore.
    """
    chunks: list[Chunk] = []

    for doc in documents:
        title, paragraphs = _title_and_body(doc)
        prefix = f"{title}\n\n" if title else ""

        # Group paragraphs so that nothing below MIN_CHUNK stands alone.
        groups: list[str] = []
        pending: list[str] = []
        for paragraph in paragraphs:
            pending.append(paragraph)
            joined = "\n\n".join(pending)
            if len(joined) >= MIN_CHUNK:
                groups.append(joined)
                pending = []
        if pending:
            tail = "\n\n".join(pending)
            if groups:
                groups[-1] = f"{groups[-1]}\n\n{tail}"
            else:
                groups.append(tail)

        # A document that is nothing but a title still has to produce a chunk.
        if not groups:
            groups = [title] if title else []
            prefix = ""

        index = 0
        for group in groups:
            for piece in _split_long(group, max(config.CHUNK_SIZE - len(prefix), 1)):
                text = f"{prefix}{piece}".strip()
                if not text:
                    continue
                chunks.append(
                    Chunk(
                        text=text,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
