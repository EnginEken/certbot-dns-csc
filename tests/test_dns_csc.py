"""Tests for certbot_dns_csc.dns_csc"""
import os
import unittest
from unittest import mock
from unittest.mock import Mock, patch

import responses
from certbot import errors
from certbot.plugins import dns_test_common
from certbot.plugins.dns_test_common import DOMAIN
from certbot.tests import util as test_util

from certbot_dns_csc.csc_client import CSCClient
from certbot_dns_csc.dns_csc import Authenticator


class AuthenticatorTest(
    test_util.TempDirTestCase, dns_test_common.BaseAuthenticatorTest
):
    def setUp(self):
        super(AuthenticatorTest, self).setUp()

        path = os.path.join(self.tempdir, "file.ini")
        dns_test_common.write(
            {"dns_csc_api_key": "foo", "dns_csc_bearer_token": "bar"}, path
        )

        self.config = mock.MagicMock(
            dns_csc_credentials=path, dns_csc_propagation_seconds=10
        )  # don't wait during tests

        self.auth = Authenticator(self.config, "dns-csc")

        self.mock_client = mock.MagicMock()
        # _get_csc_client | pylint: disable=protected-access
        self.auth._get_csc_client = mock.MagicMock(return_value=self.mock_client)

    def test_perform(self):
        with mock.patch("certbot.display.util.notify"):
            self.auth.perform([self.achall])

        expected = [
            mock.call.add_txt_record(
                DOMAIN, "_acme-challenge." + DOMAIN, mock.ANY, mock.ANY
            )
        ]
        self.assertEqual(expected, self.mock_client.mock_calls)

    def test_cleanup(self):
        # _attempt_cleanup | pylint: disable=protected-access
        self.auth._attempt_cleanup = True
        self.auth.cleanup([self.achall])

        expected = [
            mock.call.del_txt_record(DOMAIN, "_acme-challenge." + DOMAIN, mock.ANY)
        ]
        self.assertEqual(expected, self.mock_client.mock_calls)

    def test_credentials_file_not_found(self):
        self.config.dns_csc_credentials = "/not/found"
        self.assertRaises(errors.PluginError, self.auth._setup_credentials)

    def test_credentials_file_missing_api_key(self):
        dns_test_common.write(
            {"dns_csc_bearer_token": "bar"}, self.config.dns_csc_credentials
        )
        self.assertRaises(errors.PluginError, self.auth._setup_credentials)

    def test_credentials_file_missing_bearer_token(self):
        dns_test_common.write(
            {"dns_csc_api_key": "foo"}, self.config.dns_csc_credentials
        )
        self.assertRaises(errors.PluginError, self.auth._setup_credentials)


