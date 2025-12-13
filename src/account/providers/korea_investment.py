"""Korea Investment & Securities provider implementation."""

import logging
import requests
from datetime import datetime, timedelta, timezone
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

logger = logging.getLogger(__name__)


class KoreaInvestmentProvider(AccountProvider):
    """
    Provider implementation for Korea Investment & Securities.

    API Documentation: https://apiportal.koreainvestment.com
    """

    BASE_URL = "https://openapi.koreainvestment.com:9443"
    AUTH_ENDPOINT = "/oauth2/tokenP"
    DOMESTIC_HOLDINGS_ENDPOINT = "/uapi/domestic-stock/v1/trading/inquire-balance"
    OVERSEAS_HOLDINGS_ENDPOINT = (
        "/uapi/overseas-stock/v1/trading/inquire-present-balance"
    )

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
            account.token_expiry = datetime.now(timezone.utc) + timedelta(
                seconds=expires_in
            )

            return account

        except requests.RequestException as e:
            raise AccountAuthException(f"Network error during authentication: {str(e)}")

    @with_retry
    def fetch_holdings(
        self, account: BrokerageAccount, credentials: AccountCredentials = None
    ) -> AccountHoldings:
        """
        Fetch current holdings from Korea Investment & Securities.

        Fetches both domestic and overseas stock holdings and merges them.

        Args:
            account: Authenticated account
            credentials: API credentials (required for API calls)

        Returns:
            AccountHoldings: Current holdings and cash balance (domestic + overseas)

        Raises:
            AccountAuthException: If account is not authenticated
            AccountAPIException: If API request fails
        """
        if not account.is_authenticated():
            raise AccountAuthException("Account is not authenticated")

        if not credentials:
            raise AccountAuthException("Credentials are required for API calls")

        # Fetch domestic and overseas holdings
        domestic = self._fetch_domestic_holdings(account, credentials)
        overseas = self._fetch_overseas_holdings(account, credentials)

        # Merge results
        return self._merge_holdings(account.account_id, domestic, overseas)

    def _fetch_domestic_holdings(
        self, account: BrokerageAccount, credentials: AccountCredentials
    ) -> AccountHoldings:
        """
        Fetch domestic stock holdings.

        Args:
            account: Authenticated account
            credentials: API credentials

        Returns:
            AccountHoldings: Domestic stock holdings

        Raises:
            AccountAPIException: If API request fails
        """
        url = f"{self.BASE_URL}{self.DOMESTIC_HOLDINGS_ENDPOINT}"

        # Split account number: first 8 digits + last 2 digits
        cano = account.account_number[:8]
        acnt_prdt_cd = account.account_number[8:10]

        headers = {
            "authorization": f"Bearer {account.access_token}",
            "appkey": credentials.app_key,
            "appsecret": credentials.app_secret,
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
            "CTX_AREA_FK100": "",  # Continuous query key (empty for first request)
            "CTX_AREA_NK100": "",  # Continuous query key (empty for first request)
        }

        try:
            with self.rate_limiter:
                response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                raise AccountAPIException(
                    f"API request failed: {response.status_code} - {response.text}"
                )

            data = response.json()
            return self._parse_domestic_holdings_response(account.account_id, data)

        except requests.Timeout:
            raise AccountAPIException("Request timeout")
        except requests.RequestException as e:
            raise AccountAPIException(f"Network error: {str(e)}")

    def _parse_domestic_holdings_response(
        self, account_id: str, data: Dict[str, Any]
    ) -> AccountHoldings:
        """
        Parse domestic stock API response into AccountHoldings.

        Args:
            account_id: Account identifier
            data: API response data

        Returns:
            AccountHoldings: Parsed domestic holdings
        """
        output1 = data.get("output1", [])
        output2 = data.get("output2", [])

        # Handle different response structures:
        # - When holdings exist: output1=dict (summary), output2=list (stocks)
        # - When no holdings: output1=list (empty), output2=list (summary)
        if isinstance(output1, dict):
            # Mock/test data structure or some API responses
            summary = output1
            stock_list = output2  # output2 contains stock positions
        elif isinstance(output1, list) and len(output1) > 0:
            # List with stock data
            if "pdno" in output1[0]:
                # output1 contains stocks
                summary = output2[0] if len(output2) > 0 else {}
                stock_list = output1
            else:
                # output1 contains summary
                summary = output1[0]
                stock_list = []
        else:
            # Empty output1, use output2 for summary
            summary = output2[0] if len(output2) > 0 else {}
            stock_list = []

        # Parse cash balance and total value
        cash_balance = Decimal(summary.get("dnca_tot_amt", "0"))
        total_value = Decimal(summary.get("tot_evlu_amt", "0"))

        # Parse positions
        positions = []
        for item in stock_list:
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
            timestamp=datetime.now(timezone.utc),
            cash_balance=cash_balance,
            positions=positions,
            total_value=total_value,
        )

    def _fetch_overseas_holdings(
        self, account: BrokerageAccount, credentials: AccountCredentials
    ) -> AccountHoldings:
        """
        Fetch overseas stock holdings.

        Args:
            account: Authenticated account
            credentials: API credentials

        Returns:
            AccountHoldings: Overseas stock holdings (USD cash converted to KRW + positions)

        Raises:
            AccountAPIException: If API request fails
        """
        url = f"{self.BASE_URL}{self.OVERSEAS_HOLDINGS_ENDPOINT}"

        # Split account number: first 8 digits + last 2 digits
        cano = account.account_number[:8]
        acnt_prdt_cd = account.account_number[8:10]

        headers = {
            "authorization": f"Bearer {account.access_token}",
            "appkey": credentials.app_key,
            "appsecret": credentials.app_secret,
            "tr_id": "CTRP6504R",  # Real trading - overseas present balance
        }

        params = {
            "CANO": cano,
            "ACNT_PRDT_CD": acnt_prdt_cd,
            "WCRC_FRCR_DVSN_CD": "02",  # Currency division code
            "NATN_CD": "840",  # Country code (840 = USA)
            "TR_MKET_CD": "00",  # Transaction market code
            "INQR_DVSN_CD": "00",  # Inquiry division code
        }

        try:
            with self.rate_limiter:
                response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                raise AccountAPIException(
                    f"Overseas API request failed: {response.status_code} - {response.text}"
                )

            data = response.json()
            logger.debug(f"Overseas API Response for {account.account_id}: {data}")

            # Check for error response
            if data.get("rt_cd") != "0":
                logger.warning(
                    f"Overseas holdings API returned error for {account.account_id}: "
                    f"{data.get('msg_cd')} - {data.get('msg1')}"
                )
                # Return empty holdings on error
                return AccountHoldings(
                    account_id=account.account_id,
                    timestamp=datetime.now(timezone.utc),
                    cash_balance=Decimal("0"),
                    positions=[],
                    total_value=Decimal("0"),
                )

            return self._parse_overseas_holdings_response(account.account_id, data)

        except requests.Timeout:
            raise AccountAPIException("Request timeout")
        except requests.RequestException as e:
            raise AccountAPIException(f"Network error: {str(e)}")

    def _parse_overseas_holdings_response(
        self, account_id: str, data: Dict[str, Any]
    ) -> AccountHoldings:
        """
        Parse overseas stock API response into AccountHoldings.

        Args:
            account_id: Account identifier
            data: API response data

        Returns:
            AccountHoldings: Parsed overseas holdings (USD converted to KRW)
        """
        output1 = data.get("output1", [])
        output2 = data.get("output2", [])

        # Handle output2 being list or dict
        if isinstance(output2, list):
            summary = output2[0] if len(output2) > 0 else {}
        else:
            summary = output2

        # Parse cash balance (in original currency, usually USD)
        # Convert to KRW using exchange rate from response
        cash_balance_usd = Decimal(
            summary.get("frcr_dncl_amt_2", "0")
        )  # Foreign currency deposit amount
        exchange_rate = Decimal(
            summary.get("frst_bltn_exrt", "1")
        )  # Exchange rate (first bulletin exchange rate)

        # Validate exchange rate to prevent valuation errors
        if exchange_rate == Decimal("1") and cash_balance_usd > 0:
            logger.warning(
                f"Exchange rate is 1.0 for account {account_id} with USD balance ${cash_balance_usd}. "
                "This may indicate missing exchange rate data from API."
            )

        cash_balance_krw = cash_balance_usd * exchange_rate

        # Total value in KRW (evaluation amount)
        total_value_krw = Decimal(
            summary.get("frcr_evlu_amt2", "0")
        )  # Foreign currency evaluation amount in KRW

        # Parse positions
        positions = []
        for item in output1:
            # Stock info from overseas API
            symbol = item.get("ovrs_pdno", "")  # Overseas product number (ticker)
            name = item.get("ovrs_item_name", "")  # Overseas item name
            quantity = Decimal(
                item.get("ovrs_cblc_qty", "0")
            )  # Overseas balance quantity

            # Prices in USD
            avg_price_usd = Decimal(
                item.get("pchs_avg_pric", "0")
            )  # Purchase average price
            current_price_usd = Decimal(
                item.get("ovrs_now_pric1", "0")
            )  # Overseas current price

            # Convert to KRW
            avg_price_krw = avg_price_usd * exchange_rate
            current_price_krw = current_price_usd * exchange_rate
            current_value_krw = Decimal(
                item.get("ovrs_stck_evlu_amt", "0")
            )  # Overseas stock evaluation amount

            profit_loss_krw = (
                Decimal(item.get("evlu_pfls_amt", "0"))
                if item.get("evlu_pfls_amt")
                else None
            )

            if quantity > 0:  # Only include if there's actual holdings
                position = SecurityPosition(
                    symbol=symbol,
                    name=name,
                    quantity=quantity,
                    average_price=avg_price_krw,
                    current_price=current_price_krw,
                    current_value=current_value_krw,
                    asset_type=AssetType.STOCK,
                    profit_loss=profit_loss_krw,
                )
                positions.append(position)

        return AccountHoldings(
            account_id=account_id,
            timestamp=datetime.now(timezone.utc),
            cash_balance=cash_balance_krw,
            positions=positions,
            total_value=total_value_krw,
            usd_cash_balance=cash_balance_usd,
            exchange_rate=exchange_rate,
        )

    def _merge_holdings(
        self, account_id: str, domestic: AccountHoldings, overseas: AccountHoldings
    ) -> AccountHoldings:
        """
        Merge domestic and overseas holdings.

        Args:
            account_id: Account identifier
            domestic: Domestic stock holdings (KRW)
            overseas: Overseas stock holdings (USD converted to KRW)

        Returns:
            AccountHoldings: Merged holdings with currency breakdown
        """
        # Combine cash balances
        total_cash = domestic.cash_balance + overseas.cash_balance

        # Combine positions
        all_positions = domestic.positions + overseas.positions

        # Calculate total value
        total_value = domestic.total_value + overseas.total_value

        return AccountHoldings(
            account_id=account_id,
            timestamp=datetime.now(timezone.utc),
            cash_balance=total_cash,
            positions=all_positions,
            total_value=total_value,
            krw_cash_balance=domestic.cash_balance,
            usd_cash_balance=overseas.usd_cash_balance,
            exchange_rate=overseas.exchange_rate,
        )
