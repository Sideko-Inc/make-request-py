import datetime
from typing import Optional
from unittest.mock import Mock, patch

import pytest

from make_api_request.auth import (
    AuthBasic,
    AuthBearer,
    AuthKey,
    AuthProvider,
    OAuth2,
    OAuth2ClientCredentials,
    OAuth2Password,
)
from make_api_request.request import RequestConfig


class MockAuthProvider(AuthProvider):
    def __init__(self, value: Optional[str] = None):
        self.value = value

    def add_to_request(self, cfg: RequestConfig) -> RequestConfig:
        if self.value:
            headers = cfg.get("headers", {})
            headers["Mock-Auth"] = self.value
            cfg["headers"] = headers
        return cfg

    def set_value(self, val: Optional[str]) -> None:
        self.value = val


class TestAuthBasic:
    def test_init_with_credentials(self):
        auth = AuthBasic(username="testuser", password="testpass")
        assert auth.username == "testuser"
        assert auth.password == "testpass"

    def test_init_without_credentials(self):
        auth = AuthBasic()
        assert auth.username is None
        assert auth.password is None

    def test_add_to_request_with_both_credentials(self):
        auth = AuthBasic(username="user", password="pass")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = auth.add_to_request(cfg)

        assert result["auth"] == ("user", "pass")

    def test_add_to_request_with_missing_username(self):
        auth = AuthBasic(username=None, password="pass")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = auth.add_to_request(cfg)

        assert "auth" not in result

    def test_add_to_request_with_missing_password(self):
        auth = AuthBasic(username="user", password=None)
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = auth.add_to_request(cfg)

        assert "auth" not in result

    def test_set_value(self):
        auth = AuthBasic()
        auth.set_value("newuser")
        assert auth.username == "newuser"

    def test_add_to_request_preserves_other_config(self):
        auth = AuthBasic(username="user", password="pass")
        cfg: RequestConfig = {
            "method": "POST",
            "url": "https://example.com",
            "headers": {"Content-Type": "application/json"},
        }

        result = auth.add_to_request(cfg)

        assert result["method"] == "POST"
        assert result["url"] == "https://example.com"
        assert result["headers"]["Content-Type"] == "application/json"
        assert result["auth"] == ("user", "pass")


class TestAuthBearer:
    def test_init_with_token(self):
        auth = AuthBearer(token="test-token")
        assert auth.token == "test-token"

    def test_init_without_token(self):
        auth = AuthBearer()
        assert auth.token is None

    def test_add_to_request_with_token(self):
        auth = AuthBearer(token="my-token")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = auth.add_to_request(cfg)

        assert result["headers"]["Authorization"] == "Bearer my-token"

    def test_add_to_request_without_token(self):
        auth = AuthBearer(token=None)
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = auth.add_to_request(cfg)

        assert "headers" not in result

    def test_add_to_request_with_existing_headers(self):
        auth = AuthBearer(token="token123")
        cfg: RequestConfig = {
            "method": "GET",
            "url": "https://example.com",
            "headers": {"Content-Type": "application/json"},
        }

        result = auth.add_to_request(cfg)

        assert result["headers"]["Content-Type"] == "application/json"
        assert result["headers"]["Authorization"] == "Bearer token123"

    def test_set_value(self):
        auth = AuthBearer()
        auth.set_value("new-token")
        assert auth.token == "new-token"

    def test_add_to_request_overwrites_existing_auth_header(self):
        auth = AuthBearer(token="new-token")
        cfg: RequestConfig = {
            "method": "GET",
            "url": "https://example.com",
            "headers": {"Authorization": "Basic old-auth"},
        }

        result = auth.add_to_request(cfg)

        assert result["headers"]["Authorization"] == "Bearer new-token"