class CSCClientTest(unittest.TestCase):
    def setUp(self):
        self.client = CSCClient("api_key", "bearer_token", "https://api.test.com")

    @responses.activate
    def test_add_txt_record(self):
        responses.add(
            responses.GET,
            "https://api.test.com/zones",
            json=[{"zoneName": "example.com", "id": "123"}],
            status=200,
        )
        responses.add(
            responses.POST,
            "https://api.test.com/zones/edits",
            json={"success": True},
            status=200,
        )

        # Clear cache to ensure zones are fetched
        self.client._zones_cache = None

        self.client.add_txt_record(
            "test.example.com", "_acme-challenge.test.example.com", "validation", 300
        )

        # Check that the correct API calls were made
        self.assertEqual(len(responses.calls), 2)

        # Check the zones call
        zones_call = responses.calls[0]
        self.assertEqual(zones_call.request.url, "https://api.test.com/zones")

        # Check the edits call
        edit_call = responses.calls[1]
        self.assertEqual(edit_call.request.url, "https://api.test.com/zones/edits")

        # Parse the request body
        import json

        request_body = edit_call.request.body
        assert request_body is not None, "Request body should not be None"
        request_data = json.loads(request_body)

        expected_data = {
            "zoneName": "example.com",
            "edits": [
                {
                    "recordType": "TXT",
                    "action": "ADD",
                    "newKey": "_acme-challenge.test",
                    "newValue": "validation",
                    "newTtl": 300,
                    "comments": "ACME challenge for test.example.com",
                }
            ],
        }

        self.assertEqual(request_data, expected_data)

    @responses.activate
    def test_del_txt_record(self):
        responses.add(
            responses.GET,
            "https://api.test.com/zones",
            json=[{"zoneName": "example.com", "id": "123"}],
            status=200,
        )
        responses.add(
            responses.POST,
            "https://api.test.com/zones/edits",
            json={"success": True},
            status=200,
        )

        # Clear cache to ensure zones are fetched
        self.client._zones_cache = None

        self.client.del_txt_record(
            "test.example.com", "_acme-challenge.test.example.com", "validation"
        )

        # Check that the correct API calls were made
        self.assertEqual(len(responses.calls), 2)

        # Check the edits call
        edit_call = responses.calls[1]
        self.assertEqual(edit_call.request.url, "https://api.test.com/zones/edits")

        # Parse the request body
        import json

        request_body = edit_call.request.body
        assert request_body is not None, "Request body should not be None"
        request_data = json.loads(request_body)

        expected_data = {
            "zoneName": "example.com",
            "edits": [
                {
                    "recordType": "TXT",
                    "action": "PURGE",
                    "currentKey": "_acme-challenge.test",
                    "currentValue": "validation",
                }
            ],
        }

        self.assertEqual(request_data, expected_data)

    @responses.activate
    def test_add_txt_record_api_error(self):
        responses.add(
            responses.GET,
            "https://api.test.com/zones",
            json=[{"zoneName": "example.com", "id": "123"}],
            status=200,
        )
        responses.add(responses.POST, "https://api.test.com/zones/edits", status=500)

        # Clear cache to ensure zones are fetched
        self.client._zones_cache = None

        with self.assertRaises(errors.PluginError):
            self.client.add_txt_record(
                "test.example.com",
                "_acme-challenge.test.example.com",
                "validation",
                300,
            )

    @responses.activate
    def test_del_txt_record_api_error(self):
        responses.add(
            responses.GET,
            "https://api.test.com/zones",
            json=[{"zoneName": "example.com", "id": "123"}],
            status=200,
        )
        responses.add(responses.POST, "https://api.test.com/zones/edits", status=500)

        # Clear cache to ensure zones are fetched
        self.client._zones_cache = None

        with self.assertRaises(errors.PluginError):
            self.client.del_txt_record(
                "test.example.com", "_acme-challenge.test.example.com", "validation"
            )

    @responses.activate
    def test_find_zone_for_domain(self):
        zones = [
            {"zoneName": "example.com", "id": "123"},
            {"zoneName": "sub.example.com", "id": "456"},
            {"zoneName": "other.com", "id": "789"},
        ]
        responses.add(
            responses.GET, "https://api.test.com/zones", json=zones, status=200
        )

        # Clear cache to ensure zones are fetched
        self.client._zones_cache = None

        # Test exact match
        zone = self.client._find_zone_for_domain("example.com")
        self.assertEqual(zone, "example.com")

        # Test subdomain match (should find most specific)
        zone = self.client._find_zone_for_domain("test.sub.example.com")
        self.assertEqual(zone, "sub.example.com")

        # Test subdomain match (should find parent zone)
        zone = self.client._find_zone_for_domain("www.example.com")
        self.assertEqual(zone, "example.com")

        # Test no match
        zone = self.client._find_zone_for_domain("notfound.org")
        self.assertIsNone(zone)

    @responses.activate
    def test_get_zones_error(self):
        responses.add(responses.GET, "https://api.test.com/zones", status=500)

        # Clear cache to ensure zones are fetched
        self.client._zones_cache = None

        with self.assertRaises(errors.PluginError):
            self.client._get_zones()

    @responses.activate
    def test_get_zones_different_response_formats(self):
        # Test with direct list response
        zones_list = [{"zoneName": "example.com", "id": "123"}]
        responses.add(
            responses.GET, "https://api.test.com/zones", json=zones_list, status=200
        )

        self.client._zones_cache = None
        zones = self.client._get_zones()
        self.assertEqual(zones, zones_list)

        # Test with zones key
        responses.reset()
        zones_dict = {"zones": [{"zoneName": "example.com", "id": "123"}]}
        responses.add(
            responses.GET, "https://api.test.com/zones", json=zones_dict, status=200
        )

        self.client._zones_cache = None
        zones = self.client._get_zones()
        self.assertEqual(zones, zones_dict["zones"])

        # Test with data key
        responses.reset()
        zones_data = {"data": [{"zoneName": "example.com", "id": "123"}]}
        responses.add(
            responses.GET, "https://api.test.com/zones", json=zones_data, status=200
        )

        self.client._zones_cache = None
        zones = self.client._get_zones()
        self.assertEqual(zones, zones_data["data"])

    def test_find_zone_no_match(self):
        self.client._zones_cache = [{"zoneName": "example.com", "id": "123"}]

        zone = self.client._find_zone_for_domain("notfound.org")
        self.assertIsNone(zone)

    def test_record_key_extraction(self):
        """Test that record keys are properly extracted from full names."""
        self.client._zones_cache = [{"zoneName": "example.com", "id": "123"}]

        # Mock the session.post to capture the request data
        with patch.object(self.client.session, "post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            self.client.add_txt_record(
                "test.example.com",
                "_acme-challenge.test.example.com",
                "validation",
                300,
            )

            # Check that the correct record key was used
            call_args = mock_post.call_args
            request_data = call_args[1]["json"]

            self.assertEqual(request_data["edits"][0]["newKey"], "_acme-challenge.test")


if __name__ == "__main__":
    unittest.main()
