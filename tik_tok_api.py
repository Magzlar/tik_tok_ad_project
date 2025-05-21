import requests
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

@dataclass
class Campaign:
    """Class object to repersent a campaign"""
    campaign_id: str
    spend: float = 0.0
    total_complete_payment_rate: float = 0.0
    budget : float = 0 


class TikTokAPIError(Exception):
    """Custom exception class for handling TikTok API releated errpoors"""
    pass

class TikTokMarketingAPI:
    BASE_URL = "https://business-api.tiktok.com/open_api/v1.3/"
    DEFAULT_TIMEOUT = 30  #seconds

    def __init__(self, app_id:str, auth_code:str, secret:str, ad_id:str):
        self.app_id = app_id
        self.auth_code = auth_code
        self.secret = secret
        self.ad_id = ad_id
        self._access_token = None
        self._token_expiry = None
        self._session = requests.Session()

    @property
    def access_token(self):
        """
        Returns: str: current valid access token
        """
        if self._access_token is None or self._token_expiry is None or datetime.now(timezone.utc) >= self._token_expiry:
            token_data = self.get_access_token()
            if not token_data or "access_token" not in token_data:
                raise TikTokAPIError("Failed to obtain access token")
            self._access_token = token_data["access_token"]
            self._token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        return self._access_token


    def _make_request(self, method, endpoint, params=None, json_data=None, headers=None):
        """
          Helper method to perform an HTTP request to the TikTok Marketing API

            Parameters:
                method (str): The HTTP method to use (e.g., 'GET', 'POST', 'PUT', 'DELETE')
                endpoint (str): The endpoint path (relative to BASE_URL) to call
                params (dict, optional): Query parameters to include in the request. Defaults to None type
                json_data (dict, optional): JSON body to include in the request (for POST/PUT). Defaults to None type
                headers (dict, optional): Additional headers to merge with the default headers. Defaults to None type

            Returns:
                dict: Parsed JSON response from API

            Raises:
                TikTokAPIError: If the request fails due to connection issues or recieves
        """

        url = f"{self.BASE_URL}{endpoint}"
        default_headers = {
            "Content-Type": "application/json",
            "Access-Token": self.access_token
        }
        if headers:
            default_headers.update(headers)

        try:
            response = self._session.request(
                method,
                url,
                params=params,
                json=json_data,
                headers=default_headers,
                timeout=self.DEFAULT_TIMEOUT
            )

            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise TikTokAPIError(f"API request failed: {str(e)}")

    def get_access_token(self):
        """
        Requests a new access token from the TikTok Marketing API using the app ID, secret, and auth code.

        Returns:
            dict: A dictionary containing:
                - access_token (str): The OAuth access token used for authenticated requests.
                - advertiser_ids (list): A list of advertiser IDs associated with the authenticated user.
                - ad_id_validity (bool): Whether the configured advertiser ID is included in the list of valid IDs.

        Raises:
            TikTokAPIError: If the API returns an error or the request fails.
        """

        try:
            data = self._make_request(
                "GET",
                "oauth2/access_token/",
                params={
                    "app_id": self.app_id,
                    "secret": self.secret,
                    "auth_code": self.auth_code
                }
            )

            if data.get("code") == 0:
                access_token = data["data"].get("access_token")
                advertiser_ids = data["data"].get("advertiser_ids", [])
                
                return {
                    "access_token": access_token,
                    "advertiser_ids": advertiser_ids,
                    "ad_id_validity": self.ad_id in advertiser_ids
                }
            else:
                error_msg = data.get("message", "Unknown error")
                raise TikTokAPIError(f"API error: {error_msg} (code: {data.get('code')})")
        except TikTokAPIError as e:
            raise TikTokAPIError(f"Failed to get access token: {str(e)}")

    def get_campaigns(self):
        """Returns:
          list: of campaign objects"""
        try:
            data = self._make_request(
                "GET",
                "campaign/get/",
                params={"advertiser_id": self.ad_id}
            )

            if data.get("code") == 0:
                return data.get("data", {}).get("list", [])
            else:
                error_msg = data.get("message", "Unknown error")
                raise TikTokAPIError(f"API error: {error_msg} (code: {data.get('code')})")
        except TikTokAPIError as e:
            raise TikTokAPIError(f"Failed to get campaigns: {str(e)}")

    def get_campaign_performance(self, days:int, min_spend:float, min_payment_rate:float):
        """
        Parameters:
            days: Number of days to look back
            min_spend: Minimum spend to consider campaign valid
            min_payment_rate: Minimum payment rate to consider campaign valid
            
        Returns:
            List of Campaign objects that meet the criteria
        """
        try:
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=days)

            campaigns = self.get_campaigns() 
            campaign_ids = [c["campaign_id"] for c in campaigns]
            campaign_budgets = {c["campaign_id"]: c["budget"] for c in campaigns} # A bit hacky work around to keep output usable in main.py

            if not campaign_ids:
                return []

            payload = {
                "advertiser_id": self.ad_id,
                "dimensions": ["campaign_id"],
                "metrics": ["spend", "total_complete_payment_rate"],
                "start_date": str(start_date),
                "end_date": str(end_date),
                "filtering": {"campaign_ids": campaign_ids,
                              "buying_types": "AUCTION"} # Not sure if this correct way to isolate auction based campaigns
            }

            data = self._make_request(
                "POST",
                "report/integrated/get/",
                json_data=payload
            )

            if data.get("code") != 0:
                error_msg = data.get("message", "Unknown error")
                raise TikTokAPIError(f"API error: {error_msg}")

            stats_list = data.get("data", {}).get("list", [])
            valid_campaigns = []

            for stat in stats_list:
                dimensions = stat.get("dimensions", {})
                metrics = stat.get("metrics", {})
                
                campaign_id = dimensions.get("campaign_id")
                spend = float(metrics.get("spend", 0))
                payment_rate = float(metrics.get("total_complete_payment_rate", 0))
                budget = campaign_budgets.get(campaign_id)

                if spend > min_spend and payment_rate > min_payment_rate:
                    valid_campaigns.append(
                        Campaign(
                            campaign_id=campaign_id,
                            spend=spend,
                            total_complete_payment_rate=payment_rate,
                            budget=budget
                        )
                    )

            return valid_campaigns

        except TikTokAPIError as e:
            raise TikTokAPIError(f"Failed to get campaign performance: {str(e)}")

    def update_campaign_budget(self, campaign_id: str, new_budget: float):
        """
        Updates the daily budget for a specific campaign using the TikTok Marketing API.

        Sends a request to update the budget for the specified campaign ID under the current advertiser,
        using the 'BUDGET_MODE_DAY' mode.

        Parameters:
            campaign_id (str): The unique identifier of the campaign to update.
            new_budget (float): The new daily budget to set (will be rounded to two decimal places).

        Returns:
            dict: The API response data confirming the update, if successful.

        Raises:
            TikTokAPIError: If the API request fails or returns an error status.
        """
        try:
            payload = {
                "advertiser_id": self.ad_id,
                "campaign_id": campaign_id,
                "budget_mode": "BUDGET_MODE_DAY",
                "budget": round(new_budget, 2)
            }

            data = self._make_request(
                "POST",
                "campaign/update/",
                json_data=payload
            )

            if data.get("code") != 0:
                error_msg = data.get("message", "Unknown error")
                raise TikTokAPIError(f"Failed to update campaign budget: {error_msg}")

            return data
        except TikTokAPIError as e:
            raise TikTokAPIError(f"Error updating campaign {campaign_id} budget: {str(e)}")
