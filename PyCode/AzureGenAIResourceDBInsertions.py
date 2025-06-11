import os
import argparse
import mysql.connector
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from AzureGenAIResourceRead import *
from rdsConnectAzure import *

def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def db_execution(brand_name, subscription_id, resource_group_name, user_email, MAIN_DB_CONFIG, BOT_DB_CONFIG, client_id, client_secret, tenant_id, env, dep_model_name):
    # Connect to databases
    try:
        main_db_conn = mysql.connector.connect(**MAIN_DB_CONFIG)
        bot_db_conn = mysql.connector.connect(**BOT_DB_CONFIG)

        main_cursor = main_db_conn.cursor(dictionary=True)
        bot_cursor = bot_db_conn.cursor(dictionary=True)

        query_variables = getQueryVariables(subscription_id, resource_group_name, client_id, client_secret, tenant_id,
                                            env)

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

        ### Step 2: Insert into bot_db service_resources

        # query_variables = getQueryVariables(subscription_id, resource_group_name, client_id, client_secret, tenant_id, env)

        for key, value in query_variables.items():

            resource_name = key
            endpoint = value["endpoint"]
            key = value["keys"]
            region = value["region"].lower()
            type = value["type"]

            insert_service_resource = """
            INSERT INTO service_resources (brand_id, service, resource_type, resource, resource_id, region, endpoint, `key`)
            VALUES (%s, 'Azure', %s, %s, %s, %s, %s, %s)
            """

            bot_cursor.execute(insert_service_resource, (brand_id, type, resource_name, resource_name, region, endpoint, key))
            bot_db_conn.commit()
            print("✅ Inserted into service_resources.")

            ### Step 3: Fetch newly inserted resource ID
            bot_cursor.execute(
                "SELECT id FROM service_resources WHERE brand_id = %s AND resource = %s",
                (brand_id, resource_name)
            )
            resource = bot_cursor.fetchone()

            if not resource:
                raise Exception("❌ Error: Resource ID not found after insert.")

            resource_id = resource["id"]
            print(f"✅ Fetched Resource ID: {resource_id}")

            ### Step 4: Insert into resource_model
            insert_resource_model = """
            INSERT INTO resource_model (model_type, model_name, resource_id, inactive, created_by, updated_by)
            VALUES ('Deployment', %s, %s, 0, %s, %s)
            """

            bot_cursor.execute(insert_resource_model, (dep_model_name, resource_id, user_id, user_id))
            bot_db_conn.commit()
            print("✅ Inserted into resource_model.")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Close connections
        if main_cursor:
            main_cursor.close()
        if bot_cursor:
            bot_cursor.close()
        if main_db_conn:
            main_db_conn.close()
        if bot_db_conn:
            bot_db_conn.close()
        print("🔄 Database connections closed.")


def main():

    parser = argparse.ArgumentParser(description="Azure GenAI Resource DB Inserions")

    parser.add_argument('--env_m', required=True, help='Environemt e.g., pa, prod, etc')
    parser.add_argument("--user_email", required=True, help="User email")

    args = parser.parse_args()

    env_m = args.env_m
    user_email = args.user_email
    
    main_secret, bot_secret = get_secret(env_m)

    client_id = os.getenv("ARM_CLIENT_ID")
    client_secret = os.getenv("ARM_CLIENT_SECRET")
    tenant_id = os.getenv("ARM_TENANT_ID")

    config = load_config('openai_resources.json')
    subscription_id = config['subscription_id']
    resources = config['resources']
    brand_name = config['brand_name']
    resource_group_name = resources[0]["resource_group"]

    dep_model_name = resources[0]["deployment_name"]

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
    # BOT_DB_CONFIG = {
    #     "host": "localhost",
    #     "user": "root",
    #     "password": "password",
    #     "database": "PoC_bot"
    # }

    MAIN_DB_CONFIG = {
        "host": main_secret["host"],
        "user": main_secret["username"],
        "password": main_secret["password"],
        "database": main_secret["dbname"]
    }

    BOT_DB_CONFIG = {
        "host": bot_secret["host"],
        "user": bot_secret["username"],
        "password": bot_secret["password"],
        "database": bot_secret["dbname"]
    }

    #print(MAIN_DB_CONFIG)
    #print(BOT_DB_CONFIG)

    # Function to execute queries and return results
    # def execute_query(cursor, query, params=None):
    #     cursor.execute(query, params or ())
    #     return cursor.fetchall()

    db_execution(brand_name, subscription_id, resource_group_name, user_email, MAIN_DB_CONFIG, BOT_DB_CONFIG, client_id, client_secret, tenant_id, env_m, dep_model_name)


if __name__ == "__main__":
    main()
