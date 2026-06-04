import requests
from requests.auth import HTTPBasicAuth

# Paste your keys here from the Daraja portal
consumer_key = 'nkgPcYLVAE4SFW7ehOneufmuZpVIZHp3AvE64C6F8nf2Qpv4'
consumer_secret = 'PKDdXAjTgpSs0oyqxU5FGX0wHeWGPM4dAgyJw3WKKAAe5gw7OOvA2ASGRa5hD6M7'

def get_access_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    # The "Handshake"
    response = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print(f"✅ Handshake successful! Access Token: {token}")
        return token
    else:
        print(f"❌ Handshake failed: {response.text}")
        return None

if __name__ == "__main__":
    get_access_token()