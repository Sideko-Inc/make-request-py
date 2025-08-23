from typing import Any, Dict, List
from unittest.mock import Mock

import httpx
import pytest
from pydantic import BaseModel

from make_request.response import AsyncStreamResponse, StreamResponse, from_encodable


class ResponseTestModel(BaseModel):
    name: str
    value: int


class ResponseDataModel(BaseModel):
    data: Any  # Changed to Any to accept strings, dicts, etc.


def test_from_encodable_basic_types():
    assert from_encodable(data="test", load_with=str) == "test"
    assert from_encodable(data=42, load_with=int) == 42
    assert from_encodable(data=3.14, load_with=float) == 3.14
    assert from_encodable(data=None, load_with=type(None)) is None


def test_from_encodable_with_pydantic_model():
    data = {"name": "test", "value": 123}
    result = from_encodable(data=data, load_with=ResponseTestModel)
    assert isinstance(result, ResponseTestModel)
    assert result.name == "test"
    assert result.value == 123


def test_from_encodable_with_dict():
    data = {"key": "value", "number": 42}
    result = from_encodable(data=data, load_with=Dict[str, Any])
    assert result == data


def test_from_encodable_with_list():
    data = [1, 2, 3]
    result = from_encodable(data=data, load_with=List[int])
    assert result == data


class TestStreamResponse:
    def test_init(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, str)

        assert stream.response == response
        assert stream._context == context
        assert isinstance(stream.cast_to, type(str))
        assert isinstance(stream.buffer, bytearray)
        assert stream.position == 0

    def test_iter(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, str)
        assert iter(stream) == stream

    def test_parse_sse_simple_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, str)

        message = "data: hello world"
        result = stream._parse_sse(message)
        assert result == "hello world"

    def test_parse_sse_multiline_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, str)

        message = "data: line 1\ndata: line 2\ndata: line 3"
        result = stream._parse_sse(message)
        assert result == "line 1\nline 2\nline 3"

    def test_parse_sse_empty_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, str)

        message = "data:"
        result = stream._parse_sse(message)
        assert result == ""

    def test_parse_sse_no_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, str)

        message = "event: test\nid: 123"
        result = stream._parse_sse(message)
        assert result is None

    def test_process_buffer_with_json_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, ResponseDataModel)
        stream.buffer = bytearray(b'data: {"key": "value"}\r\n\r\n')

        result = stream._process_buffer()

        assert isinstance(result, ResponseDataModel)
        assert result.data == {"key": "value"}

    def test_process_buffer_with_non_json_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, ResponseDataModel)
        stream.buffer = bytearray(b"data: plain text\r\n\r\n")

        result = stream._process_buffer()

        assert isinstance(result, ResponseDataModel)
        assert (
            result.data == "plain text"
        )  # Non-JSON data becomes the data field directly

    def test_process_buffer_with_different_boundaries(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, ResponseDataModel)

        # Test \n\n boundary
        stream.buffer = bytearray(b"data: test1\n\n")
        stream.position = 0
        result = stream._process_buffer()
        assert result.data == "test1"

        # Test \r\r boundary
        stream.buffer = bytearray(b"data: test2\r\r")
        stream.position = 0
        result = stream._process_buffer()
        assert result.data == "test2"

    def test_next_with_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()

        # Mock iterator to provide chunks of data
        response.iter_bytes.return_value = iter(
            [b'data: {"test": "value"}', b"\r\n\r\n"]
        )

        stream = StreamResponse(response, context, ResponseDataModel)

        result = next(stream)
        assert isinstance(result, ResponseDataModel)
        assert result.data == {"test": "value"}

    def test_next_stop_iteration(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        context.__exit__ = Mock()

        # Empty iterator to trigger StopIteration
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, ResponseDataModel)

        with pytest.raises(StopIteration):
            next(stream)

        context.__exit__.assert_called_once_with(None, None, None)

    def test_process_buffer_final_with_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.iter_bytes.return_value = iter([])

        stream = StreamResponse(response, context, ResponseDataModel)
        stream.buffer = bytearray(b"data: final data")

        result = stream._process_buffer(final=True)

        assert isinstance(result, ResponseDataModel)
        assert result.data == "final data"


class TestAsyncStreamResponse:
    def test_init(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.aiter_bytes.return_value = Mock()

        stream = AsyncStreamResponse(response, context, str)

        assert stream.response == response
        assert stream._context == context
        assert isinstance(stream.cast_to, type(str))
        assert isinstance(stream.buffer, bytearray)
        assert stream.position == 0

    def test_aiter(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.aiter_bytes.return_value = Mock()

        stream = AsyncStreamResponse(response, context, str)
        assert stream.__aiter__() == stream

    def test_parse_sse_simple_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.aiter_bytes.return_value = Mock()

        stream = AsyncStreamResponse(response, context, str)

        message = "data: hello world"
        result = stream._parse_sse(message)
        assert result == "hello world"

    def test_parse_sse_multiline_with_strip(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.aiter_bytes.return_value = Mock()

        stream = AsyncStreamResponse(response, context, str)

        message = "  data: line 1  \n  data: line 2  "
        result = stream._parse_sse(message)
        assert result == "line 1\nline 2"

    @pytest.mark.asyncio
    async def test_anext_with_data(self):
        response = Mock(spec=httpx.Response)
        context = Mock()

        # Create a proper async iterator mock
        class AsyncIteratorMock:
            def __init__(self):
                self.values = [b'data: {"test": "value"}', b"\r\n\r\n"]
                self.index = 0

            async def __anext__(self):
                if self.index >= len(self.values):
                    raise StopAsyncIteration
                value = self.values[self.index]
                self.index += 1
                return value

        response.aiter_bytes.return_value = AsyncIteratorMock()

        stream = AsyncStreamResponse(response, context, ResponseDataModel)

        result = await stream.__anext__()
        assert isinstance(result, ResponseDataModel)
        assert result.data == {"test": "value"}

    @pytest.mark.asyncio
    async def test_anext_stop_iteration(self):
        response = Mock(spec=httpx.Response)
        context = Mock()

        # Create async mock for context
        async def mock_aexit(*args):
            pass

        context.__aexit__ = mock_aexit

        # Create empty async iterator
        class EmptyAsyncIteratorMock:
            async def __anext__(self):
                raise StopAsyncIteration

        response.aiter_bytes.return_value = EmptyAsyncIteratorMock()

        stream = AsyncStreamResponse(response, context, ResponseDataModel)

        with pytest.raises(StopAsyncIteration):
            await stream.__anext__()

    def test_process_buffer_json_without_data_key(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.aiter_bytes.return_value = Mock()

        stream = AsyncStreamResponse(response, context, ResponseDataModel)
        stream.buffer = bytearray(b'data: "just a string"\r\n\r\n')

        result = stream._process_buffer()

        assert isinstance(result, ResponseDataModel)
        assert result.data == "just a string"

    def test_process_buffer_final_empty_buffer(self):
        response = Mock(spec=httpx.Response)
        context = Mock()
        response.aiter_bytes.return_value = Mock()

        stream = AsyncStreamResponse(response, context, ResponseDataModel)
        stream.buffer = bytearray()

        result = stream._process_buffer(final=True)
        assert result is None
