import os
import requests
import json
import re
import subprocess
import argparse
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import Deployment, DeploymentMode
from azure.cli.core import get_default_cli
# from CapacityOfDeploymentResources import *
from BrandnamebySubs import *
from MaximumQuotaAzureDeploymentResources import *


# def parse_arguments():
#     parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
#     parser.add_argument('--subscription_id', required=True, help='Azure Subscription ID')
#     parser.add_argument('--region', required=True, help='Azure Region')
#     parser.add_argument('--deployment_model_name', required=True, help='Deployment Model Name')
#     parser.add_argument('--deployment_model_version', required=True, help='Deployment Model Version')
#     parser.add_argument('--brands', required=True, help='Comma-separated list of brands')
#     return parser.parse_args()

def version_based_deployment_name(deployment_name, deployment_version):

    deployment_version = deployment_version.replace('-', '')[4:]
    deployment_name = f"{deployment_name}-{deployment_version}"

    print(deployment_name)

    return deployment_name


parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
# Constants
# parser = argparse.ArgumentParser(description='Deploy OpenAI Resources')
parser.add_argument('--subscription_id', required=True, help='Azure Subscription ID')
parser.add_argument('--region', required=True, help='Azure Region')
parser.add_argument('--deployment_model_name', required=True, help='Deployment Model Name')
parser.add_argument('--deployment_model_version', required=True, help='Deployment Model Version')
parser.add_argument('--brands', required=True, help='Comma-separated list of brands')
parser.add_argument('--deployment_type', required=True, help='Deployment Type')
parser.add_argument('--env_m', required=True, help='Main environment')
parser.add_argument('--email', required=True, help='User email')

args = parser.parse_args()

SUBSCRIPTION_ID = args.subscription_id  # Replace with your Azure Subscription ID
REGION = args.region

DEPLOYMENT_TYPE = args.deployment_type
DEPLOYMENT_MODEL_NAME = args.deployment_model_name
DEPLOYMENT_MODEL_VERSION = args.deployment_model_version

DEPLOYMENT_MODEL = DEPLOYMENT_MODEL_NAME
DEPLOYMENT_MODEL_NAME = version_based_deployment_name(DEPLOYMENT_MODEL, DEPLOYMENT_MODEL_VERSION)

env = args.env_m
email = args.email

BRANDS = args.brands.split(",")

RESOURCE_TEMPLATE = {
    "PredictionAuth": ["NorthCentralUS"],
    # "Evaluation": ["WestUS"]
    # "Prediction": ["EastUS"]
    "Evaluation": ["EastUS", "WestUS3"],
    "Prediction": ["WestUS", "EastUS2"]
}

shorten_resource_type = {
    "PredictionAuth" : "PrAuth",
    "Evaluation" : "Eval",
    "Prediction" : "Pred"
}


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

def clean_brand_name(brand):
    # Remove all non-alphanumeric characters
    cleaned = re.sub(r'[^A-Za-z0-9]', '', brand)
    return cleaned

def shorten_region_name(region):

    shorten_region = ""
    for i in range(len(region)):
        if (region[i] >= 'A' and region[i] <= 'Z') or region[i].isdigit():
            shorten_region += region[i]

    return shorten_region

#parser.add_argument('--client_id', required=True, help='CLIENT_ID')
#parser.add_argument('--client_secret', required=True, help='CLIENT_SECRET')
#parser.add_argument('--tenant_id', required=True, help='TENANT_ID')

#client_id = args.client_id
#client_secret = args.client_secret
#tenant_id = args.tenant_id

# Authenticate with Azure
credentials = authenticate()
#credentials = DefaultAzureCredential()

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


def create_resource_group(brand_name):
    rg_name = f"{brand_name}GPTAdvancedStories"
    print(f"Creating Resource Group: {rg_name}")
    resource_client.resource_groups.create_or_update(
        rg_name,
        {"location": REGION}
    )
    return rg_name


# Update the create_openai_resources function to track created resources
def create_openai_resources(rg_name, brand_name, subscription_id):
    created_resources = []  # Track created resources
    for resource_type, regions in RESOURCE_TEMPLATE.items():
        for region in regions:
            region_short_name = shorten_region_name(region)
            resource_name = f"{brand_name}ProdGPTAdvancedStories{resource_type}{region_short_name.replace(' ', '')}DZ"
            if len(resource_name) >= 63:
                resource_name = f"{brand_name}ProdGPTAdvancedStories{shorten_resource_type[resource_type]}{region.replace(' ', '')}DZ"
            truncated_resource_name = resource_name[:50]
            deployment_name = f"Deploy-{truncated_resource_name}"[:64]

            # endpoint_url = f"https://{resource_name.lower()}.openai.azure.com/"
            endpoint_url = resource_name.lower()

            print(f"Creating OpenAI Resource: {resource_name} in {region}")

            deployment_properties = {
                "mode": DeploymentMode.incremental,
                "template": {
                    "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
                    "contentVersion": "1.0.0.0",
                    "resources": [
                        {
                            "type": "Microsoft.CognitiveServices/accounts",
                            "apiVersion": "2023-05-01",
                            "name": resource_name,
                            "location": region,
                            "sku": {"name": "S0"},
                            "kind": "OpenAI",
                            "properties": {
                                "customSubDomainName": endpoint_url
                            }
                        }
                    ]
                },
                "parameters": {}
            }

            resource_client.deployments.begin_create_or_update(
                rg_name,
                deployment_name,
                Deployment(properties=deployment_properties)
            ).result()  # Wait for completion

            capacity = get_max_capacity(subscription_id, region, DEPLOYMENT_MODEL, DEPLOYMENT_TYPE)
            #
            # Add resource details to list
            created_resources.append({
                "resource_group": rg_name,
                "resource_name": resource_name,
                "region": region,
                "deployment_name": DEPLOYMENT_MODEL_NAME,
                "capacity": capacity,
                "model_name": DEPLOYMENT_MODEL,
                "model_version": DEPLOYMENT_MODEL_VERSION,
                "sku_name": DEPLOYMENT_TYPE
            })

    return created_resources


def main():
    set_subscription(SUBSCRIPTION_ID)

    all_resources = []
    for brand in BRANDS:
        brand = clean_brand_name(brand)
        # brand = brand.replace("-Pay-As-You-Go", "").replace("-", "").replace(" ", "")
        rg_name = create_resource_group(brand)
        resources = create_openai_resources(rg_name, brand, SUBSCRIPTION_ID)
        all_resources.extend(resources)

    #brand = BRANDS[0].replace("-Pay-As-You-Go", "")
    # brand = BRANDS[0].replace("-Pay-As-You-Go", "").replace("-", "").replace(" ", "")
    brand = getBrandNamebySubscription(env, SUBSCRIPTION_ID, email)
    output_json = {
        "subscription_id": SUBSCRIPTION_ID,
        "resources": all_resources,
        "brand_name": brand
    }

    # Write all created resources to a JSON file
    with open("openai_resources.json", "w") as f:
        json.dump(output_json, f, indent=4)

    print("Resources written to openai_resources.json")


if __name__ == "__main__":
    main()
