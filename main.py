# main.py
from tik_tok_api import TikTokMarketingAPI, TikTokAPIError
from config import APP_ID, AUTH_CODE, SECRET, ADVERTISER_ID, DAYS, MIN_SPEND, MIN_PAYMENT_RATE
from utils import calculate_roas, calculate_adjustment_factor, calculate_new_budget, retry

def main():
    api = TikTokMarketingAPI(
        app_id=APP_ID,
        auth_code=AUTH_CODE,
        secret=SECRET,
        ad_id=ADVERTISER_ID
    )

    # 1: Get access token
    try:
        # Use api.get_access_token() when we need full token metadata (e.g., advertiser_ids, ad_id validity).
        # Use api.access_token when we just need a valid token string for making authenticated API requests.
        # The access_token property includes lazy loading logic and will automatically refresh if expired.
        # token_info = api.access_token 
        token_info = retry(api.get_access_token, max_retries=2, delay=300, exception_types=(TikTokAPIError,))
        print("Access Token:", token_info["access_token"])
        print("Advertiser ID Valid:", token_info["ad_id_validity"])
        print("List of Valid IDs:", token_info["advertiser_ids"])
    except TikTokAPIError as e:
        print("Failed to get access token after retries:", e)
        return

    # 2: Get campaign performance stats
    try:
        campaigns = retry(
            api.get_campaign_performance,
            max_retries=2,
            delay=300,
            exception_types=(TikTokAPIError,),
            days=DAYS,
            min_spend=MIN_SPEND,
            min_payment_rate=MIN_PAYMENT_RATE
        )
        if not campaigns:
            print("No campaigns met the criteria.")
            return
    except TikTokAPIError as e:
        print("Failed to get campaign performance after retries:", e)
        return

    # 3: Process each campaign
    for campaign in campaigns:
        try:
            roas = calculate_roas(campaign)
            adjustment_factor = calculate_adjustment_factor(roas)
            current_budget = campaign.budget

            if current_budget is None:
                print(f"Skipping campaign {campaign.campaign_id} due to missing budget info.")
                continue

            new_budget = calculate_new_budget(current_budget, adjustment_factor)

            if new_budget != current_budget:
                retry(
                    api.update_campaign_budget,
                    max_retries=2,
                    delay=300,
                    exception_types=(TikTokAPIError,),
                    campaign_id=campaign.campaign_id,
                    new_budget=new_budget
                )
                print(f"Updated campaign {campaign.campaign_id}: {current_budget} -> {new_budget:.2f}")
            else:
                print(f"No budget change for campaign {campaign.campaign_id} (ROAS: {roas:.2f})")

        except TikTokAPIError as e:
            print(f"Error updating campaign {campaign.campaign_id}: {e}")
        except Exception as e:
            print(f"Unexpected error for campaign {campaign.campaign_id}: {e}")

if __name__ == "__main__":
    main()
