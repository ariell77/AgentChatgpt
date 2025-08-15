import os
from flask import Flask, request, render_template_string
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import OpenAI
import httpx

app = Flask(__name__)

KEYVAULT_NAME = os.environ.get("KEYVAULT_NAME")
OPENAI_SECRET_NAME = os.environ.get("OPENAI_SECRET_NAME")

if not KEYVAULT_NAME or not OPENAI_SECRET_NAME:
    print("⚠ Missing KEYVAULT_NAME or OPENAI_SECRET_NAME in environment variables.")

# Simple chat UI
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>AgenticAI Chat</title>
</head>
<body style="font-family: Arial; max-width: 600px; margin: auto;">
    <h1>AgenticAI Chat</h1>
    <form action="/chat" method="post">
        <input type="text" name="question" style="width: 80%;" placeholder="Ask me anything..." required>
        <button type="submit">Ask</button>
    </form>
    {% if question %}
        <h3>Q: {{ question }}</h3>
        <p><strong>A:</strong> {{ answer }}</p>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/chat", methods=["POST"])
def chat():
    question = request.form.get("question", "")

    try:
        # Authenticate with Managed Identity each time
        credential = DefaultAzureCredential()
        kv_uri = f"https://{KEYVAULT_NAME}.vault.azure.net"
        secret_client = SecretClient(vault_url=kv_uri, credential=credential)

        # Get OpenAI API key from Key Vault
        retrieved_secret = secret_client.get_secret(OPENAI_SECRET_NAME)
        openai_api_key = retrieved_secret.value

        # Build a clean HTTPX client (no proxies) to avoid Azure proxy injection issue
        clean_http_client = httpx.Client(proxies=None)

        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key, http_client=clean_http_client)

        # Send request to OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": question}
            ],
            max_tokens=100
        )

        answer = completion.choices[0].message.content
        return render_template_string(HTML_PAGE, question=question, answer=answer)

    except Exception as e:
        return render_template_string(HTML_PAGE, question=question, answer=f"Error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
