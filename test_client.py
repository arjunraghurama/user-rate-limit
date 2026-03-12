import requests
import time
import os

# Keycloak settings
# In our docker-compose, keycloak is exposed on localhost:8080
KC_URL = "http://localhost:8080"
REALM = "myrealm"
CLIENT_ID = "react-client"
USERNAME = "testuser"
PASSWORD = "password"

# API settings
API_URL = "http://localhost:8000/api/data"

def get_token():
    print(f"Fetching token for {USERNAME} from Keycloak...")
    token_endpoint = f"{KC_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    payload = {
        "client_id": CLIENT_ID,
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password"
    }
    
    response = requests.post(token_endpoint, data=payload)
    
    if response.status_code == 200:
        print("Token successfully retrieved!")
        return response.json().get("access_token")
    else:
        print(f"Failed to get token: {response.text}")
        return None

def test_rate_limit(token, num_requests=10):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\nSending {num_requests} requests to {API_URL}...")
    
    for i in range(1, num_requests + 1):
        try:
            response = requests.get(API_URL, headers=headers)
            print(f"Request {i:2d} -> Status: {response.status_code} | Response: {response.text}")
            
            # Add a small delay so we don't overwhelm the local server immediately
            time.sleep(0.1)
        except Exception as e:
            print(f"Request {i:2d} -> Error: {e}")

if __name__ == "__main__":
    
    print("Testing Rate Limiting Implementation")
    print("-" * 40)
    
    token = get_token()
    
    if token:
        # Our app is configured to allow 5 requests per 60 seconds
        # So we should see 5 successes (200 OK) and 5 failures (429 Too Many Requests)
        test_rate_limit(token, num_requests=105)
