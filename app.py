import os
from flask import Flask
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import OpenAI

app = Flask(__name__)

# Get environment variables set in Azure App Service
KEYVAULT_NAME = os.environ.get("KEYVAULT_NAME")
OPENAI_SECRET_NAME = os.environ.get("OPENAI_SECRET_NAME")

if not KEYVAULT_NAME or not OPENAI_SECRET_NAME:
    raise RuntimeError("Missing KEYVAULT_NAME or OPENAI_SECRET_NAME environment variable")

# Authenticate with Managed Identity
credential = DefaultAzureCredential()

# Connect to Key Vault
KV_URI = f"https://{KEYVAULT_NAME}.vault.azure.net"
secret_client = SecretClient(vault_url=KV_URI, credential=credential)

# Retrieve OpenAI API key from Key Vault
retrieved_secret = secret_client.get_secret(OPENAI_SECRET_NAME)
openai_api_key = retrieved_secret.value

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

@app.route("/")
def home():
    return "Hello from AgenticAI with Key Vault!"

@app.route("/ask/<question>")
def ask_openai(question):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": question}
            ],
            max_tokens=100
        )
        answer = completion.choices[0].message.content
        return f"Q: {question}<br>A: {answer}"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    # Use Azure's assigned port
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
