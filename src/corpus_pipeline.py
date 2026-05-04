from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from config import (
    CLAIMS_DIR,
    CORPUS_CHUNKS_DIR,
    CORPUS_RAW_DIR,
    CORPUS_ROOT,
    METADATA_DIR,
    PROJECT_ROOT,
    RELEVANCE_KEYWORDS,
    TEXT_EXTENSIONS,
)


@dataclass
class CorpusCopy:
    source_path: str
    copied_path: str | None
    sha256: str | None
    reason: str
    bytes: int


CLAIM_PATTERNS = {
    "marche": [
        r"\bmarket\b",
        r"\bmarche\b",
        r"\bprix\b",
        r"\bbtc\b",
        r"\bbitcoin\b",
    ],
    "macro": [
        r"\bmacro\b",
        r"\bdxy\b",
        r"\btaux\b",
        r"\brates\b",
        r"\bnasdaq\b",
        r"\bliquidity\b",
    ],
    "volatilite": [
        r"\bvolatil",
        r"\bvariance\b",
        r"\bgarch\b",
        r"\bjump\b",
        r"\bregime\b",
    ],
    "risques": [
        r"\brisk\b",
        r"\brisque\b",
        r"\bdrawdown\b",
        r"\bliquidation\b",
        r"\bstress\b",
    ],
    "hypotheses": [
        r"\bhypoth",
        r"\bassumption\b",
        r"\bscenario\b",
        r"\bcondition\b",
    ],
}


def _safe_name(path: Path) -> str:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:10]
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.name)
    return f"{digest}_{name}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_text_sample(path: Path, max_chars: int = 120_000) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return handle.read(max_chars)


def _is_relevant(text: str, path: Path) -> bool:
    haystack = f"{path.name}\n{text[:10000]}".lower()
    return any(keyword in haystack for keyword in RELEVANCE_KEYWORDS)


def discover_relevant_documents(logger, max_docs: int = 100, max_bytes: int = 3_000_000) -> list[CorpusCopy]:
    copies: list[CorpusCopy] = []
    skipped = 0
    for path in CORPUS_ROOT.rglob("*"):
        if len(copies) >= max_docs:
            break
        if not path.is_file():
            continue
        try:
            resolved = path.resolve()
            if PROJECT_ROOT in resolved.parents or ".git" in resolved.parts or ".codex_tmp" in resolved.parts:
                continue
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            size = path.stat().st_size
            if size > max_bytes:
                skipped += 1
                logger.warning("corpus_skip_large_file | path=%s | bytes=%s", path, size)
                continue
            text = _read_text_sample(path)
            if not _is_relevant(text, path):
                continue
            dest = CORPUS_RAW_DIR / _safe_name(path)
            if not dest.exists():
                shutil.copy2(path, dest)
                reason = "keyword_relevance"
            else:
                reason = "existing_copy_reused"
            copies.append(
                CorpusCopy(
                    source_path=str(path),
                    copied_path=str(dest),
                    sha256=_sha256(dest),
                    reason=reason,
                    bytes=size,
                )
            )
        except Exception as exc:
            logger.warning("corpus_scan_error | path=%s | error=%s", path, exc)

    manifest_path = METADATA_DIR / "corpus_copy_manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as handle:
        for item in copies:
            handle.write(json.dumps(item.__dict__, ensure_ascii=True) + "\n")
        if skipped:
            handle.write(json.dumps({"skipped_large_files": skipped}, ensure_ascii=True) + "\n")
    logger.info("corpus_documents_copied | count=%s | manifest=%s", len(copies), manifest_path)
    return copies


def chunk_text(text: str, min_tokens: int = 500, max_tokens: int = 1000) -> list[str]:
    tokens = re.findall(r"\S+", text)
    if not tokens:
        return []
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        if end - start < min_tokens and chunks:
            chunks[-1] = chunks[-1] + " " + " ".join(tokens[start:end])
            break
        chunks.append(" ".join(tokens[start:end]))
        start = end
    return chunks


def build_chunks(copies: list[CorpusCopy], logger) -> list[dict]:
    chunk_records = []
    for item in copies:
        if not item.copied_path:
            continue
        path = Path(item.copied_path)
        try:
            text = _read_text_sample(path, max_chars=2_000_000)
            for index, chunk in enumerate(chunk_text(text), start=1):
                record = {
                    "chunk_id": f"{path.stem}_chunk_{index:04d}",
                    "source_path": item.source_path,
                    "copied_path": item.copied_path,
                    "chunk_index": index,
                    "token_estimate": len(re.findall(r"\S+", chunk)),
                    "text": chunk,
                }
                chunk_records.append(record)
                chunk_path = CORPUS_CHUNKS_DIR / f"{record['chunk_id']}.json"
                chunk_path.write_text(json.dumps(record, ensure_ascii=True, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("corpus_chunk_error | path=%s | error=%s", path, exc)
    logger.info("corpus_chunks_created | count=%s", len(chunk_records))
    return chunk_records


def extract_claims(chunks: list[dict], logger) -> list[dict]:
    claims = []
    claim_id = 1
    sentence_split = re.compile(r"(?<=[.!?])\s+|\n+")
    for chunk in chunks:
        sentences = [s.strip() for s in sentence_split.split(chunk.get("text", "")) if len(s.strip()) > 40]
        for sentence in sentences:
            lower = sentence.lower()
            categories = [
                category
                for category, patterns in CLAIM_PATTERNS.items()
                if any(re.search(pattern, lower) for pattern in patterns)
            ]
            if not categories:
                continue
            claims.append(
                {
                    "claim_id": f"claim_{claim_id:06d}",
                    "claim": sentence[:1200],
                    "categories": categories,
                    "source_document": chunk["source_path"],
                    "source_chunk": chunk["chunk_id"],
                    "reliability": "unknown",
                }
            )
            claim_id += 1
    out = CLAIMS_DIR / "claims.jsonl"
    with out.open("w", encoding="utf-8") as handle:
        for claim in claims:
            handle.write(json.dumps(claim, ensure_ascii=True) + "\n")
    logger.info("corpus_claims_extracted | count=%s | output=%s", len(claims), out)
    return claims


def run_corpus_pipeline(logger, max_docs: int = 100) -> dict:
    copies = discover_relevant_documents(logger, max_docs=max_docs)
    chunks = build_chunks(copies, logger)
    claims = extract_claims(chunks, logger)
    metadata = {
        "copied_documents": len(copies),
        "chunks": len(chunks),
        "claims": len(claims),
        "reliability_default": "unknown",
        "originals_modified": False,
    }
    (METADATA_DIR / "pipeline_summary.json").write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return metadata
