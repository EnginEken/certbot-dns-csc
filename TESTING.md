# Testing Guide for certbot-dns-csc

This guide provides comprehensive testing instructions for the certbot-dns-csc plugin, covering unit tests, integration tests, and manual testing procedures.

## Overview

The testing strategy includes:
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test API interactions with mocked responses
- **Manual Tests**: Test with real CSC API and Let's Encrypt staging
- **End-to-End Tests**: Full certificate request workflow

## Prerequisites

### Development Environment
```bash
# Clone and setup
git clone https://github.com/EnginEken/certbot-dns-csc.git
cd certbot-dns-csc
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

### Required Dependencies
- Python 3.6+
- pytest
- responses (for mocking HTTP requests)
- certbot
- CSC API credentials (for integration testing)

## Unit Tests

### Running Unit Tests

```bash
# Run all unit tests
python -m pytest tests/

# Run with verbose output
python -m pytest -v tests/

# Run with coverage
python -m pytest --cov=certbot_dns_csc tests/

# Run specific test file
python -m pytest tests/test_dns_csc.py

# Run specific test method
python -m pytest tests/test_dns_csc.py::CSCClientTest::test_add_txt_record
```

### Unit Test Coverage

Current test coverage includes:
- Authenticator plugin initialization
- Credentials file parsing and validation
- CSC API client functionality
- Zone detection algorithm
- TXT record creation and deletion
- Error handling scenarios
- Different API response formats

### Writing New Unit Tests

Example test structure:
```python
import unittest
from unittest.mock import Mock, patch
import responses
from certbot import errors
from certbot_dns_csc.dns_csc import _CSCClient

class TestNewFeature(unittest.TestCase):

    def setUp(self):
        self.client = _CSCClient("test_key", "test_token", "https://api.test.com")

    @responses.activate
    def test_new_functionality(self):
        # Arrange
        responses.add(responses.GET, 'https://api.test.com/endpoint',
                     json={"data": "test"}, status=200)

        # Act
        result = self.client.new_method()

        # Assert
        self.assertEqual(result, expected_value)
```

## Integration Tests

### Automated Integration Tests

The integration test script provides automated testing with real API credentials:

```bash
# Run integration test script
python test_integration.py
```

This script will:
1. Check plugin registration
2. Validate credentials format
3. Test zone detection
4. Optionally run full certificate request (staging)

### Manual Integration Testing

#### Step 1: Prepare Credentials

```bash
# Copy example credentials file
cp csc.ini.example test_csc.ini

# Edit with real credentials
# dns_csc_api_key = your_real_api_key
# dns_csc_bearer_token = your_real_bearer_token

# Set secure permissions
chmod 600 test_csc.ini
```

#### Step 2: Test Plugin Registration

```bash
# Verify plugin is installed
certbot plugins | grep dns-csc
```

Expected output should include:
```
dns-csc (certbot-dns-csc:dns-csc)
```

#### Step 3: Test Zone Detection

```python
# Quick zone test
python3 -c "
from certbot_dns_csc.dns_csc import _CSCClient
import configparser

config = configparser.ConfigParser()
config.read('test_csc.ini')
api_key = config.get('DEFAULT', 'dns_csc_api_key')
token = config.get('DEFAULT', 'dns_csc_bearer_token')

client = _CSCClient(api_key, token, 'https://apis.cscglobal.com/dbs/api/v2')
zones = client._get_zones()
print(f'Found {len(zones)} zones')
for zone in zones[:3]:
    print(f'  - {zone.get(\"name\", \"unknown\")}')
"
```

#### Step 4: Test with Staging Server

```bash
# Test certificate request (staging)
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials test_csc.ini \
  --dns-csc-propagation-seconds 30 \
  --server https://acme-staging-v02.api.letsencrypt.org/directory \
  --dry-run \
  --non-interactive \
  --agree-tos \
  --email test@example.com \
  -d test.yourdomain.com
```

#### Step 5: Test Certificate Renewal

```bash
# Test renewal (dry run)
certbot renew --dry-run
```

## Manual Testing Procedures

### Test Case 1: Basic Certificate Request

**Objective**: Verify basic certificate issuance functionality

**Prerequisites**:
- Valid CSC credentials
- Domain managed in CSC
- DNS propagation time configured

**Steps**:
1. Prepare credentials file
2. Run certificate request command
3. Verify TXT record creation in DNS
4. Confirm certificate issuance
5. Verify TXT record cleanup

**Expected Results**:
- TXT record appears in DNS during challenge
- Certificate files created in `/etc/letsencrypt/live/`
- TXT record removed after completion
- No errors in logs

### Test Case 2: Multiple Domain Certificate

**Objective**: Test certificate with multiple domains

**Steps**:
```bash
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials /path/to/csc.ini \
  --server https://acme-staging-v02.api.letsencrypt.org/directory \
  -d example.com \
  -d www.example.com \
  -d api.example.com
