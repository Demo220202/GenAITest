import os
import json
import subprocess
import argparse
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import Deployment, DeploymentMode

# Constants
RESOURCE_FILE = "openai_resources.json"

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


parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
#parser.add_argument('--client_id', required=True, help='CLIENT_ID')
#parser.add_argument('--client_secret', required=True, help='CLIENT_SECRET')
#parser.add_argument('--tenant_id', required=True, help='TENANT_ID')

parser.add_argument('--subscription_id', required=True, help='Azure Subscription ID')

args = parser.parse_args()

SUBSCRIPTION_ID = args.subscription_id  # Replace with your Azure Subscription ID
#client_id = args.client_id
#client_secret = args.client_secret
#tenant_id = args.tenant_id


# Authenticate with Azure
credentials = authenticate()
resource_client = ResourceManagementClient(credentials, SUBSCRIPTION_ID)


def set_subscription(subscription_id):
    """
    Sets the active Azure subscription programmatically using subprocess.
    """
    try:
        print(f"Setting subscription to: {subscription_id}")
        result = subprocess.run(
            ["az", "account", "set", "--subscription", subscription_id],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Subscription set successfully: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error setting subscription: {e.stderr}")
        raise


def delete_resource(resource_group, resource_name, region):
    """
    Deletes a specific Azure resource.
    """
    print(f"Deleting resource: {resource_name} in resource group: {resource_group}")
    try:
        resource_client.resources.begin_delete(
            resource_group_name=resource_group,
            resource_provider_namespace="Microsoft.CognitiveServices",
            parent_resource_path="",
            resource_type="accounts",
            resource_name=resource_name,
            api_version="2023-05-01"
        ).result()
        print(f"Successfully deleted resource: {resource_name}")

        # Attempt to purge the deleted resource
        purge_successful = purge_resource(resource_group, resource_name, region.lower())

        if purge_successful:
            print(f"Successfully purged resource: {resource_name}")
        else:
            print(f"Resource {resource_name} could not be purged.")

        return True  # Indicate successful deletion
    except Exception as e:
        print(f"Failed to delete resource {resource_name}: {e}")
        return False  # Indicate failure


def purge_resource(resource_group, resource_name, region):
    """
    Purges a soft-deleted Azure resource.
    """
    try:
        print(f"Purging resource: {resource_name} in resource group: {resource_group}")
        result = subprocess.run(
            [
                "az", "cognitiveservices", "account", "purge",
                "--location", region,
                "--resource-group", resource_group,
                "--name", resource_name
            ],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Purge command output: {result.stdout}")
        return True  # Purge successful
    except subprocess.CalledProcessError as e:
        print(f"Failed to purge resource {resource_name}: {e.stderr}")
        return False  # Purge failed


def delete_resource_group(resource_group):
    """
    Deletes the entire resource group if it's empty.
    """
    print(f"Deleting resource group: {resource_group}")
    try:
        resource_client.resource_groups.begin_delete(resource_group).result()
        print(f"Successfully deleted resource group: {resource_group}")
    except Exception as e:
        print(f"Failed to delete resource group {resource_group}: {e}")


def main():
    # Set the Azure subscription
    set_subscription(SUBSCRIPTION_ID)

    # Load the resources JSON file
    try:
        with open(RESOURCE_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File {RESOURCE_FILE} not found. Ensure it exists and try again.")
        return

    if not data or "resources" not in data:
        print("No resources found to delete.")
        return

    resources = data["resources"]
    resource_groups = {}

    # Delete resources
    for resource in resources:
        resource_group = resource["resource_group"]
        resource_name = resource["resource_name"]
        region = resource["region"]

        if resource_group not in resource_groups:
            resource_groups[resource_group] = True  # Assume success initially

        deletion_successful = delete_resource(resource_group, resource_name, region)

        if not deletion_successful:
            resource_groups[resource_group] = False  # Mark group as failed if deletion fails

    # Delete resource groups only if all resources within them are deleted successfully
    for rg, delete_allowed in resource_groups.items():
        if delete_allowed:
            delete_resource_group(rg)
        else:
            print(f"Skipping deletion of resource group {rg} because not all resources were deleted successfully.")

    print("Revert process completed successfully.")


if __name__ == "__main__":
    main()
