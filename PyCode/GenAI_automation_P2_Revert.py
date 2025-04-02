import json
import os
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

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

#client_id = parser.add_argument('--client_id', required=True, help='CLIENT_ID')
#client_secret = parser.add_argument('--client_secret', required=True, help='CLIENT_SECRET')
#tenant_id = parser.add_argument('--tenant_id', required=True, help='TENANT_ID')

def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def delete_deployment(client, resource_group_name, account_name, deployment_name):
    try:
        client.deployments.begin_delete(resource_group_name, account_name, deployment_name).result()
        print(f"Deployment '{deployment_name}' successfully deleted.")
    except Exception as e:
        print(f"Failed to delete deployment '{deployment_name}'. Error: {e}")

def main():
    config = load_config('openai_resources.json')
    subscription_id = config['subscription_id']
    resources = config['resources']

    credential = authenticate()
    client = CognitiveServicesManagementClient(credential, subscription_id)

    for resource in resources:
        delete_deployment(client, resource['resource_group'], resource['resource_name'], resource['deployment_name'])

if __name__ == "__main__":
    main()
