import json
from azure.identity import DefaultAzureCredential
from azure.mgmt.monitor import MonitorManagementClient

def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def delete_alert_rule(resource_group, alert_rule_name, monitor_client):
    try:
        monitor_client.metric_alerts.delete(resource_group, alert_rule_name)
        print(f"Deleted alert rule: {alert_rule_name}")
    except Exception as e:
        print(f"Failed to delete alert rule {alert_rule_name}: {e}")

def delete_action_group(resource_group, action_group_name, monitor_client):
    try:
        monitor_client.action_groups.delete(resource_group, action_group_name)
        print(f"Deleted action group: {action_group_name}")
    except Exception as e:
        print(f"Failed to delete action group {action_group_name}: {e}")

def main():

    config = load_config('alert_resources.json')
    subscription_id = config['subscription_id']
    resource_group = config['resource_group_name']
    action_group_name = config['action_group_name']
    resources = config['alerts']

    credential = DefaultAzureCredential()
    monitor_client = MonitorManagementClient(credential, subscription_id)

    for resource in resources:
        delete_alert_rule(resource_group, resource["name"], monitor_client)

    delete_action_group(resource_group, action_group_name, monitor_client)

if __name__ == "__main__":
    main()
