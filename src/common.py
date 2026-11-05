import hashlib
import json
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path, rows):
    """Atomically replace a JSONL file after successfully writing every row."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        try:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
    temp_path.replace(path)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path, value):
    """Publish JSON by atomic rename on the same filesystem."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def embedding_model():
    return os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def embedding_revision(model_name=None):
    default_model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    return os.getenv("EMBEDDING_REVISION") or (
        "e8f8c211226b894fcb81acc59f3b34ba3efd5f42" if (model_name or embedding_model()) == default_model else None
    )
