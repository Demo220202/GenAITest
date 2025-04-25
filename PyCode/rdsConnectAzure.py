import boto3
import json
from botocore.exceptions import ClientError

def fetch_secret(secret_name, region_name):
    """
    Fetch a secret from AWS Secrets Manager
    :param secret_name
    :param region_name
    :return: The secret value as a dictionary.
    """

    session = boto3.Session(region_name=region_name)
    client = session.client('secretsmanager')

    try:

        response = client.get_secret_value(SecretId=secret_name)

        # Check if the secret is stored as plain text or JSON
        if "SecretString" in response:
            secret = response["SecretString"]
        else:
            # Decode binary secrets
            secret = response["SecretBinary"].decode("utf-8")

        # Convert to a dictionary if the secret is JSON
        try:
            return json.loads(secret)
        except json.JSONDecodeError:
            return secret

    except ClientError as e:
        print(f"Error fetching secret: {e}")
        return None

def get_secret(env):

    if env == "prod":
        secret_name_main = "zenarate/prod/db/main"
        secret_name_bot = "zenarate/prod/db/bot"
        region_name = "us-west-1"
        return fetch_secret(secret_name_main, region_name), fetch_secret(secret_name_bot, region_name)
    elif env == "beta":
        secret_name_main = "zenarate/beta/db/main/root"
        secret_name_bot = "zenarate/beta/db/bot/root"
        region_name = "us-west-1"
        return fetch_secret(secret_name_main, region_name), fetch_secret(secret_name_bot, region_name)
    elif env == "pa":
        secret_name_pa = "zenarate/prod-ca/db/coach/root"
        secret_name_main = "zenarate/prod/db/main/root"
        region_name_pa = "us-west-2"
        region_name_main = "us-west-1"
        return fetch_secret(secret_name_pa, region_name_pa), fetch_secret(secret_name_main, region_name_main)
