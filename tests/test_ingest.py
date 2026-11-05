import httpx
import pymupdf
import pytest

from src import ingest


def test_article_extraction_excludes_neighbors_and_revoked_text():
    html = b'''<body><nav>MENU</nav><p>Art. 460. Before</p>
    <p>Art. 461. Equal pay.</p><s>Revoked text</s><p>Paragraph retained.</p>
    <p>Art. 462. After</p><footer>FOOTER</footer></body>'''
    result = ingest.extract_html(html, article="461")[0]["text"]
    assert "461" in result and "Paragraph retained" in result
    assert all(word not in result for word in ("460", "462", "MENU", "Revoked", "FOOTER"))
    with pytest.raises(ValueError, match="not found"):
        ingest.extract_html(html, article="999")


def test_pdf_preserves_page_numbers():
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((50, 50), "Local synthetic fixture page 1")
        pdf.new_page().insert_text((50, 50), "Local synthetic fixture page 2")
        pages = ingest.extract_pdf(pdf.tobytes())
    assert [p["page"] for p in pages] == [1, 2]
    assert "page 2" in pages[1]["text"]


@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://localhost/a", "http://127.0.0.1", "http://169.254.169.254", "https://user:secret@example.org"])
def test_rejects_unsafe_urls(url):
    with pytest.raises(ValueError):
        ingest.validate_url(url)


def test_redirect_validated_before_request_and_size_limit(monkeypatch):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})

    with (httpx.Client(transport=httpx.MockTransport(handler)) as client,
          pytest.raises(ValueError, match="Private")):
        ingest.fetch(client, "https://example.org", 0)
    assert len(calls) == 1
    monkeypatch.setattr(ingest, "MAX_BYTES", 4)
    with (httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"12345"))) as client,
          pytest.raises(ValueError, match="30 MiB")):
        ingest.fetch(client, "https://example.org", 0)


def test_forbidden_is_not_retried():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(403)

    with (httpx.Client(transport=httpx.MockTransport(handler)) as client,
          pytest.raises(httpx.HTTPStatusError)):
        ingest.fetch(client, "https://example.org", 2)
    assert len(calls) == 1
