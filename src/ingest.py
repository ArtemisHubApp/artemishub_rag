"""Collect public documents with bounded downloads and auditable source outcomes."""
import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import logging
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pymupdf
from bs4 import BeautifulSoup

from src.common import PROCESSED, RAW, ROOT, digest, write_jsonl

LOG = logging.getLogger(__name__)
MAX_BYTES = 30 * 1024 * 1024


def validate_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Public HTTP(S) URL required")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Local URL rejected")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise ValueError("Private/reserved IP rejected")


def extract_pdf(payload):
    pages = []
    with pymupdf.open(stream=payload, filetype="pdf") as doc:
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            # Keep blank pages in audit data rather than silently losing coverage.
            pages.append({"page": index, "text": text})
    return pages


def extract_html(payload, article=None):
    soup = BeautifulSoup(payload, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "s", "strike", "del"]):
        tag.decompose()
    content = soup.find("main") or soup.find("article") or soup.body or soup
    text = content.get_text("\n", strip=True)
    if article:
        # Restrict to the actual article, never links mentioning it in the preamble.
        pattern = rf"(?mi)^\s*Art\.?\s*{re.escape(str(article))}\s*[.º°-]?\s"
        start = re.search(pattern, text)
        if not start:
            raise ValueError(f"Article {article} not found")
        following = text[start.end():]
        end = re.search(r"(?mi)^\s*Art\.?\s*\d+[\s.º°-]", following)
        text = text[start.start():start.end() + end.start() if end else len(text)].strip()
    return [{"page": None, "text": text}]


def fetch(client, url, retries):
    validate_url(url)
    for attempt in range(retries + 1):
        try:
            # Validate every redirect before requesting it, with a finite hop limit.
            current = url
            redirects = []
            for _ in range(6):
                validate_url(current)
                with client.stream("GET", current, follow_redirects=False) as response:
                    if response.is_redirect:
                        current = str(response.url.join(response.headers["location"]))
                        redirects.append(current)
                        continue
                    response.raise_for_status()
                    size, parts = 0, []
                    for part in response.iter_bytes():
                        size += len(part)
                        if size > MAX_BYTES:
                            raise ValueError("Download exceeds 30 MiB")
                        parts.append(part)
                    return b"".join(parts), response, redirects
            raise ValueError("Too many redirects")
        except httpx.HTTPError as exc:
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            if attempt == retries or status in (401, 403, 404, 429):
                raise
            time.sleep(min(2 ** attempt, 4))
    raise RuntimeError("Download failed")


def collect(sources, timeout=30, strict=False, publish=True, retries=2, outcomes=None):
    docs, errors = [], []
    outcomes = outcomes if outcomes is not None else []
    RAW.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=timeout, headers={"User-Agent": "AcademicRAGResearch/0.2"}) as client:
        for source in sources:
            outcome = {"source_id": source["id"], "url": source["url"], "status": "disabled"}
            outcomes.append(outcome)
            if not source.get("enabled", True):
                continue
            try:
                if not re.fullmatch(r"[A-Za-z0-9_-]+", source["id"]):
                    raise ValueError("Unsafe source id")
                kind = source["kind"]
                if kind not in ("html", "pdf"):
                    raise ValueError("Unsupported source kind")
                payload, response, redirects = fetch(client, source["url"], retries)
                outcome.update(http_status=response.status_code, final_url=str(response.url), redirects=redirects,
                               bytes=len(payload))
                mime = response.headers.get("content-type", "").lower()
                if kind == "pdf" and not payload.startswith(b"%PDF"):
                    raise ValueError(f"Expected PDF, received {mime}")
                if kind == "html" and ("pdf" in mime or payload.startswith(b"%PDF")):
                    raise ValueError("Expected HTML, received PDF")
                (RAW / f"{source['id']}.{kind}").write_bytes(payload)
                pages = extract_pdf(payload) if kind == "pdf" else extract_html(payload, source.get("article"))
                if not pages or sum(len(p["text"].strip()) for p in pages) < 100:
                    raise ValueError("Text too short; check extraction or scanned PDF")
                normalized = " ".join(unicodedata.normalize("NFKC", " ".join(p["text"] for p in pages)).casefold().split())
                for marker in source.get("expected_text", []):
                    if " ".join(unicodedata.normalize("NFKC", marker).casefold().split()) not in normalized:
                        raise ValueError(f"Expected document marker missing: {marker}")
                blank = [p["page"] for p in pages if not p["text"].strip()]
                if blank:
                    raise ValueError(f"Empty pages require review/OCR: {blank}")
                source_docs = []
                for page in pages:
                    cleaned = re.sub(r"[ \t]+", " ", page["text"]).strip()
                    metadata = {"page": page["page"], "article": source.get("article"),
                                "final_url": str(response.url), "payload_sha256": hashlib.sha256(payload).hexdigest()}
                    source_docs.append({
                        "document_id": source["id"], "title": source["title"],
                        "source": source["organization"], "organization": source["organization"],
                        "source_url": source["url"], "document_type": kind,
                        "topic": source["topic"], "page": page["page"],
                        "collected_at": dt.datetime.now(dt.UTC).isoformat(),
                        "content": cleaned, "content_hash": digest(cleaned),
                        "content_sha256": digest(cleaned), "metadata": metadata,
                    })
                docs.extend(source_docs)
                outcome.update(status="success", documents=len(source_docs), characters=sum(len(d["content"]) for d in source_docs))
            except (httpx.HTTPError, ValueError, RuntimeError, OSError) as exc:
                errors.append(source["id"])
                outcome.update(status="failed", error_type=type(exc).__name__)
                if isinstance(exc, ValueError):
                    outcome["reason"] = str(exc)
                if isinstance(exc, httpx.HTTPStatusError):
                    outcome["http_status"] = exc.response.status_code
                LOG.warning("source_failed %s", json.dumps(outcome, ensure_ascii=False))
            LOG.info("source_result %s", json.dumps(outcome, ensure_ascii=False))
    if strict and errors:
        raise RuntimeError(f"Source collection failed: {errors}; refusing partial publication")
    if publish:
        if errors or not docs:
            raise RuntimeError("Refusing partial publication; use pipeline --allow-partial for diagnostics")
        write_jsonl(PROCESSED / "documents.jsonl", docs)
    return docs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default=str(ROOT / "config" / "sources.json"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    collect(json.loads(Path(args.sources).read_text(encoding="utf-8")), strict=True)


if __name__ == "__main__":
    main()
