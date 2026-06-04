import requests
from requests.auth import HTTPBasicAuth

# Paste your credentials here
consumer_key = "nkgPcYLVAE4SFW7ehOneufmuZpVIZHp3AvE64C6F8nf2Qpv4"
consumer_secret = "PKDdXAjTgpSs0oyqxU5FGX0wHeWGPM4dAgyJw3WKKAAe5gw7OOvA2ASGRa5hD6M7"

# Get Token
token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
token = requests.get(token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret)).json()['access_token']

# Check Registered URL
check_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/query" # Note: This is a conceptual check
print("Check your logs on the Daraja dashboard for status!")