import json
import os
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.resource import ResourceManagementClient
import re

alerts = []

email_receivers = [
    {"name": "Monika", "email": "monika.samant@zenarate.com"},
    {"name": "Robert Janssen", "email": "robertj@zenarate.com"},
    {"name": "Akash Kainth", "email": "akash@zenarate.com"},
    {"name": "Raghav Tayal", "email": "raghavt@zenarate.com"},
    {"name": "Vinod Singh", "email": "vinod.singh@zenarate.com"},
    {"name": "Sunil Kumar", "email": "sunilk@zenarate.com"},
    {"name": "Prashansa Tiwari", "email": "prashansa.tiwari@zenarate.com"},
    {"name": "Aditya", "email": "adityap@zenarate.com"},
    {"name": "Yashwant Keswani", "email": "yashwantk@zenarate.com"},
    {"name": "Praveen Balachandar", "email": "praveenb@zenarate.com"},
]

def clean_brand_name(brand):
    # Remove all non-alphanumeric characters
    cleaned = re.sub(r'[^A-Za-z0-9]', '', brand)
    return cleaned

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

# Inputs
# subscription_id = "your-subscription-id"
# brand_name = "YourBrand"  # Change dynamically
# resource_group_name = "YourResourceGroup"  # Given in the program
# deployment_resource_name = "YourDeploymentResource"  # Deployment resource name
# openai_resource_name = "YourOpenAIResource"  # OpenAI resource name
# regions = ["EastUS", "WestUS", "CentralUS", "NorthCentralUS", "SouthCentralUS"]

# Authenticate

def get_resource_id(resource_client, resource_group, resource_name, type=None):
    """Fetch resource ID by searching all resources."""
    resources = list(resource_client.resources.list_by_resource_group(resource_group))
    for resource in resources:
        print(f"🔍 Checking resource: {resource.name} ({resource.type})")  # Debugging output
        if resource.name.lower() == resource_name.lower():
            return resource.id
    print(f"⚠️ Resource '{resource_name}' not found in group '{resource_group}'")
    return None



# def get_resource_id(resource_client, resource_group, resource_name, resource_type):
#     """Fetch resource ID based on name and type."""
#     resources = resource_client.resources.list_by_resource_group(resource_group)
#     for resource in resources:
#         print(resource)
#         if resource.name.lower() == resource_name.lower() and resource.type.lower() == resource_type.lower():
#             return resource.id
#     return None  # Return None if not found




# print("All alerts and action groups created successfully!")

def create_action_group(brand_name, monitor_client, resource_group):
    # Create Action Group
    brand_name = brand_name.replace("-Pay-As-You-Go", "").replace("-", "").replace(" ", "")
    action_group_name = f"{brand_name}-DeploymentResource-Token-Alerts-AG"
    action_group_params = {
        "location": "Global",
        "group_short_name": "Alrt80TknsRc",
        "enabled": True,
        "email_receivers": [
            {"name": receiver["name"], "email_address": receiver["email"], "use_common_alert_schema": True}
            for receiver in email_receivers
        ],
        # "sms_receivers": [
        #     {"name": receiver["name"], "phone_number": receiver["phone_number"], "country_code": receiver["country_code"]}
        #     for receiver in sms_receivers
        # ],
    }

    action_group = monitor_client.action_groups.create_or_update(
        resource_group, action_group_name, action_group_params
    )

    print(f"Created Action Group: {action_group_name}")

    return action_group, action_group_name

def create_alerts(resource_group, resource_name, deployment_resource_name, region, monitor_client, resource_client, brand_name, action_group, capacity):
    # Create Alert Rules for each region
    brand_name = brand_name.replace("-Pay-As-You-Go", "").replace("-", "").replace(" ", "")
    alert_rule_name = f"{brand_name}-{region}-DeploymentRes-TokensRateLimit-Reached80"

    # Fetch resource IDs dynamically
    openai_resource_id = get_resource_id(resource_client, resource_group, resource_name)
    print(openai_resource_id)

    if not openai_resource_id:
        raise ValueError(f"❌ Resource ID not found for: {resource_name} in {resource_group}")

    count = (capacity * 1000) * 0.8
    
    alert_rule_params = {
        "location": "Global",
        "description": f"Alert when token usage exceeds 80 per second in {region}",
        "severity": 0,  # 0 = Critical
        "enabled": True,
        "scopes": [openai_resource_id],  # Including OpenAI resource
        "evaluation_frequency": "PT1M",  # Check every 1 min
        "window_size": "PT5M",  # Lookback period 5 min
        "criteria": {
            "odata.type": "Microsoft.Azure.Monitor.MultipleResourceMultipleMetricCriteria",  # FIXED: Added odata.type
            "allOf": [
                {
                    "criterionType": "StaticThresholdCriterion",
                    "name": "TokensRateLimitCheck",
                    "metricNamespace": "Microsoft.CognitiveServices/accounts",
                    "metricName": "AzureOpenAITokenPerSecond",
                    "operator": "GreaterThanOrEqual",
                    "threshold": count,
                    "time_aggregation": "Average",
                    "dimensions": [
                        {
                            "name": "ModelDeploymentName",
                            "operator": "Include",
                            "values": ["*"]  # FIXED: `values` should be a list
                        }
                    ]
                }
            ]
        },
        "actions": [{"action_group_id": action_group.id}]
    }

    alerts.append({
        "name": alert_rule_name,
    })

    # Create or update the alert rule
    alert_rule = monitor_client.metric_alerts.create_or_update(
        resource_group, alert_rule_name, alert_rule_params
    )

    print(f"✅ Created Alert Rule: {alert_rule_name}")


def main():

    config = load_config('openai_resources.json')
    brand_name = config["brand_name"]
    brand_name = clean_brand_name(brand_name)
    subscription_id = config['subscription_id']
    resources = config['resources']

    credential = authenticate()
    resource_client = ResourceManagementClient(credential, subscription_id)
    monitor_client = MonitorManagementClient(credential, subscription_id)

    action_group, action_group_name = create_action_group(brand_name, monitor_client, resources[0]["resource_group"])

    print(json.dumps(resources, indent=4))

    for resource in resources:
        capacity = resource["capacity"]
        create_alerts(resource["resource_group"], resource["resource_name"], resource["deployment_name"], resource["region"], monitor_client, resource_client, brand_name, action_group, capacity)

    output_json = {
        "subscription_id": subscription_id,
        "action_group_name": action_group_name,
        "resource_group_name": resources[0]["resource_group"],
        "alerts": alerts
    }

    with open("alert_resources.json", "w") as f:
        json.dump(output_json, f, indent=4)

    print("Resources written to alert_resources.json")

if __name__ == "__main__":
    main()

