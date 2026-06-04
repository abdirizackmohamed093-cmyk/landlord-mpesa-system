import requests
from requests.auth import HTTPBasicAuth
from mpesa_config import CONSUMER_KEY, CONSUMER_SECRET

url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

response = requests.get(
    url,
    auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET)
)

print("Status Code:", response.status_code)
print("Response:")
print(response.json())