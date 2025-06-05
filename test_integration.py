#!/usr/bin/env python3
"""
Integration test script for certbot-dns-csc plugin.
This script can be used to test the plugin with real CSC API credentials.
"""

import os
import subprocess
import sys
import tempfile


def create_test_credentials():
    """Create a test credentials file with user input."""
    api_key = input("Enter your CSC API key: ").strip()
    bearer_token = input("Enter your CSC Bearer token: ").strip()

    if not api_key or not bearer_token:
        print("Error: Both API key and Bearer token are required")
        return None

    # Create temporary credentials file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        f.write(f"dns_csc_api_key = {api_key}\n")
        f.write(f"dns_csc_bearer_token = {bearer_token}\n")
        return f.name


def test_plugin_registration():
    """Test if the plugin is properly registered with certbot."""
    print("Testing plugin registration...")
    try:
        result = subprocess.run(
            ["certbot", "plugins"], capture_output=True, text=True, check=True
        )
        if "dns-csc" in result.stdout:
            print("✓ Plugin is properly registered")
            return True
        else:
            print("✗ Plugin not found in certbot plugins list")
            return False
    except subprocess.CalledProcessError as e:
        print(f"✗ Error checking plugins: {e}")
        return False
    except FileNotFoundError:
        print("✗ Certbot not found. Please install certbot first.")
        return False


def test_credentials_validation(creds_file):
    """Test credentials validation by attempting a dry run."""
    domain = input("Enter a test domain (managed by your CSC account): ").strip()

    if not domain:
        print("Error: Domain is required for testing")
        return False

    print(f"Testing credentials with domain: {domain}")
    print("Running dry-run certificate request...")

    # Create temporary directories for certbot
    import tempfile

    temp_dir = tempfile.mkdtemp()

    cmd = [
        "certbot",
        "certonly",
        "--authenticator",
        "dns-csc",
        "--dns-csc-credentials",
        creds_file,
        "--dns-csc-propagation-seconds",
        "360",
        "--server",
        "https://acme-staging-v02.api.letsencrypt.org/directory",
        "--dry-run",
        "--non-interactive",
        "--agree-tos",
        "--email",
        "test@example.com",
        "--config-dir",
        f"{temp_dir}/config",
        "--work-dir",
        f"{temp_dir}/work",
        "--logs-dir",
        f"{temp_dir}/logs",
        "-d",
        domain,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")

        if result.returncode == 0:
            print("✓ Dry run successful!")
            print("✓ Credentials are valid and plugin is working")
            return True
        else:
            print("✗ Dry run failed!")
            return False

    except subprocess.CalledProcessError as e:
        print(f"✗ Dry run failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    finally:
        # Cleanup temp directory
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


def test_zone_detection(creds_file):
    """Test zone detection functionality."""
    print("\nTesting zone detection...")

    # Create a simple test script
    test_script = """
import sys
sys.path.insert(0, ".")
print("Starting zone detection test...")
try:
    from certbot_dns_csc.csc_client import CSCClient
    print("Successfully imported CSCClient")

    client = CSCClient("{api_key}", "{bearer_token}", "https://apis.cscglobal.com/dbs/api/v2")
    print("Successfully created client")

    zones = client._get_zones()
    print(f"API call successful. Found {{len(zones)}} zones")

    for zone in zones[:5]:  # Show first 5 zones
        print(f"  - {{zone.get('zoneName', 'Unknown')}}")
    if len(zones) > 5:
        print(f"  ... and {{len(zones) - 5}} more")

except Exception as e:
    print(f"Error: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

    # Read credentials
    try:
        with open(creds_file, "r") as f:
            content = f.read()
            api_key = None
            bearer_token = None
            for line in content.split("\n"):
                if line.strip().startswith("dns_csc_api_key"):
                    api_key = line.split("=")[1].strip()
                elif line.strip().startswith("dns_csc_bearer_token"):
                    bearer_token = line.split("=")[1].strip()

        if not api_key or not bearer_token:
            print("✗ Could not parse credentials from file")
            return False

        # Write and execute test script
        test_script = test_script.format(api_key=api_key, bearer_token=bearer_token)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_script)
            test_file = f.name

        print(f"Executing test script: {test_file}")
        result = subprocess.run(
            [sys.executable, test_file], capture_output=True, text=True
        )

        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")

        if result.returncode == 0:
            print("✓ Zone detection successful!")
            return True
        else:
            print("✗ Zone detection failed!")
            return False

        # Cleanup
        os.unlink(test_file)

    except Exception as e:
        print(f"✗ Zone detection failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main integration test function."""
    print("=== Certbot DNS CSC Plugin Integration Test ===\n")

    # Check if plugin is installed
    if not test_plugin_registration():
        print("\nPlease install the plugin first:")
        print("  pip install -e .")
        return False

    # Create test credentials
    print("\nCreating test credentials...")
    creds_file = create_test_credentials()
    if not creds_file:
        return False

    try:
        # Set restrictive permissions
        os.chmod(creds_file, 0o600)

        # Test zone detection
        if not test_zone_detection(creds_file):
            return False

        # Test full integration
        print("\n" + "=" * 50)
        print("IMPORTANT: The next test will attempt to create a real DNS record")
        print("using the Let's Encrypt staging server. This is safe but will")
        print("temporarily create a TXT record in your DNS zone.")
        print("=" * 50)

        proceed = input("\nProceed with full integration test? (y/N): ").strip().lower()
        if proceed == "y":
            if test_credentials_validation(creds_file):
                print("\n✓ All tests passed! Plugin is working correctly.")
                return True
        else:
            print("Skipping full integration test.")
            print("✓ Basic tests passed! Plugin should work correctly.")
            return True

    finally:
        # Cleanup credentials file
        if os.path.exists(creds_file):
            os.unlink(creds_file)

    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