class TestAuthKey:
    def test_init_query_location(self):
        auth = AuthKey(name="api_key", location="query", val="test-key")
        assert auth.name == "api_key"
        assert auth.location == "query"
        assert auth.val == "test-key"

    def test_init_header_location(self):
        auth = AuthKey(name="X-API-Key", location="header", val="header-key")
        assert auth.name == "X-API-Key"
        assert auth.location == "header"
        assert auth.val == "header-key"

    def test_init_cookie_location(self):
        auth = AuthKey(name="session_id", location="cookie", val="cookie-value")
        assert auth.name == "session_id"
        assert auth.location == "cookie"
        assert auth.val == "cookie-value"

    def test_add_to_request_query_location(self):
        auth = AuthKey(name="api_key", location="query", val="query-key")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = auth.add_to_request(cfg)

        assert result["params"]["api_key"] == "query-key"

    def test_add_to_request_header_location(self):
        auth = AuthKey(name="X-API-Key", location="header", val="header-key")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = auth.add_to_request(cfg)

        assert result["headers"]["X-API-Key"] == "header-key"

    def test_add_to_request_cookie_location(self):
        auth = AuthKey(name="session_id", location="cookie", val="cookie-value")
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = auth.add_to_request(cfg)

        assert result["cookies"]["session_id"] == "cookie-value"

    def test_add_to_request_without_value(self):
        auth = AuthKey(name="api_key", location="query", val=None)
        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}

        result = auth.add_to_request(cfg)

        assert "params" not in result

    def test_add_to_request_with_existing_params(self):
        auth = AuthKey(name="api_key", location="query", val="key123")
        cfg: RequestConfig = {
            "method": "GET",
            "url": "https://example.com",
            "params": {"existing": "param"},
        }

        result = auth.add_to_request(cfg)

        assert result["params"]["existing"] == "param"
        assert result["params"]["api_key"] == "key123"

    def test_add_to_request_with_existing_headers(self):
        auth = AuthKey(name="X-Custom", location="header", val="custom-value")
        cfg: RequestConfig = {
            "method": "GET",
            "url": "https://example.com",
            "headers": {"Content-Type": "application/json"},
        }

        result = auth.add_to_request(cfg)

        assert result["headers"]["Content-Type"] == "application/json"
        assert result["headers"]["X-Custom"] == "custom-value"

    def test_add_to_request_with_existing_cookies(self):
        auth = AuthKey(name="auth_token", location="cookie", val="token123")
        cfg: RequestConfig = {
            "method": "GET",
            "url": "https://example.com",
            "cookies": {"session": "abc123"},
        }

        result = auth.add_to_request(cfg)

        assert result["cookies"]["session"] == "abc123"
        assert result["cookies"]["auth_token"] == "token123"

    def test_set_value(self):
        auth = AuthKey(name="api_key", location="query")
        auth.set_value("new-key")
        assert auth.val == "new-key"


