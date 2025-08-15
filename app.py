import os
from flask import Flask, request, render_template_string
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from openai import OpenAI

app = Flask(__name__)

# Environment variables
KEYVAULT_NAME = os.environ.get("KEYVAULT_NAME")
OPENAI_SECRET_NAME = os.environ.get("OPENAI_SECRET_NAME")
UAMI_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")  # Only set if using UAMI

if not KEYVAULT_NAME or not OPENAI_SECRET_NAME:
    print("⚠ Missing KEYVAULT_NAME or OPENAI_SECRET_NAME in environment variables.")

# HTML chat interface
HTML_PAGE = """
<!doctype html>
<html>
<head>
    <title>AgenticAI Demo</title>
</head>
<body style="font-family: Arial; max-width: 600px; margin: auto;">
    <h2>🤖 AgenticAI - LLM + Azure Key Vault</h2>
    <form method="POST">
        <input name="question" style="width:80%;" placeholder="Ask me something... (or 'get secret SecretName')" autofocus>
        <button type="submit">Send</button>
    </form>
    {% if answer %}
    <div style="margin-top:20px;">
        <b>Q:</b> {{ question }}<br>
        <b>A:</b> {{ answer|safe }}
    </div>
    {% endif %}
</body>
</html>
"""

def get_identity_info():
    """Return whether using System Managed Identity or UAMI."""
    if UAMI_CLIENT_ID:
        return f"User Assigned Managed Identity (Client ID: {UAMI_CLIENT_ID})"
    else:
        return "System Assigned Managed Identity"

def get_kv_secret(secret_name):
    """Retrieve a secret from Azure Key Vault."""
    if UAMI_CLIENT_ID:
        credential = ManagedIdentityCredential(client_id=UAMI_CLIENT_ID)
    else:
        credential = DefaultAzureCredential()

    kv_uri = f"https://{KEYVAULT_NAME}.vault.azure.net"
    secret_client = SecretClient(vault_url=kv_uri, credential=credential)
    retrieved_secret = secret_client.get_secret(secret_name)
    return retrieved_secret.value

@app.route("/", methods=["GET", "POST"])
def chat():
    answer = None
    question = None

    if request.method == "POST":
        question = request.form.get("question", "").strip()

        try:
            identity_info = get_identity_info()

            if question.lower().startswith("get secret"):
                # Extract the secret name from input
                parts = question.split(" ", 2)
                if len(parts) >= 3:
                    secret_name = parts[2]
                    secret_value = get_kv_secret(secret_name)
                    answer = f"Secret '<b>{secret_name}</b>': {secret_value}<br><i>Accessed via {identity_info}</i>"
                else:
                    answer = "Please specify the secret name. Example: get secret MySecret"
            else:
                # Get OpenAI API key from Key Vault
                openai_api_key = get_kv_secret(OPENAI_SECRET_NAME)

                # Ask OpenAI
                client = OpenAI(api_key=openai_api_key)
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a concise assistant."},
                        {"role": "user", "content": question}
                    ],
                    max_tokens=100
                )
                llm_answer = completion.choices[0].message.content
                answer = f"{llm_answer}<br><i>LLM query executed via {identity_info}</i>"

        except Exception as e:
            answer = f"Error: {e}"

    return render_template_string(HTML_PAGE, answer=answer, question=question)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
