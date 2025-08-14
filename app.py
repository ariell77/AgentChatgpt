from flask import Flask, request, jsonify
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import openai
import os

app = Flask(__name__)

# Load secrets from environment (GitHub secrets)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KEY_VAULT_URL = os.getenv("AZURE_KEY_VAULT_URL")
SECRET_NAME = os.getenv("SECRET_NAME")

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Use Azure Default Credential (for system or user-managed identity)
credential = DefaultAzureCredential()
kv_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "")

    try:
        # Step 1: Get secret from Azure Key Vault
        secret = kv_client.get_secret(SECRET_NAME)
        secret_value = secret.value

        # Step 2: Ask OpenAI using the secret as context
        messages = [
            {"role": "system", "content": f"You are a cloud security assistant. The following is a Key Vault secret: {SECRET_NAME} = {secret_value}."},
            {"role": "user", "content": question}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        reply = response['choices'][0]['message']['content']
        return jsonify({"response": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health():
    return "✅ Agent is live and ready!", 200
