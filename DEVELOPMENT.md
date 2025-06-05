# Development Guide

This guide covers development setup, testing, and contribution guidelines for the certbot-dns-csc plugin.

## Development Environment Setup

### Prerequisites

- Python 3.6 or higher
- Git
- Virtual environment tool (uv, venv, virtualenv, or conda)

### Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/EnginEken/certbot-dns-csc.git
   cd certbot-dns-csc
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e .[dev]
   ```

4. **Verify installation:**
   ```bash
   certbot plugins
   # Should show dns-csc in the list
   ```

## Project Structure

```
certbot-dns-csc/
├── certbot_dns_csc/          # Main package
│   ├── __init__.py           # Package documentation and exports
│   ├── csc_client.py         # CSC API Client class implementation
│   └── dns_csc.py           # Main plugin implementation
├── tests/                   # Test suite
│   ├── __init__.py
│   └── test_dns_csc.py     # Unit tests
├── setup.py                # Package configuration
├── csc.ini.example         # Example credentials file
├── requirements.txt        # Runtime dependencies
├── pytest.ini            # Test configuration
├── tox.ini               # Multi-version testing
├── Makefile              # Development tasks
└── README.md             # User documentation
```

## Development Workflow

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests:**
   ```bash
   make test
   ```

4. **Run linting:**
   ```bash
   make lint
   ```

5. **Format code:**
   ```bash
   make format
   ```

### Code Style Guidelines

- **PEP 8 compliance:** Follow Python PEP 8 style guidelines
- **Line length:** Maximum 120 characters per line
- **Imports:** Group imports (standard library, third-party, local)
- **Docstrings:** Use Google-style docstrings for all public methods
- **Type hints:** Use type hints where appropriate

### Example Code Style

```python
"""Module docstring explaining the purpose."""
import logging
from typing import Optional

import requests
from certbot import errors

logger = logging.getLogger(__name__)


class ExampleClass:
    """Example class with proper documentation.

    Args:
        param1: Description of parameter.
        param2: Description of parameter.
    """

    def __init__(self, param1: str, param2: Optional[str] = None):
        self.param1 = param1
        self.param2 = param2

    def example_method(self, input_value: str) -> str:
        """Example method with proper documentation.

        Args:
            input_value: Description of input.

        Returns:
            Description of return value.

        Raises:
            ValueError: When input is invalid.
        """
        if not input_value:
            raise ValueError("Input value cannot be empty")

        return f"Processed: {input_value}"
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run tests with coverage
make test-coverage

# Run tests for specific Python versions
tox
```

### Writing Tests

1. **Unit tests:** Test individual functions and methods
2. **Integration tests:** Test API interactions with mocked responses
3. **Test naming:** Use descriptive test names starting with `test_`
4. **Test structure:** Follow Arrange-Act-Assert pattern

### Example Test

```python
def test_add_txt_record_success(self):
    """Test successful TXT record creation."""
    # Arrange
    client = _CSCClient("api_key", "token", "https://api.test.com")
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, 'https://api.test.com/zones',
                json=[{"name": "example.com"}], status=200)
        rsps.add(responses.POST, 'https://api.test.com/zones/edits',
                json={"success": True}, status=200)

        # Act
        client.add_txt_record("test.example.com", "_acme-challenge", "value", 300)

        # Assert
        assert len(rsps.calls) == 2
        request_data = json.loads(rsps.calls[1].request.body)
        assert request_data["zoneName"] == "example.com"
```

### Test Coverage

Aim for high test coverage:
- Minimum 80% code coverage
- 100% coverage for critical paths
- Test both success and error scenarios

## Integration Testing

### Manual Integration Testing

1. **Set up test credentials:**
   ```bash
   cp csc.ini.example test_csc.ini
   # Edit test_csc.ini with real credentials
   chmod 600 test_csc.ini
   ```

2. **Run integration test:**
   ```bash
   python test_integration.py
   ```

3. **Test with staging server:**
   ```bash
   certbot certonly \
     --dns-csc \
     --dns-csc-credentials test_csc.ini \
     --server https://acme-staging-v02.api.letsencrypt.org/directory \
     --dry-run \
     -d test.yourdomain.com
   ```

## Debugging

### Enable Debug Logging

```bash
certbot certonly \
  --dns-csc \
  --dns-csc-credentials /path/to/csc.ini \
  --debug \
  -d example.com
```

### Common Debug Points

1. **Credential loading:** Check if credentials are properly parsed
2. **Zone detection:** Verify zones are retrieved and matched correctly
3. **API requests:** Check request/response data
4. **DNS propagation:** Verify TXT records are created and visible

### Debugging Tools

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints in code
logger.debug(f"Zone found: {zone_name}")
logger.debug(f"API request: {request_data}")
```

## Release Process

### Version Management

1. Update version in `setup.py`
2. Update `CHANGELOG.md` with new features/fixes
3. Create git tag: `git tag v1.0.1`
4. Push tag: `git push origin v1.0.1`

### Building and Publishing

```bash
# Build package
make build

# Test upload to TestPyPI
make upload-test

# Upload to PyPI
make upload
```

### Pre-release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Version number incremented
- [ ] Changelog updated
- [ ] Manual testing completed
- [ ] Integration tests passing

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation
7. Submit pull request

### Pull Request Template

```
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests completed
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
```

## Troubleshooting

### Common Development Issues

1. **Plugin not found:**
   - Ensure installation with `-e` flag
   - Check virtual environment activation

2. **Test failures:**
   - Check dependency versions
   - Verify test data and mocks

3. **Import errors:**
   - Check Python path
   - Verify package structure

4. **Linting errors:**
   - Run `make format` to auto-fix
   - Check line lengths and imports

### Getting Help

- Check existing issues on GitHub
- Review documentation and examples
- Ask questions in GitHub Discussions
- Contact maintainers for complex issues

## Performance Considerations

### API Rate Limiting

- Implement backoff strategies for API calls
- Cache zone information when possible
- Minimize API requests during operations

### DNS Propagation

- Allow configurable propagation delays
- Consider regional DNS differences
- Implement verification before proceeding

## Security Guidelines

### Credential Handling

- Never log sensitive information
- Use secure file permissions (600)
- Validate input parameters
- Implement proper error handling

### API Security

- Use HTTPS for all API calls
- Validate SSL certificates
- Implement request timeouts
- Handle authentication errors gracefully

## Documentation

### Updating Documentation

1. **README.md:** User-facing documentation
2. **DEVELOPMENT.md:** This file
3. **Docstrings:** In-code documentation
4. **Comments:** Explain complex logic

### Documentation Style

- Use clear, concise language
- Provide practical examples
- Include troubleshooting sections
- Keep documentation up-to-date with code changes
