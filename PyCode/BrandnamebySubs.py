import mysql.connector
# from AzureGenAIResourceRead import *
from rdsConnectAzure import *
import json

def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def db_execution(subscription_id, user_email, MAIN_DB_CONFIG):
    # Connect to databases

    try:
        brand_name = None
        main_db_conn = mysql.connector.connect(**MAIN_DB_CONFIG)

        main_cursor = main_db_conn.cursor(dictionary=True)

        # Step 1: Fetch brand_id from main_db

        main_cursor.execute("SELECT json_unquote(json_extract(settings_json, '$.name')) as 'brand_name', brand_id from brand_settings where inactive_settings = 0 and json_unquote(json_extract(settings_json, '$.azure_subscription_id')) = %s", (subscription_id,))
        brand = main_cursor.fetchone()
        main_db_conn.commit()

        brand_name = brand['brand_name']
        brand_id = brand['brand_id']

        if not brand:
            raise Exception(f"Brand '{brand_name}' not found in main_db.")

        print(f"✅ Brand ID for '{brand_name}': {brand_id}")

        # Fetch the user_id
        main_cursor.execute("SELECT id FROM user WHERE email = %s", (user_email,))
        user = main_cursor.fetchone()

        user_id = user["id"]
        print(f"User ID for '{user_email}': {user_id}")
        if not user:
            raise Exception(f"Email '{user_email}' not found in main_db.")



    except Exception as e:
        print(f"❌ Error: {e}")
        return brand_name

    finally:
        # Close connections
        if main_cursor:
            main_cursor.close()
        if main_db_conn:
            main_db_conn.close()
        print("🔄 Database connections closed.")

        return brand_name


def getBrandNamebySubscription(env, subscription_id, user_email):

    main_secret, bot_secret = get_secret(env)

    print(main_secret)

    MAIN_DB_CONFIG = {
        "host": main_secret["host"],
        "user": main_secret["username"],
        "password": main_secret["password"],
        "database": main_secret["dbname"]
    }

    brand_name = db_execution(subscription_id, user_email, MAIN_DB_CONFIG)

    return brand_name


# brand_name = getBrandNamebySubscription("prod", "aeb00795-1157-4ec0-a15d-ecdfcc65999f", "adityap@zenarate.com")
#
# print(brand_name)
