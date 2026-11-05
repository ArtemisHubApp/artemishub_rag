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


def test_legal_selector_preserves_heading_and_excludes_navigation():
    html = b'<body><h1>GENERIC NAVIGATION</h1><h1>LEI 14.611</h1><div>MENU</div><div class="textoNorma"><p>Art. 1. Evidence.</p></div><div>FOOTER</div></body>'
    text = ingest.extract_html(html, selector='.textoNorma')[0]['text']
    assert 'LEI 14.611' in text and 'Evidence' in text
    assert 'MENU' not in text and 'FOOTER' not in text
    assert 'GENERIC NAVIGATION' not in text
    with pytest.raises(ValueError, match='selector not found'):
        ingest.extract_html(html, selector='.missing')


def test_official_alternative_retains_actual_url_and_failed_attempt(tmp_path, monkeypatch):
    primary = 'https://primary.example.org/law'
    alternate = 'https://official.example.org/law'
    source = {'id': 'law', 'url': primary, 'organization': 'Issuer', 'title': 'Fixture law',
              'topic': 'test', 'kind': 'html', 'expected_text': ['Mandatory law'],
              'alternatives': [{'url': alternate, 'publisher': 'Official publisher',
                                'version': 'Original publication', 'html_selector': '.law'}]}
    monkeypatch.setattr(ingest, 'RAW', tmp_path)
    real_client = httpx.Client

    def handler(request):
        if str(request.url) == primary:
            raise httpx.ReadError('Simulated reset', request=request)
        return httpx.Response(200, text='<h1>Mandatory law</h1><div class="law">' + 'Fixture evidence. ' * 20 + '</div>')

    monkeypatch.setattr(ingest.httpx, 'Client', lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    outcomes = []
    docs = ingest.collect([source], retries=0, publish=False, outcomes=outcomes)
    assert docs[0]['source_url'] == alternate
    assert docs[0]['source'] == 'Official publisher'
    assert docs[0]['metadata']['primary_url'] == primary
    assert docs[0]['metadata']['alternative_used'] is True
    assert outcomes[0]['status'] == 'success'
    assert [a['status'] for a in outcomes[0]['attempts']] == ['failed', 'success']
    assert len(list((tmp_path / 'versions/law').glob('*.html'))) == 1
