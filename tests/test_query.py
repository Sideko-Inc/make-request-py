import pytest

from make_request.query import (
    QueryParams,
    _encode_deep_object,
    _encode_deep_object_key,
    _encode_form,
    _encode_pipe_delimited,
    _encode_spaced_delimited,
    _query_str,
    encode_query_param,
)


class TestQueryStr:
    def test_string_value(self):
        assert _query_str("hello") == "hello"
        assert _query_str("") == ""
        assert _query_str("hello world") == "hello world"

    def test_numeric_values(self):
        assert _query_str(42) == "42"
        assert _query_str(3.14) == "3.14"
        assert _query_str(0) == "0"

    def test_boolean_values(self):
        assert _query_str(True) == "true"
        assert _query_str(False) == "false"

    def test_none_value(self):
        assert _query_str(None) == "null"

    def test_list_value(self):
        assert _query_str([1, 2, 3]) == "[1, 2, 3]"
        assert _query_str([]) == "[]"

    def test_dict_value(self):
        assert _query_str({"key": "value"}) == '{"key": "value"}'
        assert _query_str({}) == "{}"


class TestEncodeForm:
    def test_simple_value(self):
        params: QueryParams = {}
        _encode_form(params, "name", "value", explode=True)
        assert params == {"name": "value"}

    def test_list_explode_true(self):
        params: QueryParams = {}
        _encode_form(params, "id", [1, 2, 3], explode=True)
        assert params == {"id": [1, 2, 3]}

    def test_list_explode_false(self):
        params: QueryParams = {}
        _encode_form(params, "id", [1, 2, 3], explode=False)
        assert params == {"id": "1,2,3"}

    def test_list_mixed_types_explode_false(self):
        params: QueryParams = {}
        _encode_form(params, "mixed", ["a", 1, True], explode=False)
        assert params == {"mixed": "a,1,true"}

    def test_dict_explode_true(self):
        params: QueryParams = {}
        _encode_form(params, "obj", {"key1": "val1", "key2": "val2"}, explode=True)
        assert "key1" in params
        assert "key2" in params
        assert params["key1"] == "val1"
        assert params["key2"] == "val2"

    def test_dict_explode_false(self):
        params: QueryParams = {}
        _encode_form(params, "obj", {"key1": "val1", "key2": "val2"}, explode=False)
        # Order may vary, so check both possibilities
        result = params["obj"]
        assert result in ["key1,val1,key2,val2", "key2,val2,key1,val1"]

    def test_empty_list_explode_false(self):
        params: QueryParams = {}
        _encode_form(params, "empty", [], explode=False)
        assert params == {"empty": ""}

    def test_empty_dict_explode_false(self):
        params: QueryParams = {}
        _encode_form(params, "empty", {}, explode=False)
        assert params == {"empty": ""}


class TestEncodeSpaceDelimited:
    def test_list_explode_false(self):
        params: QueryParams = {}
        _encode_spaced_delimited(params, "id", [1, 2, 3], explode=False)
        assert params == {"id": "1 2 3"}

    def test_list_explode_true_falls_back_to_form(self):
        params: QueryParams = {}
        _encode_spaced_delimited(params, "id", [1, 2, 3], explode=True)
        assert params == {"id": [1, 2, 3]}

    def test_non_list_falls_back_to_form(self):
        params: QueryParams = {}
        _encode_spaced_delimited(params, "name", "value", explode=False)
        assert params == {"name": "value"}

    def test_dict_falls_back_to_form(self):
        params: QueryParams = {}
        _encode_spaced_delimited(params, "obj", {"key": "value"}, explode=True)
        assert params == {"key": "value"}

    def test_empty_list_explode_false(self):
        params: QueryParams = {}
        _encode_spaced_delimited(params, "empty", [], explode=False)
        assert params == {"empty": ""}


class TestEncodePipeDelimited:
    def test_list_explode_false(self):
        params: QueryParams = {}
        _encode_pipe_delimited(params, "id", [1, 2, 3], explode=False)
        assert params == {"id": "1|2|3"}

    def test_list_explode_true_falls_back_to_form(self):
        params: QueryParams = {}
        _encode_pipe_delimited(params, "id", [1, 2, 3], explode=True)
        assert params == {"id": [1, 2, 3]}

    def test_non_list_falls_back_to_form(self):
        params: QueryParams = {}
        _encode_pipe_delimited(params, "name", "value", explode=False)
        assert params == {"name": "value"}

    def test_dict_falls_back_to_form(self):
        params: QueryParams = {}
        _encode_pipe_delimited(params, "obj", {"key": "value"}, explode=True)
        assert params == {"key": "value"}

    def test_empty_list_explode_false(self):
        params: QueryParams = {}
        _encode_pipe_delimited(params, "empty", [], explode=False)
        assert params == {"empty": ""}


