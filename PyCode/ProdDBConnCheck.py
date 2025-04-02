import argparse
import mysql.connector
from AzureGenAIResourceRead import *
from rdsConnectAzure import *
import json

def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def db_execution(brand_name, subscription_id, resource_group_name, user_email, PA_DB_CONFIG, MAIN_DB_CONFIG):
    # Connect to databases
    try:
        pa_db_conn = mysql.connector.connect(**PA_DB_CONFIG)
        main_db_conn = mysql.connector.connect(**MAIN_DB_CONFIG)

        pa_cursor = pa_db_conn.cursor(dictionary=True)
        main_cursor = main_db_conn.cursor(dictionary=True)

        ### Step 1: Fetch brand_id from main_db
        # brand_name = "Chase"
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

        pa_cursor.execute("SELECT * FROM call_analyzer_configuration WHERE brand_id = %s", (brand_id,))
        details = pa_cursor.fetchall()
        pa_db_conn.commit()

        print(f"Details of brand id : {brand_id} in call_analyzer_configuration - {details}")

        if not details:
            raise Exception(f"{brand_id} not found in call_analyzer_configuration table")
    
        ### Step 2: Insert into bot_db service_resources

        # query_variables = getQueryVariables(subscription_id, resource_group_name)

        # for key, value in query_variables.items():
        #
        #     resource_name = key
        #     endpoint = value["endpoint"]
        #     key = value["keys"]
        #     region = value["region"].lower()
        #     type = value["type"]
        #
        #     insert_service_resource = """
        #     INSERT INTO service_resources (brand_id, service, resource_type, resource, resource_id, region, endpoint, `key`)
        #     VALUES (%s, 'Azure', %s, %s, %s, %s, %s, %s)
        #     """
        #
        #     bot_cursor.execute(insert_service_resource, (brand_id, type, resource_name, resource_name, region, endpoint, key))
        #     bot_db_conn.commit()
        #     print("✅ Inserted into service_resources.")
        #
        #     ### Step 3: Fetch newly inserted resource ID
        #     bot_cursor.execute(
        #         "SELECT id FROM service_resources WHERE brand_id = %s AND resource = %s",
        #         (brand_id, resource_name)
        #     )
        #     resource = bot_cursor.fetchone()
        #
        #     if not resource:
        #         raise Exception("❌ Error: Resource ID not found after insert.")
        #
        #     resource_id = resource["id"]
        #     print(f"✅ Fetched Resource ID: {resource_id}")
        #
        #     ### Step 4: Insert into resource_model
        #     insert_resource_model = """
        #     INSERT INTO resource_model (model_type, model_name, resource_id, inactive, created_by, updated_by)
        #     VALUES ('Deployment', 'gpt-4o', %s, 0, %s, %s)
        #     """
        #
        #     bot_cursor.execute(insert_resource_model, (resource_id, user_id, user_id))
        #     bot_db_conn.commit()
        #     print("✅ Inserted into resource_model.")

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

    env = "prod"
    #main_secret, bot_secret = get_secret(env)

    parser = argparse.ArgumentParser(description="Azure GenAI Resource DB Inserions")

    parser.add_argument('--env_m', required=True, help='Environemt e.g., beta, prod, etc')
    parser.add_argument('--env_p', required=True, help='Environemt e.g., pa, prod, etc')
    parser.add_argument("--user_email", required=True, help="User email")

    args = parser.parse_args()
    
    env_m = args.env_m
    env_p = args.env_p
    user_email = args.user_email
    
    pa_secret, main_secret = get_secret(env_p)

    #config = load_config('openai_resources.json')


    # Database connection details

    brand_name = "Amica"
        # "Wolters Kluwer" # as per brand table
    subscription_id = ""
        # "fee8cb00-2601-4963-a4f9-793ed834e3ab"
    #resource_group_name = config["resources"][0]["resource_group"]
    resource_group_name = ""
    

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

    PA_DB_CONFIG = None

    if env_p == "pa":

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

    # Function to execute queries and return results
    # def execute_query(cursor, query, params=None):
    #     cursor.execute(query, params or ())
    #     return cursor.fetchall()

    db_execution(brand_name, subscription_id, resource_group_name, user_email, PA_DB_CONFIG, MAIN_DB_CONFIG)


if __name__ == "__main__":
    main()
