import json
import argparse
import os
import mysql.connector
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from AzureGenAIResourceRead import *
from rdsConnectAzure import *

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

def db_execution(brand_name, subscription_id, resource_group_name, user_email, PA_DB_CONFIG, MAIN_DB_CONFIG, client_id, client_secret, tenant_id, env_m):
    # Connect to databases
    try:
        pa_db_conn = mysql.connector.connect(**PA_DB_CONFIG)
        main_db_conn = mysql.connector.connect(**MAIN_DB_CONFIG)

        pa_cursor = pa_db_conn.cursor(dictionary=True)
        main_cursor = main_db_conn.cursor(dictionary=True)

        query_variables = getQueryVariables(subscription_id, resource_group_name, client_id, client_secret, tenant_id,
                                            env_m)

        ### Step 1: Fetch brand_id from main_db
        #brand_name = "Chase"
        main_cursor.execute("SELECT id FROM brand WHERE name = %s", (brand_name,))
        brand = main_cursor.fetchone()
        main_db_conn.commit()

        if not brand:
            raise Exception(f"Brand '{brand_name}' not found in main_db.")

        brand_id = brand["id"]
        print(f"✅ Brand ID for '{brand_name}': {brand_id}")

        # Fetch the user_id
        # user_email = "adityap@zenarate.com"
        main_cursor.execute("SELECT id FROM user WHERE email = %s", (user_email,))
        user = main_cursor.fetchone()

        user_id = user["id"]
        print(f"User ID for '{user_email}': {user_id}")
        if not user:
            raise Exception(f"Email '{user_email}' not found in main_db.")


        # query_variables = getQueryVariables(subscription_id, resource_group_name, client_id, client_secret, tenant_id, env_m)

        variables = {}
        count = 1

        for key, value in query_variables.items():

            resource_name = key
            endpoint = value["endpoint"]
            key = value["keys"]
            region = value["region"].lower()
            type = value["type"]


            if "Evaluation" in resource_name:
                variables[f"Evaluation_url_{count}"] = endpoint
                variables[f"Evaluation_key_{count}"] = key
                count += 1


        print(json.dumps(variables, indent=2))

        json_config = json.dumps({
            "api_base": variables["Evaluation_url_1"],
            "api_key": variables["Evaluation_key_1"],
            "api_version": "2023-07-01-preview",
            "engine": "gpt-4o",
            "system_prompt": "You are an expert skills evaluator on a call transcript.",
            "deployment_options": [
                {
                    "api_base": variables["Evaluation_url_1"],
                    "api_key": variables["Evaluation_key_1"],
                    "api_version": "2023-07-01-preview",
                    "engine": "gpt-4o",
                    "system_prompt": "You are an expert skills evaluator on a call transcript.",
                    "start_range": 0,
                    "end_range": 49
                },
                {
                    "api_base": variables["Evaluation_url_2"],
                    "api_key": variables["Evaluation_key_2"],
                    "api_version": "2023-07-01-preview",
                    "engine": "gpt-4o",
                    "system_prompt": "You are an expert skills evaluator on a call transcript.",
                    "start_range": 49,
                    "end_range": 101
                }
            ]
        }, separators=(",", ":"))

        # SQL query with placeholders
        insert_ca_configs = '''
            INSERT INTO `call_analyzer_configuration`
            (`configuration_type`, `configuration_value`, `extra_parameter`, `brand_id`, `inactive`, `created_at`, `created_by`, `updated_at`, `updated_by`)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s, NOW(), %s);
        '''

        # Execute the query safely
        pa_cursor.execute(insert_ca_configs,
                          ('gpt_story_evaluation_config', 'general', json_config, brand_id, 0, 8413, 8413))
        pa_db_conn.commit()
        print("Data inserted successfully.")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Close connections
        if main_cursor:
            main_cursor.close()
        if pa_cursor:
            pa_cursor.close()
        if main_db_conn:
            main_db_conn.close()
        if pa_db_conn:
            pa_db_conn.close()
        print("🔄 Database connections closed.")


def main():

    parser = argparse.ArgumentParser(description="Azure GenAI Resource DB Inserions")

    parser.add_argument('--env', required=True, help='Environemt e.g., beta, prod, etc')
    parser.add_argument('--email', required=True, help='User email')
    parser.add_argument('--env_m', required=True, help='Environemt e.g., beta, prod, etc')
    
    args = parser.parse_args()
    
    env = args.env
    user_email = args.email
    env_m = args.env_m

    pa_secret, main_secret = get_secret(env)

    client_id = os.getenv("ARM_CLIENT_ID")
    client_secret = os.getenv("ARM_CLIENT_SECRET")
    tenant_id = os.getenv("ARM_TENANT_ID")

    # Database connection details

    config = load_config('openai_resources.json')
    subscription_id = config['subscription_id']
    resources = config['resources']
    brand_name = config['brand_name']
    resource_group_name = resources[0]["resource_group"]

    # subscription_id = ""
    # resources = ""
    # brand_name = "Prime Marketing"
    # resource_group_name = ""

    # MAIN_DB_CONFIG = {
    #     "host": "localhost",
    #     "user": "root",
    #     "password": "password",
    #     "database": "PoC"
    # }
    #
    # PA_DB_CONFIG = {
    #     "host": "localhost",
    #     "user": "root",
    #     "password": "password",
    #     "database": "PoC"
    # }

    PA_DB_CONFIG = None

    if env == "pa":

        PA_DB_CONFIG = {
            "host": pa_secret["host"],
            "user": pa_secret["username"],
            "password": pa_secret["password"],
            "database": pa_secret["dbname"]
        }

    MAIN_DB_CONFIG = {
        "host": main_secret["host"],
        "user": main_secret["username"],
        "password": main_secret["password"],
        "database": main_secret["dbname"]
    }

    #print(PA_DB_CONFIG)
    #print(MAIN_DB_CONFIG)

    db_execution(brand_name, subscription_id, resource_group_name, user_email, PA_DB_CONFIG, MAIN_DB_CONFIG, client_id, client_secret, tenant_id, env_m)


if __name__ == "__main__":
    main()
