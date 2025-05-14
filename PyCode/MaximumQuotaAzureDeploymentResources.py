import requests
import json
import sys
import os
import subprocess
from azure.identity import DefaultAzureCredential, ClientSecretCredential

def authenticate():
    client_id = os.getenv("ARM_CLIENT_ID")
    client_secret = os.getenv("ARM_CLIENT_SECRET")
    tenant_id = os.getenv("ARM_TENANT_ID")

    if not all([client_id, client_secret, tenant_id]):
        raise ValueError("Missing one or more Azure credentials. Please check your environment variables.")

    credentials = ClientSecretCredential(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id
    )
    return credentials

def get_quota_details(subscription_id, region, access_token, deployment_name, sku_name):
    url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CognitiveServices/locations/{region}/usages?api-version=2023-05-01"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            #print("Quota Details:", json.dumps(data, indent=2))  # Print the response for debugging

            for item in data.get("value", []):
                if "name" in item and "limit" in item:
                    name = item["name"]["value"]
                    limit = item["limit"]
                    current_value = item.get("currentValue", 0)

                    #print(f"Quota Type: {name}, Limit: {limit}, Current Usage: {current_value}")

                    if name == f"OpenAI.{sku_name}.{deployment_name}":
                        print(item)
                        print(f"Quota Type: {name}, Limit: {limit}, Current Usage: {current_value}")
                        return limit  # Return the maximum capacity available

            print("Warning: No 'TokensPerMinute' quota found in the response.")
            return None

        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")
            return None

    except requests.RequestException as e:
        print(f"Request Error: {e}")
        return None


# subscription_id = "b89c0503-4130-4b64-a0cf-bed256f28fc9"
# # resource_group = "Zenarate-OP-30GPTAdvancedStories"
# # resource_name = "Zenarate-OP-30ProdGPTAdvancedStoriesEvaluationWestUS"
# region = "WestUS"
# deployment_name = "gpt-4o"
# sku_name = "Standard"

def get_max_capacity(subscription_id, region, deployment_name, sku_name):

    # access_token = os.popen("az account get-access-token --query accessToken -o tsv").read().strip()
    credential = authenticate()
    access_token = credential.get_token("https://management.azure.com/.default").token
    #sku_name = "Standard" # As per current scenario

    quota_limit = get_quota_details(subscription_id, region, access_token, deployment_name, sku_name)

    if quota_limit:
        print(json.dumps({"maximum_capacity": quota_limit}))
    else:
        print(json.dumps({"error": "Failed to retrieve maximum capacity"}))

    return quota_limit

