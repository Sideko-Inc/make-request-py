from typing import Any
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from make_api_request.api_error import ApiError
from make_api_request.auth import AuthProvider
from make_api_request.base_client import (
    _DEFAULT_SERVICE_NAME,
    AsyncBaseClient,
    BaseClient,
    SyncBaseClient,
)
from make_api_request.binary_response import BinaryResponse
from make_api_request.request import RequestConfig, RequestOptions
from make_api_request.response import AsyncStreamResponse, StreamResponse
from make_api_request.retry import RetryStrategy


class MockAuthProvider(AuthProvider):
    def __init__(self, auth_id: str):
        self.auth_id = auth_id

    def add_to_request(self, cfg: RequestConfig) -> RequestConfig:
        headers = cfg.get("headers", {})
        headers["Authorization"] = f"Mock-{self.auth_id}"
        cfg["headers"] = headers
        return cfg

    def set_value(self, val):
        pass


class TestBaseClient:
    def test_init_with_string_base_url(self):
        client = BaseClient("https://api.example.com")
        assert client._base_url == {_DEFAULT_SERVICE_NAME: "https://api.example.com"}
        assert client._auths == {}

    def test_init_with_dict_base_url(self):
        urls = {"api": "https://api.example.com", "auth": "https://auth.example.com"}
        client = BaseClient(urls)
        assert client._base_url == urls
        assert client._auths == {}

    def test_init_with_auths(self):
        auth1 = MockAuthProvider("auth1")
        auth2 = MockAuthProvider("auth2")
        auths = {"auth1": auth1, "auth2": auth2}

        client = BaseClient("https://api.example.com", auths=auths)
        assert client._auths == auths

    def test_register_auth(self):
        client = BaseClient("https://api.example.com")
        auth = MockAuthProvider("test")

        client.register_auth("test_auth", auth)
        assert client._auths["test_auth"] == auth

    def test_default_headers(self):
        client = BaseClient("https://api.example.com")
        headers = client.default_headers()

        expected = {"x-sideko-sdk-language": "Python"}
        assert headers == expected

    def test_build_url_with_default_service(self):
        client = BaseClient("https://api.example.com")
        url = client.build_url("/users")
        assert url == "https://api.example.com/users"

    def test_build_url_with_named_service(self):
        urls = {"api": "https://api.example.com", "auth": "https://auth.example.com"}
        client = BaseClient(urls)

        url = client.build_url("/token", service_name="auth")
        assert url == "https://auth.example.com/token"

    def test_build_url_strips_trailing_slash_from_base(self):
        client = BaseClient("https://api.example.com/")
        url = client.build_url("/users")
        assert url == "https://api.example.com/users"

    def test_build_url_strips_leading_slash_from_path(self):
        client = BaseClient("https://api.example.com")
        url = client.build_url("users")
        assert url == "https://api.example.com/users"

    def test_build_url_handles_both_slashes(self):
        client = BaseClient("https://api.example.com/")
        url = client.build_url("/users")
        assert url == "https://api.example.com/users"

    def test_build_url_nonexistent_service(self):
        client = BaseClient("https://api.example.com")
        url = client.build_url("/users", service_name="nonexistent")
        assert url == "/users"  # Empty base URL results in just the path

    def test_cast_to_raw_response_with_httpx_response(self):
        client = BaseClient("https://api.example.com")
        assert client._cast_to_raw_response(Mock(), httpx.Response) is True

    def test_cast_to_raw_response_with_non_response(self):
        client = BaseClient("https://api.example.com")
        assert client._cast_to_raw_response(Mock(), str) is False
        assert client._cast_to_raw_response(Mock(), dict) is False
        assert client._cast_to_raw_response(Mock(), int) is False

    def test_cast_to_raw_response_with_non_class(self):
        client = BaseClient("https://api.example.com")
        assert client._cast_to_raw_response(Mock(), "not a class") is False

    def test_apply_auth_single_provider(self):
        auth = MockAuthProvider("test")
        client = BaseClient("https://api.example.com", auths={"test": auth})

        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        result = client._apply_auth(cfg=cfg, auth_names=["test"])

        assert result["headers"]["Authorization"] == "Mock-test"

    def test_apply_auth_multiple_providers(self):
        auth1 = MockAuthProvider("auth1")
        auth2 = MockAuthProvider("auth2")
        client = BaseClient(
            "https://api.example.com", auths={"auth1": auth1, "auth2": auth2}
        )

        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        result = client._apply_auth(cfg=cfg, auth_names=["auth1", "auth2"])

        # Second auth should override first
        assert result["headers"]["Authorization"] == "Mock-auth2"

    def test_apply_auth_nonexistent_provider(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = client._apply_auth(cfg=cfg, auth_names=["nonexistent"])

        # Should return unchanged config
        assert result == cfg

    def test_apply_headers_basic(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        opts: RequestOptions = {}

        result = client._apply_headers(cfg=cfg, opts=opts)

        expected_headers = {"x-sideko-sdk-language": "Python"}
        assert result["headers"] == expected_headers

    def test_apply_headers_with_content_type(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "POST", "url": "https://example.com"}
        opts: RequestOptions = {}

        result = client._apply_headers(
            cfg=cfg, opts=opts, content_type="application/json"
        )

        assert result["headers"]["content-type"] == "application/json"
        assert result["headers"]["x-sideko-sdk-language"] == "Python"

    def test_apply_headers_with_explicit_headers(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        opts: RequestOptions = {}
        explicit = {"Custom-Header": "custom-value"}

        result = client._apply_headers(cfg=cfg, opts=opts, explicit_headers=explicit)

        assert result["headers"]["Custom-Header"] == "custom-value"
        assert result["headers"]["x-sideko-sdk-language"] == "Python"

    def test_apply_headers_with_additional_headers(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        opts: RequestOptions = {"additional_headers": {"Extra-Header": "extra-value"}}

        result = client._apply_headers(cfg=cfg, opts=opts)

        assert result["headers"]["Extra-Header"] == "extra-value"
        assert result["headers"]["x-sideko-sdk-language"] == "Python"

    def test_apply_headers_with_existing_headers(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {
            "method": "GET",
            "url": "https://example.com",
            "headers": {"Existing": "header"},
        }
        opts: RequestOptions = {}

        result = client._apply_headers(cfg=cfg, opts=opts)

        assert result["headers"]["Existing"] == "header"
        assert result["headers"]["x-sideko-sdk-language"] == "Python"

    def test_apply_query_params_basic(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        opts: RequestOptions = {}
        query_params = {"param1": "value1", "param2": "value2"}

        result = client._apply_query_params(
            cfg=cfg, opts=opts, query_params=query_params
        )

        assert result["params"] == query_params

    def test_apply_query_params_with_additional_params(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        opts: RequestOptions = {"additional_params": {"extra": "param"}}
        query_params = {"original": "param"}

        result = client._apply_query_params(
            cfg=cfg, opts=opts, query_params=query_params
        )

        assert result["params"]["original"] == "param"
        assert result["params"]["extra"] == "param"

    def test_apply_query_params_with_existing_params(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {
            "method": "GET",
            "url": "https://example.com",
            "params": {"existing": "param"},
        }
        opts: RequestOptions = {}
        query_params = {"new": "param"}

        result = client._apply_query_params(
            cfg=cfg, opts=opts, query_params=query_params
        )

        assert result["params"]["existing"] == "param"
        assert result["params"]["new"] == "param"

    def test_apply_timeout(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        opts: RequestOptions = {"timeout": 30}

        result = client._apply_timeout(cfg=cfg, opts=opts)

        assert result["timeout"] == 30

    def test_apply_timeout_no_timeout(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        opts: RequestOptions = {}

        result = client._apply_timeout(cfg=cfg, opts=opts)

        assert "timeout" not in result

    def test_apply_body_with_data(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "POST", "url": "https://example.com"}

        result = client._apply_body(cfg=cfg, data={"key": "value"})

        assert result["data"] == {"key": "value"}

    def test_apply_body_with_files(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "POST", "url": "https://example.com"}

        result = client._apply_body(cfg=cfg, files={"file": ("test.txt", b"content")})

        assert result["files"]["file"] == ("test.txt", b"content")

    def test_apply_body_with_json(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "POST", "url": "https://example.com"}

        result = client._apply_body(cfg=cfg, json={"key": "value"})

        assert result["json"] == {"key": "value"}

    def test_apply_body_with_content(self):
        client = BaseClient("https://api.example.com")
        cfg: RequestConfig = {"method": "POST", "url": "https://example.com"}

        result = client._apply_body(cfg=cfg, content=b"raw content")

        assert result["content"] == b"raw content"

    def test_build_request_full(self):
        auth = MockAuthProvider("test")
        client = BaseClient("https://api.example.com", auths={"test": auth})

        result = client.build_request(
            method="POST",
            path="/users",
            auth_names=["test"],
            query_params={"param": "value"},
            headers={"Custom": "header"},
            json={"data": "value"},
            content_type="application/json",
            request_options={"timeout": 30, "additional_headers": {"Extra": "header"}},
        )

        assert result["method"] == "POST"
        assert result["url"] == "https://api.example.com/users"
        assert result["json"] == {"data": "value"}
        assert result["params"]["param"] == "value"
        assert result["headers"]["Custom"] == "header"
        assert result["headers"]["Extra"] == "header"
        assert result["headers"]["Authorization"] == "Mock-test"
        assert result["headers"]["content-type"] == "application/json"
        assert result["headers"]["x-sideko-sdk-language"] == "Python"
        assert result["timeout"] == 30

    @patch("make_api_request.utils.get_response_type", return_value="json")
    def test_process_response_204_status(self, mock_get_response_type):
        client = BaseClient("https://api.example.com")
        response = Mock()
        response.status_code = 204

        result = client.process_response(response=response, cast_to=str)

        assert result is None

    @patch("make_api_request.utils.get_response_type", return_value="json")
    def test_process_response_none_type(self, mock_get_response_type):
        client = BaseClient("https://api.example.com")
        response = Mock()
        response.status_code = 200

        result = client.process_response(response=response, cast_to=type(None))

        assert result is None

    def test_process_response_binary_response(self):
        client = BaseClient("https://api.example.com")
        response = Mock()
        response.status_code = 200
        response.content = b"binary data"
        response.headers = {"content-type": "application/octet-stream"}

        result = client.process_response(response=response, cast_to=BinaryResponse)

        assert isinstance(result, BinaryResponse)
        assert result.content == b"binary data"
        assert result.headers == {"content-type": "application/octet-stream"}

    @patch("make_api_request.utils.get_response_type", return_value="json")
    def test_process_response_json_any_type(self, mock_get_response_type):
        client = BaseClient("https://api.example.com")
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {"key": "value"}
        response.headers = httpx.Headers({"content-type": "application/json"})

        result = client.process_response(response=response, cast_to=type(Any))

        assert result == {"key": "value"}

    @patch("make_api_request.utils.get_response_type", return_value="json")
    def test_process_response_json_with_cast(self, mock_get_response_type):
        client = BaseClient("https://api.example.com")
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.json.return_value = {"key": "value"}
        response.headers = httpx.Headers({"content-type": "application/json"})

        # The actual code path: when cast_to is not type(Any), it calls from_encodable
        # But let's test the actual behavior rather than mocking it
        result = client.process_response(response=response, cast_to=dict)
        # The actual implementation should return the JSON data directly for simple cases
        assert isinstance(result, dict)
        assert "key" in result

    @patch("make_api_request.utils.get_response_type", return_value="text")
    def test_process_response_text(self, mock_get_response_type):
        client = BaseClient("https://api.example.com")
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.text = "text response"
        response.headers = httpx.Headers({"content-type": "text/plain"})

        result = client.process_response(response=response, cast_to=str)

        assert result == "text response"

    @patch("make_api_request.utils.get_response_type", return_value="binary")
    def test_process_response_binary(self, mock_get_response_type):
        client = BaseClient("https://api.example.com")
        response = Mock()
        response.status_code = 200
        response.content = b"binary content"
        response.headers = {"content-type": "application/pdf"}

        result = client.process_response(response=response, cast_to=str)

        assert isinstance(result, BinaryResponse)
        assert result.content == b"binary content"


class TestSyncBaseClient:
    def test_init(self):
        httpx_client = Mock(spec=httpx.Client)
        auth = MockAuthProvider("test")
        auths = {"test": auth}

        client = SyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client, auths=auths
        )

        assert client.httpx_client == httpx_client
        assert client._base_url == {_DEFAULT_SERVICE_NAME: "https://api.example.com"}
        assert client._auths == auths

    def test_request_success(self):
        httpx_client = Mock(spec=httpx.Client)
        response = Mock(spec=httpx.Response)
        response.is_success = True
        response.status_code = 200
        response.json.return_value = {"result": "success"}
        response.headers = httpx.Headers({"content-type": "application/json"})
        httpx_client.request.return_value = response

        with patch("make_api_request.utils.get_response_type", return_value="json"):
            client = SyncBaseClient(
                base_url="https://api.example.com", httpx_client=httpx_client
            )

            result = client.request(method="GET", path="/test", cast_to=type(Any))

        assert result == {"result": "success"}
        httpx_client.request.assert_called_once()

    def test_request_api_error(self):
        httpx_client = Mock(spec=httpx.Client)
        response = Mock()
        response.is_success = False
        response.status_code = 400
        httpx_client.request.return_value = response

        client = SyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client
        )

        with pytest.raises(ApiError):
            client.request(method="GET", path="/test", cast_to=dict)

    def test_request_raw_response(self):
        httpx_client = Mock(spec=httpx.Client)
        response = Mock(spec=httpx.Response)
        response.is_success = True
        httpx_client.request.return_value = response

        client = SyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client
        )

        result = client.request(method="GET", path="/test", cast_to=httpx.Response)

        assert result == response

    def test_stream_request(self):
        httpx_client = Mock(spec=httpx.Client)
        response = Mock(spec=httpx.Response)
        response.iter_bytes.return_value = iter([])

        # Create a proper context manager mock
        context = MagicMock()
        context.__enter__.return_value = response
        context.__exit__.return_value = None
        httpx_client.stream.return_value = context

        client = SyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client
        )

        result = client.stream_request(method="GET", path="/stream", cast_to=dict)

        assert isinstance(result, StreamResponse)
        assert result.response == response
        assert result.cast_to == dict  # noqa: E721
        httpx_client.stream.assert_called_once()


class TestAsyncBaseClient:
    def test_init(self):
        httpx_client = Mock(spec=httpx.AsyncClient)
        auth = MockAuthProvider("test")
        auths = {"test": auth}

        client = AsyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client, auths=auths
        )

        assert client.httpx_client == httpx_client
        assert client._base_url == {_DEFAULT_SERVICE_NAME: "https://api.example.com"}
        assert client._auths == auths

    @pytest.mark.asyncio
    async def test_request_success(self):
        httpx_client = Mock(spec=httpx.AsyncClient)
        response = Mock(spec=httpx.Response)
        response.is_success = True
        response.status_code = 200
        response.json.return_value = {"result": "success"}
        response.headers = httpx.Headers({"content-type": "application/json"})

        # Create async mock for request method
        async def mock_request(*args, **kwargs):
            return response

        httpx_client.request = mock_request

        with patch("make_api_request.utils.get_response_type", return_value="json"):
            client = AsyncBaseClient(
                base_url="https://api.example.com", httpx_client=httpx_client
            )

            result = await client.request(method="GET", path="/test", cast_to=type(Any))

        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_request_api_error(self):
        httpx_client = Mock(spec=httpx.AsyncClient)
        response = Mock(spec=httpx.Response)
        response.is_success = False
        response.status_code = 500

        # Create async mock for request method
        async def mock_request(*args, **kwargs):
            return response

        httpx_client.request = mock_request

        client = AsyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client
        )

        with pytest.raises(ApiError):
            await client.request(method="GET", path="/test", cast_to=dict)

    @pytest.mark.asyncio
    async def test_request_raw_response(self):
        httpx_client = Mock(spec=httpx.AsyncClient)
        response = Mock(spec=httpx.Response)
        response.is_success = True

        # Create async mock for request method
        async def mock_request(*args, **kwargs):
            return response

        httpx_client.request = mock_request

        client = AsyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client
        )

        result = await client.request(
            method="GET", path="/test", cast_to=httpx.Response
        )

        assert result == response

    @pytest.mark.asyncio
    async def test_stream_request(self):
        httpx_client = Mock(spec=httpx.AsyncClient)
        response = Mock(spec=httpx.Response)
        response.aiter_bytes.return_value = Mock()

        # Create a proper async context manager
        class AsyncContextManager:
            async def __aenter__(self):
                return response

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        context = AsyncContextManager()
        httpx_client.stream.return_value = context

        client = AsyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client
        )

        result = await client.stream_request(method="GET", path="/stream", cast_to=dict)

        assert isinstance(result, AsyncStreamResponse)
        assert result.response == response
        assert result.cast_to == dict  # noqa: E721
        httpx_client.stream.assert_called_once()


class TestRetryStrategy:
    @patch("make_api_request.base_client.sleep")
    def test_sync_client_retries_on_500_status(self, mock_sleep):
        httpx_client = Mock(spec=httpx.Client)

        # First call fails with 500, second succeeds
        responses = [
            Mock(spec=httpx.Response, is_success=False, status_code=500),
            Mock(
                spec=httpx.Response,
                is_success=True,
                status_code=200,
                json=Mock(return_value={"result": "success"}),
                headers=httpx.Headers({"content-type": "application/json"}),
            ),
        ]
        httpx_client.request.side_effect = responses

        retry_strategy: RetryStrategy = {"max_retries": 2, "initial_delay": 100}
        client = SyncBaseClient(
            base_url="https://api.example.com",
            httpx_client=httpx_client,
            retries=retry_strategy,
        )

        with patch("make_api_request.utils.get_response_type", return_value="json"):
            result = client.request(method="GET", path="/test", cast_to=type(Any))

        assert result == {"result": "success"}
        assert httpx_client.request.call_count == 2
        mock_sleep.assert_called_once_with(0.1)  # 100ms / 1000

    @patch("make_api_request.base_client.sleep")
    def test_sync_client_retries_with_exponential_backoff(self, mock_sleep):
        httpx_client = Mock(spec=httpx.Client)

        # All calls fail with 500 except the last one
        responses = [
            Mock(spec=httpx.Response, is_success=False, status_code=500),
            Mock(spec=httpx.Response, is_success=False, status_code=500),
            Mock(
                spec=httpx.Response,
                is_success=True,
                status_code=200,
                json=Mock(return_value={"result": "success"}),
                headers=httpx.Headers({"content-type": "application/json"}),
            ),
        ]
        httpx_client.request.side_effect = responses

        retry_strategy: RetryStrategy = {
            "max_retries": 3,
            "initial_delay": 100,
            "backoff_factor": 2.0,
            "max_delay": 1000,
        }
        client = SyncBaseClient(
            base_url="https://api.example.com",
            httpx_client=httpx_client,
            retries=retry_strategy,
        )

        with patch("make_api_request.utils.get_response_type", return_value="json"):
            result = client.request(method="GET", path="/test", cast_to=type(Any))

        assert result == {"result": "success"}
        assert httpx_client.request.call_count == 3
        # Should sleep 0.1s (100ms), then 0.2s (200ms)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.1)
        mock_sleep.assert_any_call(0.2)

    @patch("make_api_request.base_client.sleep")
    def test_sync_client_respects_max_retries(self, mock_sleep):
        httpx_client = Mock(spec=httpx.Client)

        # All calls fail with 500
        response = Mock(spec=httpx.Response, is_success=False, status_code=500)
        httpx_client.request.return_value = response

        retry_strategy: RetryStrategy = {"max_retries": 2, "initial_delay": 100}
        client = SyncBaseClient(
            base_url="https://api.example.com",
            httpx_client=httpx_client,
            retries=retry_strategy,
        )

        with pytest.raises(ApiError):
            client.request(method="GET", path="/test", cast_to=dict)

        # Should call 1 initial + 2 retries = 3 total calls
        assert httpx_client.request.call_count == 3
        # Should sleep twice (before each retry)
        assert mock_sleep.call_count == 2

    @patch("make_api_request.base_client.sleep")
    def test_sync_client_retries_on_configured_status_codes(self, mock_sleep):
        httpx_client = Mock(spec=httpx.Client)

        # First call fails with 429, second succeeds
        responses = [
            Mock(spec=httpx.Response, is_success=False, status_code=429),
            Mock(
                spec=httpx.Response,
                is_success=True,
                status_code=200,
                json=Mock(return_value={"result": "success"}),
                headers=httpx.Headers({"content-type": "application/json"}),
            ),
        ]
        httpx_client.request.side_effect = responses

        retry_strategy: RetryStrategy = {
            "max_retries": 2,
            "status_codes": [429, 5],  # 429 and 5XX range
            "initial_delay": 100,
        }
        client = SyncBaseClient(
            base_url="https://api.example.com",
            httpx_client=httpx_client,
            retries=retry_strategy,
        )

        with patch("make_api_request.utils.get_response_type", return_value="json"):
            result = client.request(method="GET", path="/test", cast_to=type(Any))

        assert result == {"result": "success"}
        assert httpx_client.request.call_count == 2
        mock_sleep.assert_called_once_with(0.1)

    @patch("make_api_request.base_client.sleep")
    def test_sync_client_does_not_retry_on_non_configured_status_codes(
        self, mock_sleep
    ):
        httpx_client = Mock(spec=httpx.Client)

        # Call fails with 404 (not in retry codes)
        response = Mock(spec=httpx.Response, is_success=False, status_code=404)
        httpx_client.request.return_value = response

        retry_strategy: RetryStrategy = {
            "max_retries": 2,
            "status_codes": [5],  # Only 5XX range
            "initial_delay": 100,
        }
        client = SyncBaseClient(
            base_url="https://api.example.com",
            httpx_client=httpx_client,
            retries=retry_strategy,
        )

        with pytest.raises(ApiError):
            client.request(method="GET", path="/test", cast_to=dict)

        # Should only call once (no retries for 404)
        assert httpx_client.request.call_count == 1
        mock_sleep.assert_not_called()

    @patch("make_api_request.base_client.sleep")
    def test_sync_client_request_options_override_retries(self, mock_sleep):
        httpx_client = Mock(spec=httpx.Client)

        # First call fails with 500, second succeeds
        responses = [
            Mock(spec=httpx.Response, is_success=False, status_code=500),
            Mock(
                spec=httpx.Response,
                is_success=True,
                status_code=200,
                json=Mock(return_value={"result": "success"}),
                headers=httpx.Headers({"content-type": "application/json"}),
            ),
        ]
        httpx_client.request.side_effect = responses

        # Base retry strategy with different delay
        base_retry_strategy: RetryStrategy = {"max_retries": 2, "initial_delay": 500}
        client = SyncBaseClient(
            base_url="https://api.example.com",
            httpx_client=httpx_client,
            retries=base_retry_strategy,
        )

        # Override with different delay
        override_retry: RetryStrategy = {"initial_delay": 200}
        request_options: RequestOptions = {"retries": override_retry}

        with patch("make_api_request.utils.get_response_type", return_value="json"):
            result = client.request(
                method="GET",
                path="/test",
                cast_to=type(Any),
                request_options=request_options,
            )

        assert result == {"result": "success"}
        assert httpx_client.request.call_count == 2
        # Should use override delay (200ms)
        mock_sleep.assert_called_once_with(0.2)

    @pytest.mark.asyncio
    @patch("make_api_request.base_client.async_sleep")
    async def test_async_client_retries_on_500_status(self, mock_async_sleep):
        httpx_client = Mock(spec=httpx.AsyncClient)

        # First call fails with 500, second succeeds
        responses = [
            Mock(spec=httpx.Response, is_success=False, status_code=500),
            Mock(
                spec=httpx.Response,
                is_success=True,
                status_code=200,
                json=Mock(return_value={"result": "success"}),
                headers=httpx.Headers({"content-type": "application/json"}),
            ),
        ]

        async def mock_request(*_args, **_kwargs):
            return responses.pop(0)

        httpx_client.request = mock_request

        retry_strategy: RetryStrategy = {"max_retries": 2, "initial_delay": 100}
        client = AsyncBaseClient(
            base_url="https://api.example.com",
            httpx_client=httpx_client,
            retries=retry_strategy,
        )

        with patch("make_api_request.utils.get_response_type", return_value="json"):
            result = await client.request(method="GET", path="/test", cast_to=type(Any))

        assert result == {"result": "success"}
        mock_async_sleep.assert_called_once_with(0.1)  # 100ms / 1000

    @pytest.mark.asyncio
    @patch("make_api_request.base_client.async_sleep")
    async def test_async_client_retries_with_exponential_backoff(
        self, mock_async_sleep
    ):
        httpx_client = Mock(spec=httpx.AsyncClient)

        # Track request calls
        request_call_count = 0
        responses = [
            Mock(spec=httpx.Response, is_success=False, status_code=500),
            Mock(spec=httpx.Response, is_success=False, status_code=500),
            Mock(
                spec=httpx.Response,
                is_success=True,
                status_code=200,
                json=Mock(return_value={"result": "success"}),
                headers=httpx.Headers({"content-type": "application/json"}),
            ),
        ]

        async def mock_request(*_args, **_kwargs):
            nonlocal request_call_count
            response = responses[request_call_count]
            request_call_count += 1
            return response

        httpx_client.request = mock_request

        retry_strategy: RetryStrategy = {
            "max_retries": 3,
            "initial_delay": 100,
            "backoff_factor": 2.0,
            "max_delay": 1000,
        }
        client = AsyncBaseClient(
            base_url="https://api.example.com",
            httpx_client=httpx_client,
            retries=retry_strategy,
        )

        with patch("make_api_request.utils.get_response_type", return_value="json"):
            result = await client.request(method="GET", path="/test", cast_to=type(Any))

        assert result == {"result": "success"}
        assert request_call_count == 3
        # Should sleep 0.1s (100ms), then 0.2s (200ms)
        assert mock_async_sleep.call_count == 2
        mock_async_sleep.assert_any_call(0.1)
        mock_async_sleep.assert_any_call(0.2)

    @pytest.mark.asyncio
    @patch("make_api_request.base_client.async_sleep")
    async def test_async_client_respects_max_retries(self, mock_async_sleep):
        httpx_client = Mock(spec=httpx.AsyncClient)

        # All calls fail with 500
        request_call_count = 0

        async def mock_request(*_args, **_kwargs):
            nonlocal request_call_count
            request_call_count += 1
            return Mock(spec=httpx.Response, is_success=False, status_code=500)

        httpx_client.request = mock_request

        retry_strategy: RetryStrategy = {"max_retries": 2, "initial_delay": 100}
        client = AsyncBaseClient(
            base_url="https://api.example.com",
            httpx_client=httpx_client,
            retries=retry_strategy,
        )

        with pytest.raises(ApiError):
            await client.request(method="GET", path="/test", cast_to=dict)

        # Should call 1 initial + 2 retries = 3 total calls
        assert request_call_count == 3
        # Should sleep twice (before each retry)
        assert mock_async_sleep.call_count == 2

    def test_sync_client_no_retries_when_not_configured(self):
        httpx_client = Mock(spec=httpx.Client)

        # Call fails with 500
        response = Mock(spec=httpx.Response, is_success=False, status_code=500)
        httpx_client.request.return_value = response

        # No retry strategy configured
        client = SyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client
        )

        with pytest.raises(ApiError):
            client.request(method="GET", path="/test", cast_to=dict)

        # Should only call once (no retries)
        assert httpx_client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_async_client_no_retries_when_not_configured(self):
        httpx_client = Mock(spec=httpx.AsyncClient)

        # Call fails with 500
        request_call_count = 0

        async def mock_request(*_args, **_kwargs):
            nonlocal request_call_count
            request_call_count += 1
            return Mock(spec=httpx.Response, is_success=False, status_code=500)

        httpx_client.request = mock_request

        # No retry strategy configured
        client = AsyncBaseClient(
            base_url="https://api.example.com", httpx_client=httpx_client
        )

        with pytest.raises(ApiError):
            await client.request(method="GET", path="/test", cast_to=dict)

        # Should only call once (no retries)
        assert request_call_count == 1
