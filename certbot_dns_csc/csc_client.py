import logging
from typing import Any, Dict, List, Optional

import requests
from certbot import errors

logger = logging.getLogger(__name__)


class CSCClient:
    """
    Encapsulates all communication with the CSC Global Domain Manager API.
    """

    def __init__(self, api_key: str, bearer_token: str, base_url: str):
        self.api_key = api_key
        self.bearer_token = bearer_token
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "accept": "application/json;charset=UTF-8",
                "apikey": self.api_key,
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json;charset=UTF-8",
            }
        )
        self._zones_cache: Optional[List[Dict[str, Any]]] = None

    def add_txt_record(self, domain: str, name: str, value: str, ttl: int) -> None:
        """
        Add a TXT record using the CSC API.

        :param str domain: The domain to add the record to.
        :param str name: The record name (without the domain).
        :param str value: The record value.
        :param int ttl: The record TTL.
        :raises certbot.errors.PluginError: if an error occurs communicating with the CSC API
        """
        zone_name = self._find_zone_for_domain(domain)
        if not zone_name:
            raise errors.PluginError(f"Unable to determine zone for domain {domain}")

        # Extract the record key (remove zone from the full name)
        record_key = (
            name.replace(f".{zone_name}", "")
            if name.endswith(f".{zone_name}")
            else name
        )

        data = {
            "zoneName": zone_name,
            "edits": [
                {
                    "recordType": "TXT",
                    "action": "ADD",
                    "newKey": record_key,
                    "newValue": value,
                    "newTtl": ttl,
                    "comments": f"ACME challenge for {domain}",
                }
            ],
        }

        try:
            response = self.session.post(f"{self.base_url}/zones/edits", json=data)
            response.raise_for_status()
            logger.debug(
                f"Successfully added TXT record for {name} in zone {zone_name}"
            )
        except requests.exceptions.RequestException as e:
            raise errors.PluginError(f"Error adding TXT record: {e}")

    def del_txt_record(self, domain: str, name: str, value: str) -> None:
        """
        Delete a TXT record using the CSC API.

        :param str domain: The domain to delete the record from.
        :param str name: The record name (without the domain).
        :param str value: The record value.
        :raises certbot.errors.PluginError: if an error occurs communicating with the CSC API
        """
        zone_name = self._find_zone_for_domain(domain)
        if not zone_name:
            raise errors.PluginError(f"Unable to determine zone for domain {domain}")

        # Extract the record key (remove zone from the full name)
        record_key = (
            name.replace(f".{zone_name}", "")
            if name.endswith(f".{zone_name}")
            else name
        )

        data = {
            "zoneName": zone_name,
            "edits": [
                {
                    "recordType": "TXT",
                    "action": "PURGE",
                    "currentKey": record_key,
                    "currentValue": value,
                }
            ],
        }

        try:
            response = self.session.post(f"{self.base_url}/zones/edits", json=data)
            response.raise_for_status()
            logger.debug(
                f"Successfully deleted TXT record for {name} in zone {zone_name}"
            )
        except requests.exceptions.RequestException as e:
            raise errors.PluginError(f"Error deleting TXT record: {e}")

    def _find_zone_for_domain(self, domain: str) -> Optional[str]:
        """
        Find the zone that contains the given domain.

        :param str domain: The domain to find the zone for.
        :return: The zone name, or None if not found.
        :rtype: str or None
        """
        zones = self._get_zones()

        # Sort zones by length (longest first) to find the most specific match
        sorted_zones = sorted(
            zones, key=lambda x: len(x.get("zoneName", "")), reverse=True
        )

        for zone in sorted_zones:
            zone_name = zone.get("zoneName", "")
            if domain == zone_name or domain.endswith(f".{zone_name}"):
                return zone_name

        return None

    def _get_zones(self) -> List[Dict[str, Any]]:
        """
        Get all zones from the CSC API.

        :return: List of zone dictionaries.
        :rtype: list
        :raises certbot.errors.PluginError: if an error occurs communicating with the CSC API
        """
        if self._zones_cache is not None:
            return self._zones_cache

        try:
            response = self.session.get(f"{self.base_url}/zones")
            response.raise_for_status()
            zones_data = response.json()

            # Handle different possible response structures
            if isinstance(zones_data, list):
                self._zones_cache = zones_data
            elif isinstance(zones_data, dict) and "zones" in zones_data:
                self._zones_cache = zones_data["zones"]
            elif isinstance(zones_data, dict) and "data" in zones_data:
                self._zones_cache = zones_data["data"]
            else:
                # Assume the response itself contains zone data
                self._zones_cache = [zones_data] if isinstance(zones_data, dict) else []

            logger.debug(f"Retrieved {len(self._zones_cache)} zones from CSC API")
            return self._zones_cache

        except requests.exceptions.RequestException as e:
            raise errors.PluginError(f"Error retrieving zones: {e}")
