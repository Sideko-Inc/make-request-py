import httpx

from make_request import ApiError


def test_api_error_with_json_body():
    response = httpx.Response(
        status_code=400,
        json={"error": "Bad Request", "message": "Invalid input"},
        request=httpx.Request("GET", "https://example.com"),
    )

    error = ApiError(response=response)

    assert error.status_code == 400
    assert error.body == {"error": "Bad Request", "message": "Invalid input"}
    assert error.response == response
    assert "status_code: 400" in str(error)


def test_api_error_with_invalid_json():
    response = httpx.Response(
        status_code=500,
        content=b"Internal Server Error",
        request=httpx.Request("GET", "https://example.com"),
    )

    error = ApiError(response=response)

    assert error.status_code == 500
    assert error.body is None
    assert error.response == response


def test_api_error_string_representation():
    response = httpx.Response(
        status_code=404,
        json={"error": "Not Found"},
        request=httpx.Request("GET", "https://example.com"),
    )

    error = ApiError(response=response)
    expected = "status_code: 404, body: {'error': 'Not Found'}"

    assert str(error) == expected