class TestOAuth2:
    def test_init_with_client_credentials(self):
        mock_mutator = MockAuthProvider()
        form: OAuth2ClientCredentials = {
            "client_id": "test-client",
            "client_secret": "test-secret",
            "grant_type": "client_credentials",
            "scope": ["read", "write"],
            "token_url": None,
        }

        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="json",
            request_mutator=mock_mutator,
            form=form,
        )

        assert oauth.client_id == "test-client"
        assert oauth.client_secret == "test-secret"
        assert oauth.grant_type == "client_credentials"
        assert oauth.scope == ["read", "write"]
        assert oauth.username is None
        assert oauth.password is None

    def test_init_with_password_flow(self):
        mock_mutator = MockAuthProvider()
        form: OAuth2Password = {
            "username": "testuser",
            "password": "testpass",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "grant_type": "password",
            "scope": ["user"],
            "token_url": "/custom/token",
        }

        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="basic_authorization_header",
            body_content="form",
            request_mutator=mock_mutator,
            form=form,
        )

        assert oauth.username == "testuser"
        assert oauth.password == "testpass"
        assert oauth.grant_type == "password"
        assert oauth.token_url == "/custom/token"  # Custom token URL

    def test_init_defaults_grant_type_based_on_username(self):
        mock_mutator = MockAuthProvider()

        # With username - should default to password
        form_password: OAuth2Password = {
            "username": "user",
            "password": "pass",
            "client_id": None,
            "client_secret": None,
            "grant_type": None,
            "scope": None,
            "token_url": None,
        }
        oauth_password = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="json",
            request_mutator=mock_mutator,
            form=form_password,
        )
        assert oauth_password.grant_type == "password"

        # Without username - should default to client_credentials
        form_client: OAuth2ClientCredentials = {
            "client_id": "client",
            "client_secret": "secret",
            "grant_type": None,
            "scope": None,
            "token_url": None,
        }
        oauth_client = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="json",
            request_mutator=mock_mutator,
            form=form_client,
        )
        assert oauth_client.grant_type == "client_credentials"

    @patch("httpx.post")
    def test_refresh_with_json_body(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new-token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="json",
            request_mutator=mock_mutator,
            form={
                "client_id": "test-client",
                "client_secret": "test-secret",
                "grant_type": "client_credentials",
                "scope": None,
                "token_url": None,
            },
        )

        token, expires_at = oauth._refresh()

        assert token == "new-token"
        assert isinstance(expires_at, datetime.datetime)

        mock_post.assert_called_once()
        call_args = mock_post.call_args.kwargs
        assert call_args["json"]["grant_type"] == "client_credentials"
        assert call_args["json"]["client_id"] == "test-client"
        assert call_args["json"]["client_secret"] == "test-secret"
        assert call_args["headers"]["content-type"] == "application/json"

    @patch("httpx.post")
    def test_refresh_with_form_body(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "form-token",
            "expires_in": 1800,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="form",
            request_mutator=mock_mutator,
            form={
                "client_id": "form-client",
                "client_secret": "form-secret",
                "grant_type": "client_credentials",
                "scope": None,
                "token_url": None,
            },
        )

        token, expires_at = oauth._refresh()

        assert token == "form-token"

        mock_post.assert_called_once()
        call_args = mock_post.call_args.kwargs
        assert call_args["data"]["grant_type"] == "client_credentials"
        assert (
            call_args["headers"]["content-type"] == "application/x-www-form-urlencoded"
        )

    @patch("httpx.post")
    def test_refresh_with_basic_auth_credentials(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "basic-auth-token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="basic_authorization_header",
            body_content="form",
            request_mutator=mock_mutator,
            form={
                "client_id": "basic-client",
                "client_secret": "basic-secret",
                "grant_type": "client_credentials",
                "scope": None,
                "token_url": None,
            },
        )

        oauth._refresh()

        mock_post.assert_called_once()
        call_args = mock_post.call_args.kwargs
        assert call_args["auth"] == ("basic-client", "basic-secret")
        assert "client_id" not in call_args["data"]
        assert "client_secret" not in call_args["data"]

    @patch("httpx.post")
    def test_refresh_with_scope(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "scoped-token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="form",
            request_mutator=mock_mutator,
            form={
                "client_id": "client",
                "client_secret": "secret",
                "grant_type": "client_credentials",
                "scope": ["read", "write", "admin"],
                "token_url": None,
            },
        )

        oauth._refresh()

        mock_post.assert_called_once()
        call_args = mock_post.call_args.kwargs
        assert call_args["data"]["scope"] == "read write admin"

    @patch("httpx.post")
    def test_refresh_with_password_flow_data(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "password-token",
            "expires_in": 7200,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="form",
            request_mutator=mock_mutator,
            form={
                "username": "testuser",
                "password": "testpass",
                "client_id": "client",
                "client_secret": "secret",
                "grant_type": "password",
                "scope": None,
                "token_url": None,
            },
        )

        oauth._refresh()

        mock_post.assert_called_once()
        call_args = mock_post.call_args.kwargs
        assert call_args["data"]["username"] == "testuser"
        assert call_args["data"]["password"] == "testpass"
        assert call_args["data"]["grant_type"] == "password"

    @patch("httpx.post")
    def test_refresh_with_relative_token_url(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "relative-url-token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com/",  # Note the trailing slash
            default_token_url="/oauth/token",  # Note the leading slash
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="form",
            request_mutator=mock_mutator,
            form={
                "client_id": "client",
                "client_secret": "secret",
                "grant_type": "client_credentials",
                "scope": None,
                "token_url": None,
            },
        )

        oauth._refresh()

        mock_post.assert_called_once()
        call_args = mock_post.call_args.kwargs
        assert call_args["url"] == "https://api.example.com/oauth/token"

    @patch("httpx.post")
    def test_refresh_with_invalid_expires_in(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "token-without-expiry",
            "expires_in": "not-an-integer",  # Invalid type
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="form",
            request_mutator=mock_mutator,
            form={
                "client_id": "client",
                "client_secret": "secret",
                "grant_type": "client_credentials",
                "scope": None,
                "token_url": None,
            },
        )

        token, expires_at = oauth._refresh()

        # Should default to 600 seconds when expires_in is not an integer
        assert token == "token-without-expiry"
        now = datetime.datetime.now()
        expected_expiry = now + datetime.timedelta(seconds=540)  # 600 - 60 buffer
        assert (
            abs((expires_at - expected_expiry).total_seconds()) < 5
        )  # Allow 5 second tolerance

    def test_add_to_request_without_credentials(self):
        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="form",
            request_mutator=mock_mutator,
        )

        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        result = oauth.add_to_request(cfg)

        # Should return unchanged config when no credentials are set
        assert result == cfg

    @patch.object(OAuth2, "_refresh")
    def test_add_to_request_with_valid_token(self, mock_refresh):
        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="form",
            request_mutator=mock_mutator,
            form={
                "client_id": "client",
                "client_secret": "secret",
                "grant_type": "client_credentials",
                "scope": None,
                "token_url": None,
            },
        )

        # Set valid token that hasn't expired
        oauth.access_token = "existing-token"
        oauth.expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)

        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        result = oauth.add_to_request(cfg)

        # Should not call refresh since token is still valid
        mock_refresh.assert_not_called()

        # Should use existing token with mutator
        assert result["headers"]["Mock-Auth"] == "existing-token"

    @patch.object(OAuth2, "_refresh")
    def test_add_to_request_with_expired_token(self, mock_refresh):
        mock_refresh.return_value = (
            "new-token",
            datetime.datetime.now() + datetime.timedelta(hours=1),
        )

        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="form",
            request_mutator=mock_mutator,
            form={
                "client_id": "client",
                "client_secret": "secret",
                "grant_type": "client_credentials",
                "scope": None,
                "token_url": None,
            },
        )

        # Set expired token
        oauth.access_token = "expired-token"
        oauth.expires_at = datetime.datetime.now() - datetime.timedelta(hours=1)

        cfg: RequestConfig = {"method": "GET", "url": "https://example.com"}
        result = oauth.add_to_request(cfg)

        # Should call refresh since token is expired
        mock_refresh.assert_called_once()

        # Should use new token
        assert result["headers"]["Mock-Auth"] == "new-token"
        assert oauth.access_token == "new-token"

    def test_set_value_raises_not_implemented(self):
        mock_mutator = MockAuthProvider()
        oauth = OAuth2(
            base_url="https://api.example.com",
            default_token_url="/oauth/token",
            access_token_pointer="/access_token",
            expires_in_pointer="/expires_in",
            credentials_location="request_body",
            body_content="form",
            request_mutator=mock_mutator,
        )

        with pytest.raises(
            NotImplementedError,
            match="an OAuth2 auth provider cannot be a request_mutator",
        ):
            oauth.set_value("some-value")
