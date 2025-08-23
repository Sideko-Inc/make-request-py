# make-api-request

A modern Python HTTP client library with built-in authentication and response handling.

## Features

- 🚀 **Modern async/sync support** - Built on httpx with full async/await support
- 🔐 **Built-in authentication** - Support for API keys, Basic auth, Bearer tokens, and OAuth2
- 📦 **Type-safe** - Full type hints with Pydantic models
- 🔄 **Flexible responses** - Handle JSON, binary, and streaming responses
- 🛡️ **Error handling** - Comprehensive API error handling with detailed context
- ⚡ **Performance** - Efficient request building and response parsing

## Installation

```bash
pip install make-api-request
```

Or with Poetry:

```bash
poetry add make-api-request
```

## Quick Start

### Basic Usage

```python
import asyncio
from make_api_request import AsyncBaseClient

async def main():
    client = AsyncBaseClient("https://api.example.com")
    
    # Simple GET request
    response = await client.get("/users")
    print(response)

asyncio.run(main())
```

### With Authentication

```python
from make_api_request import AsyncBaseClient, AuthBearer

async def main():
    # Bearer token authentication
    auth = AuthBearer("your-token-here")
    client = AsyncBaseClient(
        "https://api.example.com",
        auths={"bearer": auth}
    )
    
    response = await client.get("/protected-endpoint")
    print(response)

asyncio.run(main())
```

### Synchronous Usage

```python
from make_api_request import SyncBaseClient, AuthKey

# API key authentication
auth = AuthKey("x-api-key", "your-api-key")
client = SyncBaseClient(
    "https://api.example.com",
    auths={"api_key": auth}
)

response = client.get("/users")
print(response)
```

## Authentication Types

### API Key Authentication

```python
from make_api_request import AuthKey

# Header-based API key
auth = AuthKey("x-api-key", "your-api-key")

# Query parameter API key  
auth = AuthKey("api_key", "your-api-key", location="query")
```

### Bearer Token

```python
from make_api_request import AuthBearer

auth = AuthBearer("your-jwt-token")
```

### Basic Authentication

```python
from make_api_request import AuthBasic

auth = AuthBasic("username", "password")
```

### OAuth2

```python
from make_api_request import OAuth2ClientCredentials

auth = OAuth2ClientCredentials(
    token_url="https://auth.example.com/token",
    client_id="your-client-id",
    client_secret="your-client-secret"
)
```

## Advanced Usage

### Custom Request Options

```python
from make_api_request import RequestOptions

options = RequestOptions(
    timeout=30.0,
    headers={"Custom-Header": "value"},
    max_retries=3
)

response = await client.get("/endpoint", options=options)
```

### Binary Responses

```python
# Download a file
binary_response = await client.get("/download/file.pdf")
if isinstance(binary_response, BinaryResponse):
    with open("file.pdf", "wb") as f:
        f.write(binary_response.content)
```

### Streaming Responses

```python
async with client.stream("GET", "/large-dataset") as response:
    async for chunk in response.iter_content():
        process_chunk(chunk)
```

### Error Handling

```python
from make_api_request import ApiError

try:
    response = await client.get("/might-fail")
except ApiError as e:
    print(f"API Error: {e.status_code}")
    print(f"Response body: {e.body}")
    print(f"Full response: {e.response}")
```

## API Reference

### Client Classes

- **`AsyncBaseClient`** - Asynchronous HTTP client
- **`SyncBaseClient`** - Synchronous HTTP client  
- **`BaseClient`** - Base class for client implementations

### Authentication

- **`AuthKey`** - API key authentication (header or query parameter)
- **`AuthBasic`** - HTTP Basic authentication
- **`AuthBearer`** - Bearer token authentication
- **`OAuth2`** - Base OAuth2 authentication
- **`OAuth2ClientCredentials`** - OAuth2 client credentials flow
- **`OAuth2Password`** - OAuth2 resource owner password flow

### Response Types

- **`BinaryResponse`** - Binary content responses
- **`StreamResponse`** - Streaming response handling
- **`AsyncStreamResponse`** - Async streaming responses

### Utilities

- **`RequestOptions`** - Configure individual requests
- **`QueryParams`** - Type-safe query parameter handling
- **`ApiError`** - Comprehensive API error information

## Development

### Setup

```bash
git clone <repository-url>
cd make-api-request-py
poetry install
```

### Run Tests

```bash
poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint
poetry run ruff check .

# Type checking
poetry run mypy make_api_request/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.