from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
import json
import argparse
import os


# # Set your Azure Subscription ID
# subscription_id = "f5eb2504-71c9-4d5d-b758-ecfc952962b5"
# resource_group_name = "ChaseGPTAdvancedStories"
#
# # Authenticate
# credential = DefaultAzureCredential()
# client = ResourceManagementClient(credential, subscription_id)
# cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)
#
# # Fetch resources in the resource group
# resources = client.resources.list_by_resource_group(resource_group_name)

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

# parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
#
# client_id = parser.add_argument('--client_id', required=True, help='CLIENT_ID')
# client_secret = parser.add_argument('--client_secret', required=True, help='CLIENT_SECRET')
# tenant_id = parser.add_argument('--tenant_id', required=True, help='TENANT_ID')


def get_type_region(resource):

    res_type = None
    region = None

    for i in range(len(resource)):

        if "PredictionAuth" in resource or "PrAuth" in resource:

            res_type = "Authoring"
            region = "NorthCentralUS"
            break

        elif i > 0 and resource[i] >= 'A' and resource[i] <= 'Z':
            res_type = resource[:i]
            region = resource[i:]
            break

    print("Through first function: ", res_type, region)
    return res_type, region

def getRegionNType(resource_client, resource_group_name, resource_name):

    resources = resource_client.resources.list_by_resource_group(resource_group_name)

    resource_type = None

    if "PredictionAuth" in resource_name or "PrAuth" in resource_name:
        resource_type = "Authoring"
    elif "Evaluation" in resource_name:
        resource_type = "Evaluation"
    elif "Prediction" in resource_name:
        resource_type = "Prediction"

    for resource in resources:
        if resource.name == resource_name:
            return resource_type, resource.location


def getQueryVariables(subs_id, res_grp_name, client_id, client_secret, tenant_id, env):
    # Set your Azure Subscription ID
    subscription_id = subs_id
    resource_group_name = res_grp_name

    # Authenticate
    credential = authenticate()
    client = ResourceManagementClient(credential, subscription_id)
    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)
    resource_client = ResourceManagementClient(credential, subscription_id)

    # Fetch resources in the resource group
    resources = client.resources.list_by_resource_group(resource_group_name)

    # env = "prod"
    length = len(env)

    query_variables = {}

    # Print resource details
    for resource in resources:
        try:
            # print(resource.name[27:])
            # print(len(res_grp_name) + 4)
            resource_ref = resource.name.replace("-Datazone", "")
            res_type, region = get_type_region(resource_ref[len(res_grp_name) + length:])
            res_type, region = getRegionNType(resource_client, resource_group_name, resource.name)
            # print(res_type, region)

            keys = cognitive_client.accounts.list_keys(resource_group_name, resource.name)
            resource_fetch = cognitive_client.accounts.get(resource_group_name, resource.name)
            endpoint = resource_fetch.properties.endpoint

            query_variables[resource.name] = {
                'type': f'Open AI {res_type}',
                'region': region,
                'endpoint': resource_fetch.properties.endpoint,
                'keys': keys.key1
            }

            print(f"Name: {resource.name}, Endpoint: {resource_fetch.properties.endpoint}, Key: {keys.key1}")
        except Exception as e:
            print(f"Error retrieving keys for {resource.name}: {e}")

    print(json.dumps(query_variables, indent=4))

    return query_variables