class TestEncodeDeepObject:
    def test_simple_dict(self):
        params: QueryParams = {}
        _encode_deep_object(params, "obj", {"key": "value"}, explode=True)
        assert params == {"obj[key]": "value"}

    def test_nested_dict(self):
        params: QueryParams = {}
        _encode_deep_object(
            params, "obj", {"level1": {"level2": "value"}}, explode=True
        )
        assert params == {"obj[level1][level2]": "value"}

    def test_list_value(self):
        params: QueryParams = {}
        _encode_deep_object(params, "arr", [1, 2, 3], explode=True)
        expected = {"arr[0]": "1", "arr[1]": "2", "arr[2]": "3"}
        assert params == expected

    def test_mixed_dict_and_list(self):
        params: QueryParams = {}
        _encode_deep_object(
            params, "obj", {"items": [1, 2], "name": "test"}, explode=True
        )
        expected = {"obj[items][0]": "1", "obj[items][1]": "2", "obj[name]": "test"}
        assert params == expected

    def test_primitive_falls_back_to_form(self):
        params: QueryParams = {}
        _encode_deep_object(params, "name", "value", explode=True)
        assert params == {"name": "value"}

    def test_empty_dict(self):
        params: QueryParams = {}
        _encode_deep_object(params, "empty", {}, explode=True)
        assert params == {}

    def test_empty_list(self):
        params: QueryParams = {}
        _encode_deep_object(params, "empty", [], explode=True)
        assert params == {}


class TestEncodeDeepObjectKey:
    def test_simple_value(self):
        params: QueryParams = {}
        _encode_deep_object_key(params, "key", "value")
        assert params == {"key": "value"}

    def test_dict_value(self):
        params: QueryParams = {}
        _encode_deep_object_key(params, "obj", {"a": 1, "b": 2})
        expected = {"obj[a]": "1", "obj[b]": "2"}
        assert params == expected

    def test_list_value(self):
        params: QueryParams = {}
        _encode_deep_object_key(params, "arr", ["x", "y", "z"])
        expected = {"arr[0]": "x", "arr[1]": "y", "arr[2]": "z"}
        assert params == expected

    def test_nested_structure(self):
        params: QueryParams = {}
        data = {"users": [{"name": "alice", "age": 30}]}
        _encode_deep_object_key(params, "data", data)
        expected = {"data[users][0][name]": "alice", "data[users][0][age]": "30"}
        assert params == expected


class TestEncodeQueryParam:
    def test_form_style(self):
        params: QueryParams = {}
        encode_query_param(params, "name", "value", style="form", explode=True)
        assert params == {"name": "value"}

    def test_space_delimited_style(self):
        params: QueryParams = {}
        encode_query_param(
            params, "id", [1, 2, 3], style="spaceDelimited", explode=False
        )
        assert params == {"id": "1 2 3"}

    def test_pipe_delimited_style(self):
        params: QueryParams = {}
        encode_query_param(
            params, "id", [1, 2, 3], style="pipeDelimited", explode=False
        )
        assert params == {"id": "1|2|3"}

    def test_deep_object_style(self):
        params: QueryParams = {}
        encode_query_param(
            params, "obj", {"key": "value"}, style="deepObject", explode=True
        )
        assert params == {"obj[key]": "value"}

    def test_invalid_style(self):
        params: QueryParams = {}
        with pytest.raises(
            NotImplementedError, match="query param style 'invalid' not implemented"
        ):
            encode_query_param(params, "name", "value", style="invalid")  # type: ignore

    def test_default_parameters(self):
        params: QueryParams = {}
        encode_query_param(params, "name", "value")
        assert params == {"name": "value"}

    def test_explode_false_default(self):
        params: QueryParams = {}
        encode_query_param(params, "id", [1, 2], explode=False)
        assert params == {"id": "1,2"}
