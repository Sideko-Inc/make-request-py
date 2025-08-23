"""make-api-request: A modern Python HTTP client library with built-in authentication and response handling."""

from .api_error import ApiError
from .auth import (
    AuthBasic,
    AuthBearer,
    AuthKey,
    AuthProvider,
    GrantType,
    OAuth2,
    OAuth2ClientCredentials,
    OAuth2Password,
)
from .base_client import AsyncBaseClient, BaseClient, SyncBaseClient
from .binary_response import BinaryResponse
from .query import QueryParams, encode_query_param
from .request import (
    RequestOptions,
    default_request_options,
    filter_not_given,
    to_content,
    to_encodable,
    to_form_urlencoded,
)
from .response import AsyncStreamResponse, StreamResponse, from_encodable

__all__ = [
    "ApiError",
    "AsyncBaseClient",
    "BaseClient",
    "BinaryResponse",
    "RequestOptions",
    "default_request_options",
    "SyncBaseClient",
    "AuthKey",
    "AuthBasic",
    "AuthBearer",
    "AuthProvider",
    "GrantType",
    "OAuth2",
    "OAuth2ClientCredentials",
    "OAuth2Password",
    "to_encodable",
    "to_form_urlencoded",
    "filter_not_given",
    "to_content",
    "encode_query_param",
    "from_encodable",
    "AsyncStreamResponse",
    "StreamResponse",
    "QueryParams",
]