```

**Expected Results**:
- TXT records created for each domain
- Single certificate covering all domains
- All records cleaned up

### Test Case 3: Wildcard Certificate

**Objective**: Test wildcard certificate issuance

**Steps**:
```bash
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials /path/to/csc.ini \
  --server https://acme-staging-v02.api.letsencrypt.org/directory \
  -d "*.example.com" \
  -d example.com
```

**Expected Results**:
- TXT record created for `_acme-challenge.example.com`
- Wildcard certificate issued
- Certificate valid for subdomains

### Test Case 4: Error Handling

**Objective**: Test error scenarios

**Test Scenarios**:
1. Invalid credentials
2. Non-existent domain
3. Network connectivity issues
4. API rate limiting
5. DNS propagation timeout

**Steps for Invalid Credentials**:
```bash
# Create invalid credentials file
echo "dns_csc_api_key = invalid_key" > invalid_csc.ini
echo "dns_csc_bearer_token = invalid_token" >> invalid_csc.ini

# Test with invalid credentials
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials invalid_csc.ini \
  --server https://acme-staging-v02.api.letsencrypt.org/directory \
  -d test.example.com
```

**Expected Results**:
- Clear error message about authentication
- No partial DNS records created
- Graceful failure handling

## Performance Testing

### DNS Propagation Testing

**Test different propagation times**:
```bash
# Test with minimal propagation time
certbot certonly --authenticator dns-csc --dns-csc-propagation-seconds 5 -d test.domain.com

# Test with extended propagation time
certbot certonly --authenticator dns-csc --dns-csc-propagation-seconds 120 -d test.domain.com
```

### Load Testing

**Test multiple concurrent requests**:
```bash
# Script to test multiple domains
for domain in test1.example.com test2.example.com test3.example.com; do
  certbot certonly \
    --authenticator dns-csc \
    --dns-csc-credentials /path/to/csc.ini \
    --server https://acme-staging-v02.api.letsencrypt.org/directory \
    -d $domain &
done
wait
```

## Automated Testing with CI/CD

### GitHub Actions Testing

The project includes GitHub Actions workflow (`.github/workflows/ci.yml`) that:
- Runs tests on multiple Python versions
- Performs linting and formatting checks
- Builds and validates the package
- Generates coverage reports

### Local CI Simulation

```bash
# Run the same tests as CI
tox

# Test specific Python version
tox -e py39

# Run linting
tox -e flake8
tox -e pylint

# Generate coverage report
tox -e coverage
```

## Test Data and Fixtures

### Mock API Responses

The test suite includes fixtures for common API responses:

```python
# Example zone response
MOCK_ZONES_RESPONSE = [
    {"name": "example.com", "id": "123"},
    {"name": "subdomain.example.com", "id": "456"}
]

# Example successful edit response
MOCK_EDIT_SUCCESS = {"success": True, "message": "Record created"}
```

### Test Domains

For testing, use domains that:
- Are managed in your CSC account
- Won't affect production systems
- Have appropriate DNS delegation

## Troubleshooting Tests

### Common Test Failures

1. **Import Errors**:
   ```bash
   # Verify installation
   pip list | grep certbot-dns-csc
   # Reinstall if needed
   pip install -e .
   ```

2. **API Authentication Failures**:
   - Check credentials file format
   - Verify API key and token validity
   - Test with CSC API directly using curl

3. **DNS Propagation Issues**:
   ```bash
   # Check DNS propagation manually
   dig TXT _acme-challenge.example.com
   # Try different DNS servers
   dig @8.8.8.8 TXT _acme-challenge.example.com
   ```

4. **Network Connectivity**:
   ```bash
   # Test API connectivity
   curl -H "apikey: YOUR_API_KEY" \
        -H "Authorization: Bearer YOUR_TOKEN" \
        https://apis.cscglobal.com/dbs/api/v2/zones
   ```

### Debug Mode

Enable debug logging for detailed troubleshooting:
```bash
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials /path/to/csc.ini \
  --debug \
  -d example.com
```

### Log Analysis

Check certbot logs for detailed information:
```bash
# View recent logs
tail -f /var/log/letsencrypt/letsencrypt.log

# Search for specific errors
grep -i error /var/log/letsencrypt/letsencrypt.log
```

## Test Environment Cleanup

### After Testing

1. **Remove test certificates**:
   ```bash
   certbot delete --cert-name test.example.com
   ```

2. **Clean up credentials**:
   ```bash
   rm test_csc.ini
   ```

3. **Remove test artifacts**:
   ```bash
   make clean
   ```

## Continuous Testing Strategy

### Pre-commit Testing

```bash
# Run before each commit
make check  # Runs lint + test
```

### Release Testing

Before each release:
1. Run full test suite: `tox`
2. Execute integration tests: `python test_integration.py`
3. Manual testing with staging server
4. Performance testing with multiple domains
5. Documentation review and testing

### Monitoring

Set up monitoring for:
- API response times
- Success/failure rates
- DNS propagation times
- Certificate renewal success

This comprehensive testing approach ensures the plugin works reliably across different environments and use cases.
