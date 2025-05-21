# Configurable parameters 
import os

# API params (use environment variables to protect these)
APP_ID = os.environ("APP_ID")
AUTH_CODE = os.environ("AUTH_CODE")
SECRET = os.environ("SECRET")
ADVERTISER_ID = "7041312028410778178" # Could be stored as environment variable as well

# Budget params
TARGET_ROAS = 1.5 # GBP
MAX_ADJUSTMENT = 0.75
MIN_BUDGET = 50 # GBP 
DAYS = 30
MIN_SPEND = 0
MIN_PAYMENT_RATE = 0