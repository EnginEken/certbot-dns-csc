# Certbot DNS CSC Plugin

A [Certbot](https://certbot.eff.org/) plugin for automating the process of completing a `dns-01` challenge by creating, and subsequently removing, TXT records using the [CSC Global Domain Manager API](https://www.cscglobal.com/cscglobal/docs/dbs/domainmanager/api-v2/).

This plugin enables automatic SSL certificate generation and renewal for domains managed by CSC Global Domain Manager.

## Features

- **Automatic zone detection**: Automatically determines the correct DNS zone for your domain
- **Secure credential handling**: Stores API credentials in a separate configuration file
- **Configurable propagation delay**: Allows customization of DNS propagation wait time
- **Zone edit conflict handling**: Automatically retries when CSC zone edits are in progress
- **Full ACME challenge support**: Handles both certificate issuance and renewal
- **Error handling**: Comprehensive error reporting and logging
- **Testing support**: Includes comprehensive test suite

## Installation

### From PyPI (Recommended)

```bash
pip install certbot-dns-csc
```

### From Source

```bash
git clone https://github.com/EnginEken/certbot-dns-csc.git
cd certbot-dns-csc
pip install .
```

### Development Installation

```bash
git clone https://github.com/EnginEken/certbot-dns-csc.git
cd certbot-dns-csc
pip install -e .
```

## Prerequisites

1. **CSC Global Domain Manager Account**: You need to enable API feature for your account with CSC Global Domain Manager by contacting with your service specialist
2. **API Credentials**: Obtain your API key and generate Bearer token from your CSC account
3. **API Permissions**: You need at least `GET /zones` and `POST /zones/edits` permissions for the zones that you will use this plugin
3. **Domain Management**: Ensure your domains are managed through CSC Global Domain Manager
4. **Certbot**: This plugin requires Certbot to be installed

## Configuration

### Credentials File

Create a credentials file (e.g., `/etc/letsencrypt/csc.ini`) with your CSC API credentials:

```ini
# CSC Global Domain Manager API credentials used by Certbot
dns_csc_api_key = your_api_key_here
dns_csc_bearer_token = your_bearer_token_here

# Optional: Custom API base URL (defaults to https://apis.cscglobal.com/dbs/api/v2)
# dns_csc_base_url = https://apis.cscglobal.com/dbs/api/v2
```

**Important Security Notes:**
- Set restrictive permissions on the credentials file: `chmod 600 /etc/letsencrypt/csc.ini`
- Never commit credentials to version control
- Store the file in a secure location accessible only to the certbot process
- Consider using environment variables or secret management systems in production

### Obtaining CSC API Credentials

1. Log in to your CSC Global Domain Manager account
2. Navigate to the API section in your account settings
3. Generate or retrieve your API key
4. Generate or retrieve your Bearer token
5. Add these credentials to your configuration file

## Usage

### Basic Certificate Request

```bash
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials /etc/letsencrypt/csc.ini \
  -d example.com
```

### Multiple Domains

```bash
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials /etc/letsencrypt/csc.ini \
  -d example.com \
  -d www.example.com \
  -d api.example.com
```

### Custom Propagation Time

Default propagation time is 360 seconds for this package because usually the record in CSC should start propagating on the internet from the 6th minute onwards but in some cases, can take longer to upto 15 minute onwards. It's suggested to choose more than 360 seconds.

```bash
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials /etc/letsencrypt/csc.ini \
  --dns-csc-propagation-seconds 60 \
  -d example.com
```

### Zone Edit Conflict Retry Mechanism

With CSC API, it's not possible to add/delete records if the propagation is in progress for a domain. If you try to add/delete/edit the zone CSC API will return below example response:

```sh
HTTP/1.1 400
Content-Type: application/json;charset=UTF-8
Content-Length: 158
Date: Fri, 06 Jun 2025 10:33:42 GMT
Connection: close
Server: Layer7-API-Gateway

{"code":"OPEN_ZONE_EDITS","description":"Existing zone edits need to be resolved before publishing a new edit","value":"<zone_edit_uuid>"}
```

This plugin has avoid mechanism for this situation with below details:

- **Default behavior**: Retries up to 10 times with exponential backoff
- **Wait times**: Starts at 30 seconds, increases to maximum 5 minutes
- **Total time**: May take up to 15 minutes in worst case scenarios

This is normal when multiple certificate requests are made simultaneously. Because you won't be able to send another `POST` request during this time which means certbot will fail. This problem is resolved with this feature.

Example logs:

```sh
2025-06-06 12:16:33,757:DEBUG:acme.client:Storing nonce: Fn04lWFjB-i-FEqtx7kghthfPiMe0vdndvOOr1G9uRh873svDFiwB0iasfafj5Y
2025-06-06 12:16:33,758:INFO:certbot._internal.auth_handler:Performing the following challenges:
2025-06-06 12:16:33,758:INFO:certbot._internal.auth_handler:dns-01 challenge for test.example.com
2025-06-06 12:16:33,764:DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): apis.cscglobal.com:443
2025-06-06 12:16:34,479:DEBUG:urllib3.connectionpool:https://apis.cscglobal.com:443 "GET /dbs/api/v2/zones HTTP/1.1" 200 2055
2025-06-06 12:16:34,481:DEBUG:certbot_dns_csc.csc_client:Retrieved 1 zones from CSC API
2025-06-06 12:16:34,787:DEBUG:urllib3.connectionpool:https://apis.cscglobal.com:443 "POST /dbs/api/v2/zones/edits HTTP/1.1" 400 160
2025-06-06 12:16:34,789:INFO:certbot_dns_csc.csc_client:Zone edit in progress (attempt 1/11). Waiting 32 seconds before retry. Edit UUID: <edit_uuid>
2025-06-06 12:17:06,797:DEBUG:urllib3.connectionpool:Resetting dropped connection: apis.cscglobal.com
2025-06-06 12:17:07,233:DEBUG:urllib3.connectionpool:https://apis.cscglobal.com:443 "POST /dbs/api/v2/zones/edits HTTP/1.1" 400 160
2025-06-06 12:17:07,235:INFO:certbot_dns_csc.csc_client:Zone edit in progress (attempt 2/11). Waiting 50 seconds before retry. Edit UUID: <edit_uuid>
2025-06-06 12:20:49,366:DEBUG:urllib3.connectionpool:Resetting dropped connection: apis.cscglobal.com
2025-06-06 12:20:49,991:DEBUG:urllib3.connectionpool:https://apis.cscglobal.com:443 "POST /dbs/api/v2/zones/edits HTTP/1.1" 201 193
2025-06-06 12:20:49,992:DEBUG:certbot_dns_csc.csc_client:Successfully added TXT record for _acme-challenge.test.example.com in zone example.com
```

### Wildcard Certificates

```bash
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials /etc/letsencrypt/csc.ini \
  -d "*.example.com" \
  -d example.com
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dns-csc-credentials` | Path to CSC credentials INI file | `/etc/letsencrypt/csc.ini` |
| `--dns-csc-propagation-seconds` | Seconds to wait for DNS propagation | `360` |

## Certificate Renewal

Certificates obtained using this plugin will automatically renew using the same DNS-01 challenge. Ensure your credentials file remains accessible and valid.

To test renewal:

```bash
certbot renew --dry-run
```

## Automatic Renewal Setup

Set up automatic renewal using cron:

```bash
# Edit crontab
crontab -e

# Add renewal check twice daily
0 12 * * * /usr/bin/certbot renew --quiet
```

Or use systemd timer (on systemd-enabled systems):

```bash
# Enable certbot renewal timer
systemctl enable certbot.timer
systemctl start certbot.timer
```

## Testing

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
python -m pytest tests/

# Run tests with coverage
python -m pytest --cov=certbot_dns_csc tests/
```

### Manual Testing

1. **Test credentials setup:**
   ```bash
   certbot plugins
   ```
   Verify that `dns-csc` appears in the list.

2. **Test with staging server:**
   ```bash
   certbot certonly \
     --authenticator dns-csc \
     --dns-csc-credentials /path/to/csc.ini \
     --server https://acme-staging-v02.api.letsencrypt.org/directory \
     -d test.yourdomain.com
   ```

3. **Dry run renewal test:**
   ```bash
   certbot renew --dry-run
   ```

## API Integration Details

This plugin integrates with the CSC Global Domain Manager API using the following endpoints:

- **GET /zones**: Retrieves available DNS zones
- **POST /zones/edits**: Creates and deletes TXT records

### Zone Detection Algorithm

The plugin automatically determines the appropriate DNS zone for your domain:

1. Retrieves all available zones from your CSC account
2. Finds the most specific zone that matches your domain
3. For example, if you have zones for `example.com` and `api.example.com`, requesting a certificate for `test.api.example.com` will use the `api.example.com` zone

### Record Management

- **Creation**: TXT records are created with the prefix `_acme-challenge`
- **TTL**: Records are created with a TTL of 300 seconds
- **Cleanup**: Records are automatically removed after validation
- **Error Handling**: Failed operations are logged and reported

## Troubleshooting

### Common Issues

1. **Plugin not found:**
   ```
   certbot: error: unrecognized arguments: --dns-csc
   ```
   - Ensure the plugin is installed: `pip list | grep certbot-dns-csc`
   - Verify plugin registration: `certbot plugins`

2. **Credentials file errors:**
   ```
   PluginError: The credentials file could not be found
   ```
   - Check file path and permissions
   - Ensure file contains required credentials

3. **API authentication errors:**
   ```
   PluginError: Error adding TXT record: 401 Client Error
   ```
   - Verify API key and Bearer token are correct
   - Check token expiration

4. **Zone not found:**
   ```
   PluginError: Unable to determine zone for domain
   ```
   - Ensure domain is managed in your CSC account
   - Verify zone is active and accessible via API

5. **DNS propagation timeout:**
   - Increase `--dns-csc-propagation-seconds` value
   - Check DNS propagation manually: `dig TXT _acme-challenge.yourdomain.com`

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
certbot certonly \
  --authenticator dns-csc \
  --dns-csc-credentials /etc/letsencrypt/csc.ini \
  --debug \
  -d example.com
```

### Checking DNS Propagation

Manually verify TXT record creation:

```bash
# Check DNS propagation
dig TXT _acme-challenge.example.com

# Check from different DNS servers
dig @8.8.8.8 TXT _acme-challenge.example.com
dig @1.1.1.1 TXT _acme-challenge.example.com
```

## Security Considerations

- **Credential Protection**: Store credentials securely with appropriate file permissions
- **Network Security**: Ensure secure communication with CSC API (HTTPS)
- **Access Control**: Limit access to the credentials file and certbot execution
- **Audit Logging**: Monitor certificate operations and API usage
- **Key Rotation**: Regularly rotate API credentials

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `python -m pytest`
6. Commit your changes: `git commit -am 'Add feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/EnginEken/certbot-dns-csc.git
cd certbot-dns-csc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests
python -m pytest
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/EnginEken/certbot-dns-csc/issues)
- **Documentation**: Additional documentation available in the `/docs` directory
- **Community**: Join discussions in the project's GitHub Discussions

## Changelog

### Version 1.0.1 - 2025-06-05
- Automatic retry mechanism for CSC zone edit conflicts (OPEN_ZONE_EDITS)
- Exponential backoff with jitter for retry attempts
- Enhanced logging for retry operations

### Version 1.0.0
- Initial release
- Support for CSC Global Domain Manager API
- Automatic zone detection
- Comprehensive test suite
- Full documentation

## Related Projects

- [Certbot](https://github.com/certbot/certbot) - ACME client
- [ACME Protocol](https://tools.ietf.org/html/rfc8555) - Automatic Certificate Management Environment

## Acknowledgments

- Thanks to the Certbot team for the excellent plugin architecture
- CSC Global for providing the Domain Manager API
- The Let's Encrypt project for making SSL certificates accessible
