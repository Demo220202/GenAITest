import json
import argparse
import mysql.connector
from mysql.connector import Error
from rdsConnectAzure import *

brand_ids = []

names = [
    ('Danielle', 'female', 'Danielle', 'Polly', None, None, 0),
    ('Gregory', 'male', 'Gregory', 'Polly', None, None, 0),
    ('Joanna', 'female', 'Joanna', 'Polly', None, None, 0),
    ('Ruth', 'female', 'Ruth', 'Polly', None, None, 0),
    ('Matthew', 'male', 'Matthew', 'Polly', None, None, 0),
    ('Stephen', 'male', 'Stephen', 'Polly', None, None, 0),
    ('arcas', 'male', 'aura-arcas-en', 'Deepgram', None, '/apis/api/v1/advance-authoring/get-avatar-url/arcas.jpg', 0),
    ('asteria', 'female', 'aura-asteria-en', 'Deepgram', None,
     '/apis/api/v1/advance-authoring/get-avatar-url/asteria.jpg', 0),
    ('athena', 'female', 'aura-athena-en', 'Deepgram', None, '/apis/api/v1/advance-authoring/get-avatar-url/athena.jpg',
     0),
    ('helios', 'male', 'aura-helios-en', 'Deepgram', None, '/apis/api/v1/advance-authoring/get-avatar-url/helios.jpg',
     0),
    ('hera', 'female', 'aura-hera-en', 'Deepgram', None, '/apis/api/v1/advance-authoring/get-avatar-url/hera.jpg', 0),
    ('luna', 'female', 'aura-luna-en', 'Deepgram', None, '/apis/api/v1/advance-authoring/get-avatar-url/luna.jpg', 0),
    ('orion', 'male', 'aura-orion-en', 'Deepgram', None, '/apis/api/v1/advance-authoring/get-avatar-url/orion.jpg', 0),
    (
    'perseus', 'male', 'aura-perseus-en', 'Deepgram', None, '/apis/api/v1/advance-authoring/get-avatar-url/perseus.jpg',
    0),
    ('stella', 'female', 'aura-stella-en', 'Deepgram', None, '/apis/api/v1/advance-authoring/get-avatar-url/stella.jpg',
     0),
    ('zeus', 'male', 'aura-zeus-en', 'Deepgram', None, '/apis/api/v1/advance-authoring/get-avatar-url/zeus.jpg', 0),
    ('Wyatt', 'male', 'YXpFCvM1S3JbWEJhoskW', 'Elevenlabs', None, None, 0),
    ('Cole', 'male', 'Tw2LVqLUUWkxqrCfFOpw', 'Elevenlabs', None, None, 0),
    ('Jessica Anne Bogart', 'female', 'g6xIsTj2HwM6VR4iXFCw', 'Elevenlabs', None, None, 0),
    ('Cassidy', 'female', '56AoDkrOh6qfVPDXZ7Pt', 'Elevenlabs', None, None, 0),
    ('Dakota H', 'female', 'P7x743VjyZEOihNNygQ9', 'Elevenlabs', None, None, 0),
    ('Jerry', 'male', 'XA2bIQ92TabjGbpO2xRr', 'Elevenlabs', None, None, 0),
    ('Oliver', 'male', 'L1aJrPa7pLJEyYlh3Ilq', 'Elevenlabs', None, None, 0),
    ('Jeff', 'male', 'gs0tAILXbY5DNrJrsM6F', 'Elevenlabs', None, None, 0),
    ('Amelia', 'female', 'ZF6FPAbjXT4488VcRRnw', 'Elevenlabs', None, None, 0),
    ('Beth', 'female', '8N2ng9i2uiUWqstgmWlH', 'Elevenlabs', None, None, 0),
    ('Lily Wolff', 'female', 'qBDvhofpxp92JgXJxDjB', 'Elevenlabs', None, None, 0),
    ('Grandpa Spuds Oxley', 'male', 'NOpBlnGInO9m6vDvFkFC', 'Elevenlabs', None, None, 0),
    ('{Spanish} - Nico', 'male', 'iXa2i9eYvgmNMRQRCwqO', 'Elevenlabs', None, None, 0),
    ('{Spanish} - Ninoska', 'female', 'gt8UWQljAEAt5YLqG4LW', 'Elevenlabs', None, None, 0),
    ('{French} - Martin Dupont', 'male', 'a5n9pJUnAhX4fn7lx3uo', 'Elevenlabs', None, None, 0),
    ('{French} - Emilie Lacroix', 'female', 'qMfbtjrTDTlGtBy52G6E', 'Elevenlabs', None, None, 0),
    ('{Mandarin} - Martin Li', 'male', 'WuLq5z7nEcrhppO0ZQJw', 'Elevenlabs', None, None, 0),
    ('{Mandarin} - Liang', 'female', 'FjfxJryh105iTLL4ktHB', 'Elevenlabs', None, None, 0),
]

def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Azure GenAI Resource DB Inserions")

    parser.add_argument('--env_m', required=True, help='Environemt e.g., pa, prod, etc')
    # parser.add_argument('--brands', required=True, help='Comma-separated list of brands')

    args = parser.parse_args()

    env = args.env_m
    # brand_names = args.brands.split(',')

    # brand_name = brand_names[0]  # As per DB

    config = load_config('openai_resources.json')
    brand_name = config['brand_name']

    # env = "prod"
    main_secret, bot_secret = get_secret(env)


    # MAIN_DB_CONFIG = {
    #     "host": "localhost",
    #     "user": "root",
    #     "password": "password",
    #     "database": "PoC"
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

    try:
        conn = mysql.connector.connect(
            **MAIN_DB_CONFIG,
        )
        cursor = conn.cursor(dictionary=True)

        # Fetching brand_id based on brand_name

        cursor.execute("SELECT id FROM brand WHERE name = %s", (brand_name,))
        brand = cursor.fetchone()
        conn.commit()

        if not brand:
            raise Exception(f"Brand '{brand_name}' not found in main_db.")

        brand_id = brand["id"]
        print(f"✅ Brand ID for '{brand_name}': {brand_id}")

        brand_ids.append(brand_id)

        # Building insert query
        insert_query = """
        INSERT INTO advance_story_voices 
        (brand_id, name, gender, voiceId, service, audio_url, avatar_url, inactive)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        all_values = []
        for brand_id in brand_ids:
            for name, gender, voiceId, service, audio_url, avatar_url, inactive in names:
                all_values.append((brand_id, name, gender, voiceId, service, audio_url, avatar_url, inactive))

        # Preview the query
        preview_rows = [
            f"({brand_id}, '{name}', '{gender}', '{voiceId}', '{service}', '{audio_url}', '{avatar_url}', {inactive})"
            for brand_id, name, gender, voiceId, service, audio_url, avatar_url, inactive in all_values
        ]
        print("Preview of generated INSERT statement:")
        print("INSERT INTO advance_story_voices (brand_id, name, gender, voiceId, service, audio_url, avatar_url, inactive) VALUES")
        print(",\n".join(preview_rows) + ";\n")

        # Execute
        cursor.executemany(insert_query, all_values)
        conn.commit()
        print(f"✅ Inserted {cursor.rowcount} rows successfully!")

    except Error as e:
        print(f"❌ Error occurred: {e}")
        if conn:
            conn.rollback()  # rollback if anything goes wrong
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
