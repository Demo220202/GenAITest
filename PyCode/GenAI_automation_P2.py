import json
import os
import argparse
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import Deployment
from azure.mgmt.cognitiveservices.models import Sku as DeploymentSku  # Import Sku directly and rename it

def authenticate(client_id, client_secret, tenant_id):
    
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

def create_or_update_deployment(client, resource_group_name, account_name, deployment_name, capacity, model_name, model_version):
    try:
        deployment_params = Deployment(
            sku=DeploymentSku(name="Standard", capacity=capacity),
            properties={
                "model": {
                    "format": "OpenAI",
                    "name": model_name,
                    "version": model_version
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

    client_id = parser.add_argument('--client_id', required=True, help='CLIENT_ID')
    client_secret = parser.add_argument('--client_secret', required=True, help='CLIENT_SECRET')
    tenant_id = parser.add_argument('--tenant_id', required=True, help='TENANT_ID')

    credential = authenticate(client_id, client_secret, tenant_id)
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
                resource['model_version']
            )

if __name__ == "__main__":
    main()
