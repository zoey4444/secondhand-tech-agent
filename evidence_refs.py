"""Source excerpts belong to the application, never to model-generated text.

Resolving a reference proves text provenance, not the truth of a seller claim
or the semantic correctness of the model's interpretation.
"""
from __future__ import annotations

import re


def build_catalog(sources: dict[str, str]) -> dict[str, dict[str, str]]:
    catalog = {}
    for source, text in sources.items():
        index = 0
        # Keep clauses short enough to cite both sides of a same-source conflict.
        for sentence in re.finditer(r"[^。！？!?；;\n，,]+[。！？!?；;\n，,]*", text):
            segment = sentence.group()
            for start in range(0, len(segment), 280):
                quote = segment[start:start + 280].strip()
                if quote:
                    index += 1
                    catalog[f"{source}:{index}"] = {"source": source, "quote": quote}
    return catalog


def resolve_reference(sources: dict[str, str], item, catalog=None):
    if not isinstance(item, dict):
        return None
    if "ref" in item:
        citation = (catalog if catalog is not None else build_catalog(sources)).get(str(item["ref"]))
        if not citation:
            return None
        # Never ignore a conflicting quote/source supplied alongside a valid id.
        if "source" in item and item["source"] != citation["source"]:
            return None
        if "quote" in item and item["quote"] != citation["quote"]:
            return None
        return dict(citation)
    # Legacy structured responses are still accepted, with strict text checking.
    source = str(item.get("source", ""))
    quote = str(item.get("quote") or "").strip()
    if len(quote) < 3 or len(quote) > 300 or source not in sources:
        return None
    if quote in sources[source]:
        return {"source": source, "quote": quote}
    # Allow whitespace changes only and return the actual source span.
    indexes = [i for i, char in enumerate(sources[source]) if not char.isspace()]
    compact = "".join(sources[source][i] for i in indexes)
    wanted = re.sub(r"\s+", "", quote)
    start = compact.find(wanted)
    if wanted and start >= 0:
        actual = sources[source][indexes[start]:indexes[start + len(wanted) - 1] + 1]
        return {"source": source, "quote": actual}
    return None
