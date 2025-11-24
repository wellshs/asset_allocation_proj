"""Korea Investment & Securities provider implementation."""

import requests
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict

from src.account.providers.base import AccountProvider
from src.account.models import (
    BrokerageAccount,
    AccountHoldings,
    SecurityPosition,
    AccountStatus,
    AssetType,
)
from src.account.config import AccountCredentials
from src.account.exceptions import AccountAuthException, AccountAPIException
from src.account.rate_limiter import RateLimiter
from src.account.client import with_retry


class KoreaInvestmentProvider(AccountProvider):
    """
    Provider implementation for Korea Investment & Securities.

    API Documentation: https://apiportal.koreainvestment.com
    """

    BASE_URL = "https://openapi.koreainvestment.com:9443"
    AUTH_ENDPOINT = "/oauth2/tokenP"
    HOLDINGS_ENDPOINT = "/uapi/domestic-stock/v1/trading/inquire-balance"

    def __init__(self):
        """Initialize provider with rate limiter."""
        self.rate_limiter = RateLimiter(delay=1.1)

    def authenticate(
        self, account: BrokerageAccount, credentials: AccountCredentials
    ) -> BrokerageAccount:
        """
        Authenticate with Korea Investment & Securities API.

        Args:
            account: Account to authenticate
            credentials: API credentials

        Returns:
            BrokerageAccount: Account with access token

        Raises:
            AccountAuthException: If authentication fails
        """
        url = f"{self.BASE_URL}{self.AUTH_ENDPOINT}"

        payload = {
            "grant_type": "client_credentials",
            "appkey": credentials.app_key,
            "appsecret": credentials.app_secret,
        }

        try:
            with self.rate_limiter:
                response = requests.post(url, json=payload, timeout=30)

            if response.status_code != 200:
                raise AccountAuthException(
                    f"Authentication failed: {response.status_code} - {response.text}"
                )

            data = response.json()
            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 86400)  # Default 24 hours

            if not access_token:
                raise AccountAuthException("No access token in response")

            # Update account with auth info
            account.status = AccountStatus.CONNECTED
            account.access_token = access_token
            account.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            return account

        except requests.RequestException as e:
            raise AccountAuthException(f"Network error during authentication: {str(e)}")

    @with_retry
    def fetch_holdings(self, account: BrokerageAccount) -> AccountHoldings:
        """
        Fetch current holdings from Korea Investment & Securities.

        Args:
            account: Authenticated account

        Returns:
            AccountHoldings: Current holdings and cash balance

        Raises:
            AccountAuthException: If account is not authenticated
            AccountAPIException: If API request fails
        """
        if not account.is_authenticated():
            raise AccountAuthException("Account is not authenticated")

        url = f"{self.BASE_URL}{self.HOLDINGS_ENDPOINT}"

        # Split account number: first 8 digits + last 2 digits
        cano = account.account_number[:8]
        acnt_prdt_cd = account.account_number[8:10]

        headers = {
            "authorization": f"Bearer {account.access_token}",
            "appkey": account.account_number,  # This should come from credentials
            "appsecret": "secret",  # This should come from credentials
            "tr_id": "TTTC8434R",  # Real trading
        }

        params = {
            "CANO": cano,
            "ACNT_PRDT_CD": acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "N",
            "INQR_DVSN": "01",  # All holdings
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
        }

        try:
            with self.rate_limiter:
                response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                raise AccountAPIException(
                    f"API request failed: {response.status_code} - {response.text}"
                )

            data = response.json()
            return self._parse_holdings_response(account.account_id, data)

        except requests.Timeout:
            raise AccountAPIException("Request timeout")
        except requests.RequestException as e:
            raise AccountAPIException(f"Network error: {str(e)}")

    def _parse_holdings_response(
        self, account_id: str, data: Dict[str, Any]
    ) -> AccountHoldings:
        """
        Parse API response into AccountHoldings.

        Args:
            account_id: Account identifier
            data: API response data

        Returns:
            AccountHoldings: Parsed holdings
        """
        output1 = data.get("output1", {})
        output2 = data.get("output2", [])

        # Parse cash balance
        cash_balance = Decimal(output1.get("dnca_tot_amt", "0"))
        total_value = Decimal(output1.get("tot_evlu_amt", "0"))

        # Parse positions
        positions = []
        for item in output2:
            position = SecurityPosition(
                symbol=item.get("pdno", ""),
                name=item.get("prdt_name", ""),
                quantity=Decimal(item.get("hldg_qty", "0")),
                average_price=Decimal(item.get("pchs_avg_pric", "0")),
                current_price=Decimal(item.get("prpr", "0")),
                current_value=Decimal(item.get("evlu_amt", "0")),
                asset_type=AssetType.STOCK,
                profit_loss=Decimal(item.get("evlu_pfls_amt", "0"))
                if item.get("evlu_pfls_amt")
                else None,
            )
            positions.append(position)

        return AccountHoldings(
            account_id=account_id,
            timestamp=datetime.now(),
            cash_balance=cash_balance,
            positions=positions,
            total_value=total_value,
        )
