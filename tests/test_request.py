from typing import Any, Dict, List
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, ValidationError

from make_request.request import (
    _get_default_for_type,
    default_request_options,
    filter_not_given,
    model_dump,
    to_content,
    to_encodable,
    to_form_urlencoded,
)
from make_request.type_utils import NOT_GIVEN


class RequestTestModel(BaseModel):
    name: str
    value: int
    optional_field: str = "default"


class RequestNestedModel(BaseModel):
    inner: RequestTestModel
    items: List[str]


class TestDefaultRequestOptions:
    def test_returns_empty_dict(self):
        options = default_request_options()
        assert options == {}
        assert isinstance(options, dict)


class TestModelDump:
    def test_with_pydantic_model(self):
        model = RequestTestModel(name="test", value=42)
        result = model_dump(model)

        expected = {"name": "test", "value": 42}
        assert result == expected

    def test_with_list_of_models(self):
        models = [
            RequestTestModel(name="first", value=1),
            RequestTestModel(name="second", value=2),
        ]
        result = model_dump(models)

        expected = [{"name": "first", "value": 1}, {"name": "second", "value": 2}]
        assert result == expected

    def test_with_nested_model(self):
        inner = RequestTestModel(name="inner", value=10)
        nested = RequestNestedModel(inner=inner, items=["a", "b", "c"])
        result = model_dump(nested)

        expected = {"inner": {"name": "inner", "value": 10}, "items": ["a", "b", "c"]}
        assert result == expected

    def test_with_non_model_object(self):
        data = {"key": "value", "number": 42}
        result = model_dump(data)
        assert result == data

    def test_with_primitive_types(self):
        assert model_dump("string") == "string"
        assert model_dump(42) == 42
        assert model_dump(3.14) == 3.14
        assert model_dump(True) is True
        assert model_dump(None) is None

    def test_with_mixed_list(self):
        model = RequestTestModel(name="test", value=1)
        mixed_list = [model, "string", 42, {"dict": "value"}]
        result = model_dump(mixed_list)

        expected = [{"name": "test", "value": 1}, "string", 42, {"dict": "value"}]
        assert result == expected


class TestToEncodable:
    def test_with_valid_data(self):
        data = {"name": "test", "value": 123}
        result = to_encodable(item=data, dump_with=RequestTestModel)

        expected = {"name": "test", "value": 123}
        assert result == expected

    def test_with_not_given_values(self):
        data = {"name": "test", "value": 123, "ignored": NOT_GIVEN}
        result = to_encodable(item=data, dump_with=RequestTestModel)

        expected = {"name": "test", "value": 123}
        assert result == expected

    def test_with_list_type(self):
        data = [1, 2, 3]
        result = to_encodable(item=data, dump_with=List[int])
        assert result == [1, 2, 3]

    def test_with_dict_type(self):
        data = {"key1": "value1", "key2": "value2"}
        result = to_encodable(item=data, dump_with=Dict[str, str])
        assert result == data

    def test_with_invalid_data(self):
        data = {"name": "test"}  # missing required 'value' field
        with pytest.raises(ValidationError):
            to_encodable(item=data, dump_with=RequestTestModel)

    def test_with_nested_not_given(self):
        data = {
            "name": "test",
            "value": 123,
            "nested": {"keep": "this", "remove": NOT_GIVEN},
        }
        # Using a more flexible type for this test
        result = to_encodable(item=data, dump_with=Dict[str, Any])

        expected = {"name": "test", "value": 123, "nested": {"keep": "this"}}
        assert result == expected


class TestToFormUrlencoded:
    def test_simple_object(self):
        data = {"name": "test", "value": 123}
        style = {}  # defaults to 'form'
        explode = {}  # defaults based on style

        result = to_form_urlencoded(
            item=data, dump_with=Dict[str, Any], style=style, explode=explode
        )

        assert result["name"] == "test"
        assert result["value"] == 123

    def test_with_list_form_style(self):
        data = {"ids": [1, 2, 3]}
        style = {"ids": "form"}
        explode = {"ids": False}  # non-exploded form

        result = to_form_urlencoded(
            item=data, dump_with=Dict[str, Any], style=style, explode=explode
        )

        assert result["ids"] == "1,2,3"

    def test_with_dict_form_style_exploded(self):
        data = {"obj": {"key1": "val1", "key2": "val2"}}
        style = {"obj": "form"}
        explode = {"obj": True}

        result = to_form_urlencoded(
            item=data, dump_with=Dict[str, Any], style=style, explode=explode
        )

        # When exploded, object keys become top-level parameters
        assert "key1" in result
        assert "key2" in result
        assert result["key1"] == "val1"
        assert result["key2"] == "val2"

    def test_with_space_delimited_style(self):
        data = {"ids": [1, 2, 3]}
        style = {"ids": "spaceDelimited"}
        explode = {"ids": False}

        result = to_form_urlencoded(
            item=data, dump_with=Dict[str, Any], style=style, explode=explode
        )

        assert result["ids"] == "1 2 3"

    def test_with_pipe_delimited_style(self):
        data = {"ids": [1, 2, 3]}
        style = {"ids": "pipeDelimited"}
        explode = {"ids": False}

        result = to_form_urlencoded(
            item=data, dump_with=Dict[str, Any], style=style, explode=explode
        )

        assert result["ids"] == "1|2|3"

    def test_with_deep_object_style(self):
        data = {"user": {"name": "john", "age": 30}}
        style = {"user": "deepObject"}
        explode = {"user": True}

        result = to_form_urlencoded(
            item=data, dump_with=Dict[str, Any], style=style, explode=explode
        )

        assert result["user[name]"] == "john"
        assert result["user[age]"] == "30"

    def test_non_dict_raises_error(self):
        data = [1, 2, 3]  # Not a dict
        style = {}
        explode = {}

        with pytest.raises(
            TypeError, match="x-www-form-urlencoded data must be an object"
        ):
            to_form_urlencoded(
                item=data, dump_with=List[int], style=style, explode=explode
            )

    def test_default_style_and_explode(self):
        data = {"simple": "value", "list": [1, 2]}
        style = {}  # Should default to 'form'
        explode = {}  # Should default based on style

        result = to_form_urlencoded(
            item=data, dump_with=Dict[str, Any], style=style, explode=explode
        )

        assert result["simple"] == "value"
        assert result["list"] == [1, 2]  # form + explode defaults to True for form


