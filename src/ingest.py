"""Download public sources and extract document-level text. Network required."""
import argparse
import datetime as dt
import json
import re
import time

import fitz
import httpx
from bs4 import BeautifulSoup

from src.common import PROCESSED, RAW, ROOT, digest, write_jsonl


def extract_pdf(payload):
    pages = []
    with fitz.open(stream=payload, filetype="pdf") as doc:
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append({"page": index, "text": text})
    return pages


def extract_html(payload):
    soup = BeautifulSoup(payload, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    # Document-specific extraction may be needed for legal text.
    content = soup.find("main") or soup.find("article") or soup.body or soup
    return [{"page": None, "text": content.get_text("\n", strip=True)}]


def collect(sources, timeout=30, strict=False, publish=True, retries=2):
    docs = []
    errors = []
    RAW.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "AcademicRAGResearch/0.1"}) as client:
        for source in sources:
            if not source.get("enabled", True):
                print(f"SKIP {source['id']} (disabled)")
                continue
            try:
                for attempt in range(retries + 1):
                    try:
                        response = client.get(source["url"])
                        response.raise_for_status()
                        break
                    except httpx.HTTPError:
                        if attempt == retries:
                            raise
                        time.sleep(min(2 ** attempt, 4))
                kind = source["kind"]
                mime = response.headers.get("content-type", "").lower()
                if kind == "pdf" and not response.content.startswith(b"%PDF"):
                    raise ValueError(f"Expected PDF, received {mime}")
                if kind == "html" and "pdf" in mime:
                    raise ValueError("Expected HTML, received PDF")
                suffix = ".pdf" if kind == "pdf" else ".html"
                (RAW / f"{source['id']}{suffix}").write_bytes(response.content)
                pages = extract_pdf(response.content) if kind == "pdf" else extract_html(response.content)
                if not pages or sum(len(p["text"]) for p in pages) < 100:
                    raise ValueError("Text too short; check extraction or scanned PDF")
                for page in pages:
                    cleaned = re.sub(r"[ \t]+", " ", page["text"])
                    docs.append({
                        "document_id": source["id"], "title": source["title"],
                        "organization": source["organization"], "source_url": source["url"],
                        "topic": source["topic"], "page": page["page"],
                        "collected_at": dt.date.today().isoformat(),
                        "content": cleaned, "content_sha256": digest(cleaned)
                    })
                print(f"OK {source['id']}: {len(pages)} section(s)")
            except (httpx.HTTPError, ValueError, RuntimeError) as exc:
                errors.append(source["id"])
                print(f"ERROR {source['id']}: {exc}")
    if strict and errors:
        raise RuntimeError(f"Source collection failed: {errors}; refusing partial publication")
    if publish:
        write_jsonl(PROCESSED / "documents.jsonl", docs)
    print(f"Wrote {len(docs)} records to data/processed/documents.jsonl")
    return docs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default=str(ROOT / "config" / "sources.json"))
    args = parser.parse_args()
    with open(args.sources, encoding="utf-8") as handle:
        sources = json.load(handle)
    collect(sources)


if __name__ == "__main__":
    main()
