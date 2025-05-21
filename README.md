# Tik-Tok ad manager #
AIM: Use the TikTok Marketing API to update budgets based on ad performance

## Workflow Summary:
1. **Authenticate** with TikTok Marketing API to retrive 1hr valid token
2. **Fetch all auction campaigns** and their performance metrics (spend, complete payment rate).
3. **Calculate ROAS** for each campaign.
4. **Determine budget adjustment rate** using formulas houses in utils.py
5. **Clamp amendments** No more than ±75% to buget increase, and ensure budgets don’t fall below £50.
6. **Apply updated budgets** using API

### API endpoints used

1) [authenctication token](https://business-api.tiktok.com/portal/docs?id=1738373164380162)
2) [campaigns info](https://business-api.tiktok.com/portal/docs?id=1739315828649986)
3) [performance metrics (spend + total_complete_payment_rate)](https://business-api.tiktok.com/portal/docs?id=1751625293044737)
4) [get budget](https://business-api.tiktok.com/portal/docs?id=1739381246298114)
5) [update budget](https://business-api.tiktok.com/portal/docs?id=1739320422086657)

## File structure
| File               | Description |
|--------------------|-------------|
| `main.py`          | Main entry point, coordinates API calls and budget logic |
| `tik_tok_api.py`   | Handles all API interactions (auth, campaign performance, and campaign updates) |
| `utils.py`         | Contains logic for calculating ROAS, adjustment factor, new budget and retry logic for failed access to API  |
| `config.py`        | Houses all configurable values |
| `requirements.txt` | Python dependencies |


## considerations
- Sensitive variables are stored using environment variables
- private variables and methods used were approriate to designate should not be used by the client
- Used @dataclass to quickly implment 'Campaign' class which can represent each campaign and allow for budget comparisons between campaign attributes without cluttering the tik_tok_api.py file
- retry function housed in utlis.py can be used in main.py to handle retry's with API calls
- self._token_expiry ensures token is valid, this would be more important if multiple campaigns were being managed at high frequency
- get_campaigns method retrives the campaigns and budget in one call, reducing API calls
- The Task Overview specifies 'auction campaigns' not sure if filtering the buying_type controls this?
- Exhaustion criteria states "Correctness: Does the solution correctly identify and pause low-ROAS campaigns?". Task overview does not mention pausing low-ROAS campaigns?
- Increase user friendlness by implementing Flask/Dash to have simple web interface for users ammending configurable attributes like budget, target ROAS etc, would also be able to create dashboard displaying current performance stats on a campaign basis
- Implemented unit tests using pytest to cover the utility functions. I don’t have experience writing tests for API interactions, I looked into it and understand that mocking (e.g., using unittest.mock or pytest-mock) would be the typical approach. With access to a sandbox environment or mock server, I would extend testing to include the API integration points as well.