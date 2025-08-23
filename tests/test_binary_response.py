from httpx import Headers

from make_api_request.binary_response import BinaryResponse


class TestBinaryResponse:
    def test_init_with_content_and_headers(self):
        content = b"binary data content"
        headers = Headers(
            {"content-type": "application/octet-stream", "content-length": "19"}
        )

        response = BinaryResponse(content=content, headers=headers)

        assert response.content == content
        assert response.headers == headers

    def test_init_with_empty_content(self):
        content = b""
        headers = Headers({"content-type": "application/octet-stream"})

        response = BinaryResponse(content=content, headers=headers)

        assert response.content == content
        assert response.headers == headers

    def test_init_with_empty_headers(self):
        content = b"some binary data"
        headers = Headers({})

        response = BinaryResponse(content=content, headers=headers)

        assert response.content == content
        assert response.headers == headers

    def test_content_property(self):
        content = b"test binary content"
        headers = Headers({"content-type": "image/png"})

        response = BinaryResponse(content=content, headers=headers)

        assert response.content is content

    def test_headers_property(self):
        content = b"test content"
        headers = Headers(
            {
                "content-type": "application/pdf",
                "content-disposition": "attachment; filename=test.pdf",
            }
        )

        response = BinaryResponse(content=content, headers=headers)

        assert response.headers is headers
        assert response.headers["content-type"] == "application/pdf"
        assert (
            response.headers["content-disposition"] == "attachment; filename=test.pdf"
        )

    def test_with_large_binary_content(self):
        # Test with larger binary content
        content = b"x" * 10000  # 10KB of data
        headers = Headers({"content-type": "application/octet-stream"})

        response = BinaryResponse(content=content, headers=headers)

        assert len(response.content) == 10000
        assert response.content == content
        assert response.headers == headers

    def test_with_unicode_headers(self):
        content = b"binary content"
        headers = Headers(
            {
                "content-type": "text/plain; charset=utf-8",
                "custom-header": "unicode-value-test",
            }
        )

        response = BinaryResponse(content=content, headers=headers)

        assert response.content == content
        assert response.headers == headers
        assert response.headers["custom-header"] == "unicode-value-test"

    def test_immutability_of_content(self):
        original_content = b"original content"
        headers = Headers({"content-type": "application/octet-stream"})

        response = BinaryResponse(content=original_content, headers=headers)

        # Verify that the content is the same object reference
        assert response.content is original_content

    def test_case_insensitive_headers(self):
        content = b"test content"
        headers = Headers({"Content-Type": "application/json"})

        response = BinaryResponse(content=content, headers=headers)

        # httpx.Headers should handle case-insensitive access
        assert response.headers["content-type"] == "application/json"
        assert response.headers["Content-Type"] == "application/json"
