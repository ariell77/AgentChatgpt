from flask import Flask, jsonify
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
from azure.ai.openai import OpenAIClient
import os

app = Flask(__name__)

# Environment variables
key_vault_url = os.environ["KEY_VAULT_URL"]
storage_account_url = os.environ["STORAGE_ACCOUNT_URL"]
container_name = os.environ.get("STORAGE_CONTAINER", "demo")
endpoint = os.environ["OPENAI_ENDPOINT"]
deployment_name = os.environ["DEPLOYMENT_NAME"]

# Auth + clients
credential = DefaultAzureCredential()
kv_client = SecretClient(vault_url=key_vault_url, credential=credential)
blob_service = BlobServiceClient(account_url=storage_account_url, credential=credential)
openai_client = OpenAIClient(endpoint=endpoint, credential=credential)

@app.route("/")
def index():
    return "App is running!"

@app.route("/kv")
def get_secret():
    try:
        secret = kv_client.get_secret("my-secret")
        return jsonify({"secret": secret.value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/containers")
def list_containers():
    try:
        containers = [c["name"] for c in blob_service.list_containers()]
        return jsonify({"containers": containers})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/agent")
def run_agent():
    try:
        response = openai_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in one sentence."}
            ],
            max_tokens=20
        )
        return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/diag")
def diag():
    try:
        test = openai_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "ping"},
                {"role": "user", "content": "say hi"}
            ],
            max_tokens=8,
        )
        return {
            "ok": True,
            "endpoint": endpoint,
            "deployment": deployment_name,
            "preview": test.choices[0].message.content
        }
    except Exception as e:
        return {
            "ok": False,
            "endpoint": endpoint,
            "deployment": deployment_name,
            "error": str(e)
        }, 500
