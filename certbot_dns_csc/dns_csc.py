"""DNS Authenticator for CSC Global Domain Manager."""
import logging
from typing import Callable, Optional

import zope.interface
from certbot import errors, interfaces
from certbot.plugins import dns_common
from certbot.plugins.dns_common import CredentialsConfiguration

from .csc_client import CSCClient

logger = logging.getLogger(__name__)


@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for CSC Global Domain Manager

    This Authenticator uses the CSC Global Domain Manager API to fulfill a dns-01 challenge.
    """

    description = "Obtain certificates using a DNS TXT record (if you are using CSC Global Domain Manager for DNS)."
    ttl = 300

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials: Optional[CredentialsConfiguration] = None
        self._csc_client: Optional[CSCClient] = None

    @classmethod
    def add_parser_arguments(
        cls, add: Callable[..., None], default_propagation_seconds: int = 360
    ) -> None:
        super(Authenticator, cls).add_parser_arguments(
            add, default_propagation_seconds=default_propagation_seconds
        )
        add(
            "credentials",
            help="CSC credentials INI file.",
            default="/etc/letsencrypt/csc.ini",
        )

    def more_info(self) -> str:
        return (
            "This plugin configures a DNS TXT record to respond to a dns-01 challenge using "
            + "the CSC Global Domain Manager API."
        )

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            "credentials",
            "CSC credentials INI file",
            {
                "api_key": "API key for CSC Global Domain Manager API",
                "bearer_token": "Bearer token for CSC Global Domain Manager API",
            },
        )

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_csc_client().add_txt_record(
            domain, validation_name, validation, self.ttl
        )

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_csc_client().del_txt_record(domain, validation_name, validation)

    def _get_csc_client(self) -> "CSCClient":
        if not self._csc_client:
            if self.credentials is None:
                raise errors.PluginError("Credentials not configured")

            try:
                base_url = (
                    self.credentials.conf("base_url")
                    or "https://apis.cscglobal.com/dbs/api/v2"
                )
            except KeyError:
                base_url = "https://apis.cscglobal.com/dbs/api/v2"

            api_key = self.credentials.conf("api_key")
            bearer_token = self.credentials.conf("bearer_token")

            if not api_key:
                raise errors.PluginError("Missing required credential: api_key")
            if not bearer_token:
                raise errors.PluginError("Missing required credential: bearer_token")

            self._csc_client = CSCClient(api_key, bearer_token, base_url)
        return self._csc_client
