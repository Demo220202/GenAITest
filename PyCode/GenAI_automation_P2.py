import json
import os
import argparse
import subprocess
import requests
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import Deployment
from azure.mgmt.cognitiveservices.models import Sku as DeploymentSku  # Import Sku directly and rename it

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


def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def get_cognitive_account(client, resource_group_name, account_name):
    try:
        return client.accounts.get(resource_group_name, account_name)
    except Exception as e:
        print(f"Failed to fetch Cognitive Account: {account_name} in RG: {resource_group_name}. Error: {e}")
        return None

def disable_version_auto_upgrade(subscription_id, resource_group, account_name, deployment_name, credential, api_version="2023-10-01-preview"):

    url = (
        f"https://management.azure.com/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices"
        f"/accounts/{account_name}/deployments/{deployment_name}?api-version={api_version}"
    )

    token = credential.get_token("https://management.azure.com/.default").token

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    deployment = response.json()

    # Update to disable automatic version updates
    deployment["properties"]["versionUpgradeOption"] = "NoAutoUpgrade"
    # deployment["properties"]["dynamicThrottlingEnabled"] = True

    # Send PATCH request to update the deployment
    patch_response = requests.put(url, headers=headers, json=deployment)

    if patch_response.status_code in [200, 201]:
        print("✅ Auto version update disabled successfully.")
        response = requests.get(url, headers=headers)
        deployment = response.json()
        print(json.dumps(deployment, indent=4))

    else:
        print("❌ Failed to update deployment:", patch_response.status_code, patch_response.text)



def enable_dynamic_quota(subscription_id, resource_group, account_name, deployment_name, credential, api_version="2023-10-01-preview"):
    """
    Enables the Dynamic Quota (Dynamic Throttling) for an Azure Cognitive Services deployment.

    :param subscription_id: Azure Subscription ID
    :param resource_group: Azure Resource Group name
    :param account_name: Cognitive Services account name
    :param deployment_name: Deployment name (e.g., GPT-4o)
    :param api_version: API version (default: "2023-10-01-preview")
    :return: Response JSON or error message
    """

    # Convert the Python dictionary to a JSON string
    # body_json = json.dumps(body)

    # Construct the Azure CLI command
    az_command = [
        "az", "rest",
        "--method", "patch",
        "--url",
        f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{account_name}/deployments/{deployment_name}?api-version={api_version}",
        "--body", '{"properties": {"dynamicThrottlingEnabled": true} }'
    ]

    try:
        # Execute the command and capture the output
        result = subprocess.run(az_command, capture_output=True, text=True, check=True)

        # Print the response from Azure
        print(f"Response: {result.stdout}")

        # Parse the response as JSON
        response = json.loads(result.stdout)

        # Validate if both settings are applied
        if "properties" in response and response["properties"].get("dynamicThrottlingEnabled") == True or response[
            "properties"].get("raiPolicyName") == "Microsoft.DefaultV2":
            return {"success": True, "message": "✅ Successfully enabled Dynamic Quota!",
                    "response": response}
        else:
            return {"success": False, "message": f"❌ Failed to apply settings. Response: {response}"}

    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"❌ Command failed with error: {e.stderr}"}


def create_or_update_deployment(client, resource_group_name, account_name, deployment_name, capacity, model_name, model_version, sku_name):
    try:
        deployment_params = Deployment(
            sku=DeploymentSku(name=sku_name, capacity=capacity),
            properties={
                "model": {
                    "format": "OpenAI",
                    "name": model_name,
                    "version": model_version,
                    #"source": "azureOpenAI"
                }
            }
        )

        deployment = client.deployments.begin_create_or_update(
            resource_group_name,
            account_name,
            deployment_name,
            deployment_params
        ).result()

        print(f"Deployment '{deployment_name}' successfully created/updated.")
    except Exception as e:
        print(f"Failed to create/update deployment '{deployment_name}'. Error: {e}")

def main():
    config = load_config('openai_resources.json')
    subscription_id = config['subscription_id']
    resources = config['resources']


    credential = authenticate()
    client = CognitiveServicesManagementClient(credential, subscription_id)

    for resource in resources:
        account = get_cognitive_account(client, resource['resource_group'], resource['resource_name'])

        if account:
            create_or_update_deployment(
                client,
                resource['resource_group'],
                resource['resource_name'],
                resource['deployment_name'],
                resource['capacity'],
                resource['model_name'],
                resource['model_version'],
                resource['sku_name']
            )

            if resource['sku_name'] != "DataZoneStandard":
                print(enable_dynamic_quota(subscription_id, resource['resource_group'], resource['resource_name'], resource['deployment_name'], credential,"2023-10-01-preview"))


            disable_version_auto_upgrade(subscription_id, resource['resource_group'], resource['resource_name'], resource['deployment_name'], credential,"2023-10-01-preview")

            deployment_details = client.deployments.get(resource['resource_group'], resource['resource_name'], resource['deployment_name'])
            deployment_json = deployment_details.as_dict()

            print("\n🔹 Deployment JSON after toggling:\n", json.dumps(deployment_json, indent=4))


if __name__ == "__main__":
    main()
