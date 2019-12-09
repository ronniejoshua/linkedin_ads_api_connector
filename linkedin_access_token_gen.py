import requests


# Linkedin Authentication
# Reference Documentation
# -----------------------
# https://docs.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow?context=linkedin/marketing/context
# https://docs.microsoft.com/en-us/linkedin/marketing/integrations/ads-reporting/ads-reporting#statistics-finder

# Step 0
# Application to make the linkedin api call
# -----------------------------------------
# https://www.linkedin.com/developers/


# Step 1: Configure Your Application
# ----------------------------------
# https://www.linkedin.com/developers/apps/{app_id}/auth


# Step 2: Request an Authorization Code
# -------------------------------------
client_id = 'my_client_id'
clientSecret = 'my_client_secret'
redirect_uri = 'https://redirect_uri'
response_type = 'code'
state = 'my_state'

r_ads_reporting = 'r_ads_reporting'
rw_ads = 'rw_ads'
query = " ".join([r_ads_reporting, rw_ads])

payload = {
    'response_type': response_type,
    'client_id': client_id,
    'redirect_uri': redirect_uri,
    'state': state,
    'scope': query
}

r = requests.get('https://www.linkedin.com/oauth/v2/authorization', params=payload)

# Click the following URL and provide the credentials
# ---------------------------------------------------
print(r.url)

# Copy the response url to extract the Authorization Code
# Response URL contains Authorization Code & State
# ------------------------------------------------
code = ""


# Step 3: Exchange Authorization Code for an Access Token
# -------------------------------------------------------

payload = {
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': redirect_uri,
    'client_id': client_id,
    'client_secret': clientSecret
}

headers = {'Content-Type': 'application/x-www-form-urlencoded',
           'Accept': 'text/plain'}

r = requests.post(
    'https://www.linkedin.com/oauth/v2/accessToken', params=payload, headers=headers)

r.json()

# CRITICAL : Access Token - Use to make Authenticated Requests
# ------------------------------------------------------------
access_token = r.json()['access_token']
