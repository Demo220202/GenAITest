from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
import json

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

def authenticate(client_id, client_secret, tenant_id):
    
    credentials = ClientSecretCredential(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id
    )
    return credentials

client_id = parser.add_argument('--client_id', required=True, help='CLIENT_ID')
client_secret = parser.add_argument('--client_secret', required=True, help='CLIENT_SECRET')
tenant_id = parser.add_argument('--tenant_id', required=True, help='TENANT_ID')

def get_type_region(resource):

    res_type = None
    region = None

    for i in range(len(resource)):
        if i > 0 and resource[i] >= 'A' and resource[i] <= 'Z':
            res_type = resource[:i]
            region = resource[i:]
            break

    return res_type, region


def getQueryVariables(subs_id, res_grp_name):
    # Set your Azure Subscription ID
    subscription_id = subs_id
    resource_group_name = res_grp_name

    # Authenticate
    credential = credential = authenticate(client_id, client_secret, tenant_id)
    client = ResourceManagementClient(credential, subscription_id)
    cognitive_client = CognitiveServicesManagementClient(credential, subscription_id)

    # Fetch resources in the resource group
    resources = client.resources.list_by_resource_group(resource_group_name)


    query_variables = {}

    # Print resource details
    for resource in resources:
        try:
            # print(resource.name[27:])
            # print(len(res_grp_name) + 4)
            res_type, region = get_type_region(resource.name[len(res_grp_name) + 4:])
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





