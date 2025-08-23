import typing
from typing import Any, Dict, Union

import httpx
import pytest

from make_api_request.binary_response import BinaryResponse
from make_api_request.utils import (
    filter_binary_response,
    get_response_type,
    is_union_type,
    remove_none_from_dict,
)


class TestRemoveNoneFromDict:
    def test_empty_dict(self):
        result = remove_none_from_dict({})
        assert result == {}

    def test_no_none_values(self):
        original = {"key1": "value1", "key2": 42, "key3": True}
        result = remove_none_from_dict(original)
        assert result == original

    def test_all_none_values(self):
        original = {"key1": None, "key2": None, "key3": None}
        result = remove_none_from_dict(original)
        assert result == {}

    def test_mixed_values(self):
        original = {
            "keep1": "value1",
            "remove1": None,
            "keep2": 42,
            "remove2": None,
            "keep3": False,
            "keep4": 0,
            "keep5": "",
        }
        expected = {
            "keep1": "value1",
            "keep2": 42,
            "keep3": False,
            "keep4": 0,
            "keep5": "",
        }
        result = remove_none_from_dict(original)
        assert result == expected

    def test_nested_structures_with_none(self):
        original = {
            "list": [1, 2, None],  # None inside list should be kept
            "dict": {"nested": None},  # None inside nested dict should be kept
            "none_key": None,  # This should be removed
        }
        expected = {
            "list": [1, 2, None],
            "dict": {"nested": None},
        }
        result = remove_none_from_dict(original)
        assert result == expected


class TestGetResponseType:
    def test_json_content_type(self):
        headers = httpx.Headers({"content-type": "application/json"})
        assert get_response_type(headers) == "json"

    def test_json_with_charset(self):
        headers = httpx.Headers({"content-type": "application/json; charset=utf-8"})
        assert get_response_type(headers) == "json"

    def test_json_with_plus_suffix(self):
        headers = httpx.Headers({"content-type": "application/vnd.api+json"})
        assert get_response_type(headers) == "json"

    def test_text_content_type(self):
        headers = httpx.Headers({"content-type": "text/plain"})
        assert get_response_type(headers) == "text"

    def test_text_html(self):
        headers = httpx.Headers({"content-type": "text/html"})
        assert get_response_type(headers) == "text"

    def test_text_with_charset(self):
        headers = httpx.Headers({"content-type": "text/plain; charset=utf-8"})
        assert get_response_type(headers) == "text"

    def test_binary_content_type(self):
        headers = httpx.Headers({"content-type": "application/octet-stream"})
        assert get_response_type(headers) == "binary"

    def test_image_content_type(self):
        headers = httpx.Headers({"content-type": "image/png"})
        assert get_response_type(headers) == "binary"

    def test_no_content_type_header(self):
        headers = httpx.Headers({})
        # This will cause a TypeError as designed - the function expects content-type to exist
        with pytest.raises(TypeError):
            get_response_type(headers)

    def test_empty_content_type(self):
        headers = httpx.Headers({"content-type": ""})
        assert get_response_type(headers) == "binary"

    def test_case_insensitive_headers(self):
        headers = httpx.Headers({"Content-Type": "application/json"})
        assert get_response_type(headers) == "json"

    def test_unknown_application_type(self):
        headers = httpx.Headers({"content-type": "application/pdf"})
        assert get_response_type(headers) == "binary"


class TestIsUnionType:
    def test_union_type(self):
        union_type = Union[str, int]
        assert is_union_type(union_type) is True

    def test_union_with_none(self):
        union_type = Union[str, None]
        assert is_union_type(union_type) is True

    def test_multiple_union(self):
        union_type = Union[str, int, float, bool]
        assert is_union_type(union_type) is True

    def test_non_union_type(self):
        assert is_union_type(str) is False
        assert is_union_type(int) is False
        assert is_union_type(list) is False
        assert is_union_type(dict) is False

    def test_generic_types(self):
        assert is_union_type(typing.List[str]) is False
        assert is_union_type(typing.Dict[str, int]) is False

    def test_none_type(self):
        assert is_union_type(type(None)) is False

    def test_optional_type(self):
        # Optional[T] is equivalent to Union[T, None]
        optional_type = typing.Optional[str]
        assert is_union_type(optional_type) is True

    def test_callable_type(self):
        callable_type = typing.Callable[[int], str]
        assert is_union_type(callable_type) is False


class TestFilterBinaryResponse:
    def test_non_union_type(self):
        result = filter_binary_response(str)
        assert result == str

    def test_non_union_binary_response(self):
        result = filter_binary_response(BinaryResponse)
        assert result == BinaryResponse

    def test_union_with_binary_response(self):
        union_type = Union[str, BinaryResponse]
        result = filter_binary_response(union_type)
        assert result == str

    def test_union_with_multiple_types_and_binary_response(self):
        union_type = Union[str, int, BinaryResponse]
        result = filter_binary_response(union_type)
        # Should return Union[str, int]
        args = typing.get_args(result)
        assert str in args
        assert int in args
        assert BinaryResponse not in args
        assert len(args) == 2

    def test_union_only_binary_response(self):
        union_type = Union[BinaryResponse]
        result = filter_binary_response(union_type)
        # Should return original type if everything filtered out
        assert result == union_type

    def test_union_without_binary_response(self):
        union_type = Union[str, int]
        result = filter_binary_response(union_type)
        assert result == union_type

    def test_complex_union_filtering(self):
        union_type = Union[str, int, BinaryResponse, Dict[str, Any]]
        result = filter_binary_response(union_type)
        args = typing.get_args(result)
        assert str in args
        assert int in args
        assert Dict[str, Any] in args
        assert BinaryResponse not in args
        assert len(args) == 3

    def test_union_with_none(self):
        union_type = Union[str, None, BinaryResponse]
        result = filter_binary_response(union_type)
        args = typing.get_args(result)
        assert str in args
        assert type(None) in args
        assert BinaryResponse not in args
        assert len(args) == 2

    def test_single_type_after_filtering(self):
        union_type = Union[str, BinaryResponse]
        result = filter_binary_response(union_type)
        # When only one type remains, should return that type directly
        assert result is str

    def test_empty_union_filtered(self):
        # This would be an edge case - Union with only BinaryResponse
        union_type = Union[BinaryResponse]
        result = filter_binary_response(union_type)
        # Should return original if everything filtered out
        assert result == union_type
