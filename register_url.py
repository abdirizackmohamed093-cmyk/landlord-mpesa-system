import requests
from requests.auth import HTTPBasicAuth

# 1. Your Daraja Credentials
consumer_key = "nkgPcYLVAE4SFW7ehOneufmuZpVIZHp3AvE64C6F8nf2Qpv4"
consumer_secret = "PKDdXAjTgpSs0oyqxU5FGX0wHeWGPM4dAgyJw3WKKAAe5gw7OOvA2ASGRa5hD6M7"
api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"

# 2. Get Access Token
token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
response = requests.get(token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
access_token = response.json()['access_token']

# 3. The Registration Data
# REPLACE THIS URL WITH YOUR ACTUAL NGROK URL
my_ngrok_url = "https://skedaddle-tarmac-grub.ngrok-free.app"

payload = {
    "ShortCode": "174379", 
    "ResponseType": "Completed",
    "ConfirmationURL": f"{my_ngrok_url}/payment-callback",
    "ValidationURL": f"{my_ngrok_url}/payment-callback"
}

headers = {"Authorization": f"Bearer {access_token}"}

response = requests.post(api_url, json=payload, headers=headers)
print(response.json())