class TestToContent:
    def test_with_file_tuple_readable_content(self):
        mock_file = Mock()
        mock_file.read.return_value = b"file content"

        file_tuple = ("filename.txt", mock_file)
        result = to_content(file=file_tuple)

        assert result == b"file content"
        mock_file.read.assert_called_once()

    def test_with_file_tuple_bytes_content(self):
        file_tuple = ("filename.txt", b"file content")
        result = to_content(file=file_tuple)

        assert result == b"file content"

    def test_with_direct_readable_file(self):
        mock_file = Mock()
        mock_file.read.return_value = b"direct file content"

        result = to_content(file=mock_file)

        assert result == b"direct file content"
        mock_file.read.assert_called_once()

    def test_with_direct_bytes(self):
        content = b"direct bytes content"
        result = to_content(file=content)

        assert result == content

    def test_with_string_content(self):
        content = "string content"
        result = to_content(file=content)

        assert result == content

    def test_with_file_tuple_string_content(self):
        file_tuple = ("filename.txt", "string content")
        result = to_content(file=file_tuple)

        assert result == "string content"

    def test_with_file_like_object_without_read(self):
        # Object without read method
        content = {"not": "a file"}
        result = to_content(file=content)

        assert result == content


class TestFilterNotGiven:
    def test_with_not_given_value(self):
        result = filter_not_given(NOT_GIVEN)
        assert result is None

    def test_with_regular_value(self):
        assert filter_not_given("test") == "test"
        assert filter_not_given(42) == 42
        assert filter_not_given([1, 2, 3]) == [1, 2, 3]

    def test_with_dict_containing_not_given(self):
        data = {"keep": "this", "remove": NOT_GIVEN, "also_keep": 42}
        result = filter_not_given(data)

        expected = {"keep": "this", "also_keep": 42}
        assert result == expected

    def test_with_nested_dict(self):
        data = {
            "outer": {
                "keep": "value",
                "remove": NOT_GIVEN,
                "nested": {"deep_keep": "deep_value", "deep_remove": NOT_GIVEN},
            },
            "remove_outer": NOT_GIVEN,
        }
        result = filter_not_given(data)

        expected = {"outer": {"keep": "value", "nested": {"deep_keep": "deep_value"}}}
        assert result == expected

    def test_with_list_containing_not_given(self):
        data = [1, NOT_GIVEN, "keep", NOT_GIVEN, 3]
        result = filter_not_given(data)

        expected = [1, "keep", 3]
        assert result == expected

    def test_with_tuple_containing_not_given(self):
        data = (1, NOT_GIVEN, "keep", NOT_GIVEN, 3)
        result = filter_not_given(data)

        expected = (1, "keep", 3)
        assert result == expected

    def test_with_nested_list(self):
        data = [{"keep": "this", "remove": NOT_GIVEN}, NOT_GIVEN, [1, NOT_GIVEN, 2]]
        result = filter_not_given(data)

        expected = [{"keep": "this"}, [1, 2]]
        assert result == expected

    def test_empty_containers(self):
        assert filter_not_given({}) == {}
        assert filter_not_given([]) == []
        assert filter_not_given(()) == ()

    def test_all_not_given(self):
        data = {"all": NOT_GIVEN, "removed": NOT_GIVEN}
        result = filter_not_given(data)
        assert result == {}

        data_list = [NOT_GIVEN, NOT_GIVEN]
        result_list = filter_not_given(data_list)
        assert result_list == []


class TestGetDefaultForType:
    def test_dict_type(self):
        assert _get_default_for_type(dict) == {}
        assert (
            _get_default_for_type(Dict[str, Any]) is None
        )  # Generic types return None

    def test_list_type(self):
        assert _get_default_for_type(list) == []
        assert _get_default_for_type(List[int]) is None  # Generic types return None

    def test_other_types(self):
        assert _get_default_for_type(str) is None
        assert _get_default_for_type(int) is None
        assert _get_default_for_type(float) is None
        assert _get_default_for_type(bool) is None
        assert _get_default_for_type(type(None)) is None

    def test_custom_class(self):
        class CustomClass:
            pass

        assert _get_default_for_type(CustomClass) is None
