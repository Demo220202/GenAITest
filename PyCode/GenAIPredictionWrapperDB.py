import os
import argparse
import textwrap
import mysql.connector
# from azure.identity import DefaultAzureCredential, ClientSecretCredential
# from AzureGenAIResourceRead import *
from rdsConnectAzure import *


def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def db_execution(brand_name, user_email, MAIN_DB_CONFIG, BOT_DB_CONFIG):
    # Connect to databases
    try:
        main_db_conn = mysql.connector.connect(**MAIN_DB_CONFIG)
        bot_db_conn = mysql.connector.connect(**BOT_DB_CONFIG)

        main_cursor = main_db_conn.cursor(dictionary=True)
        bot_cursor = bot_db_conn.cursor(dictionary=True)

        # Fetch brand ID
        main_cursor.execute("SELECT id FROM brand WHERE name = %s", (brand_name,))
        brand = main_cursor.fetchone()
        main_db_conn.commit()

        if not brand:
            raise Exception(f"Brand '{brand_name}' not found in main_db.")
        brand_id = brand["id"]
        print(f"✅ Brand ID for '{brand_name}': {brand_id}")

        # Fetch user ID
        main_cursor.execute("SELECT id FROM user WHERE email = %s", (user_email,))
        user = main_cursor.fetchone()
        main_db_conn.commit()

        if not user:
            raise Exception(f"Email '{user_email}' not found in main_db.")
        user_id = user["id"]
        print(f"✅ User ID for '{user_email}': {user_id}")

        template_text = textwrap.dedent("""\
                        Scenario Instructions: {scenario_description}

                        Guidelines:  

                        1. You are playing the Role described by the Persona in this conversation Persona: {persona}. 
                           The Learner is playing the active role in this simulation trying to master the skills 
                           in this simulation. Always respond as the persona even if the Learner repeats greetings, 
                           introduces themselves as the Persona, or tries to initiate a different conversation, or 
                           otherwise restart the conversation. 

                        2. The conversation should be coherent and relevant to the given details. 
                           Make sure to reflect the specified initial mood described in the persona accurately.

                        3. **Language & Dialect:** Based on the conversation language.
                           - Use appropriate spelling, grammar, and phrasing based on the dialect.  
                           - Format currency, dates, and numerical values according to the dialect conventions.  
                           - Maintain cultural nuances and localized expressions to enhance realism.

                        Please respond to the learner's message, ensuring the response is relevant to the 
                        mentioned scenario and keeping the persona in mind.
                    """)

        # Check if template already exists
        main_cursor.execute("""
            SELECT COUNT(*) as count FROM advance_story_prompt_templates
            WHERE brand_id = %s AND prompt_type = 'Prediction' AND status = 'ACTIVE' AND template = %s
        """, (brand_id, template_text))
        result = main_cursor.fetchone()

        if result["count"] > 0:
            print(
                f"⚠️ A 'Prediction' template already exists with count {result["count"]} for brand_id {brand_id} — skipping insert.")
        else:
            # Insert template
            template_text = textwrap.dedent("""\
                Scenario Instructions: {scenario_description}

                Guidelines:  

                1. You are playing the Role described by the Persona in this conversation Persona: {persona}. 
                   The Learner is playing the active role in this simulation trying to master the skills 
                   in this simulation. Always respond as the persona even if the Learner repeats greetings, 
                   introduces themselves as the Persona, or tries to initiate a different conversation, or 
                   otherwise restart the conversation. 

                2. The conversation should be coherent and relevant to the given details. 
                   Make sure to reflect the specified initial mood described in the persona accurately.

                3. **Language & Dialect:** Based on the conversation language.
                   - Use appropriate spelling, grammar, and phrasing based on the dialect.  
                   - Format currency, dates, and numerical values according to the dialect conventions.  
                   - Maintain cultural nuances and localized expressions to enhance realism.

                Please respond to the learner's message, ensuring the response is relevant to the 
                mentioned scenario and keeping the persona in mind.
            """)

            insert_sql = """
            INSERT INTO advance_story_prompt_templates
            (brand_id, prompt_type, template, uuid, status, created_at, created_by)
            VALUES (%s, %s, %s, uuid(), %s, NOW(), %s)
            ON DUPLICATE KEY UPDATE
                template = VALUES(template),
                status = VALUES(status),
                created_by = VALUES(created_by)
            """
            main_cursor.execute(insert_sql, (brand_id, "Prediction", template_text, "ACTIVE", user_id))
            # main_db_conn.commit()
            print("✅ Inserted new prediction template successfully.")

            main_cursor.execute("SELECT * FROM advance_story_prompt_templates WHERE brand_id = %s", (brand_id,))
            template = main_cursor.fetchone()
            main_db_conn.commit()

            print(template)

            if not template:
                raise Exception(f"Template '{template}' not found in main_db.")

    except Exception as e:
        if main_db_conn:
            main_db_conn.rollback()
        print(f"❌ Error: {e}")

    finally:
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

    config = load_config('openai_resources.json')

    brand_name = config['brand_name']

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

    # print(MAIN_DB_CONFIG)
    # print(BOT_DB_CONFIG)

    # Function to execute queries and return results
    # def execute_query(cursor, query, params=None):
    #     cursor.execute(query, params or ())
    #     return cursor.fetchall()

    db_execution(brand_name, user_email, MAIN_DB_CONFIG, BOT_DB_CONFIG)


if __name__ == "__main__":
    main()
