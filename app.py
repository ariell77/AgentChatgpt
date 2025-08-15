import os
from flask import Flask, request, render_template_string
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import OpenAI

app = Flask(__name__)

# Environment variables
KEYVAULT_NAME = os.environ.get("KEYVAULT_NAME")
OPENAI_SECRET_NAME = os.environ.get("OPENAI_SECRET_NAME")

if not KEYVAULT_NAME or not OPENAI_SECRET_NAME:
    print("⚠ Missing KEYVAULT_NAME or OPENAI_SECRET_NAME in environment variables.")

# HTML chat interface
HTML_PAGE = """
<!doctype html>
<html>
<head>
    <title>AgenticAI Demo</title>
    <style>
        .banner {
            padding: 10px;
            margin-bottom: 15px;
            font-weight: bold;
            text-align: center;
            border-radius: 5px;
        }
        .warning {
            background-color: #ffdddd;
            color: #b30000;
            border: 1px solid #b30000;
        }
        .safe {
            background-color: #ddffdd;
            color: #006600;
            border: 1px solid #006600;
        }
    </style>
</head>
<body style="font-family: Arial; max-width: 600px; margin: auto;">
    <h2>🤖 AgenticAI - LLM + Azure Key Vault</h2>
    
    {% if banner %}
    <div class="banner {{ banner_class }}">{{ banner }}</div>
    {% endif %}
    
    <form method="POST">
        <input name="question" style="width:80%;" placeholder="Ask me something... (or 'get secret SecretName')" autofocus>
        <select name="temperature">
            <option value="0.2" {% if temperature == '0.2' %}selected{% endif %}>Safe (0.2)</option>
            <option value="0.7" {% if temperature == '0.7' %}selected{% endif %}>Balanced (0.7)</option>
            <option value="1.5" {% if temperature == '1.5' %}selected{% endif %}>Risky (1.5)</option>
        </select>
        <button type="submit">Send</button>
    </form>
    
    {% if answer %}
    <div style="margin-top:20px;">
        <b>Q:</b> {{ question }}<br>
        <b>Temperature:</b> {{ temperature }}<br>
        <b>A:</b> {{ answer }}
    </div>
    {% endif %}
</body>
</html>
"""

def get_kv_secret(secret_name):
    """Retrieve a secret from Azure Key Vault."""
    credential = DefaultAzureCredential()
    kv_uri = f"https://{KEYVAULT_NAME}.vault.azure.net"
    secret_client = SecretClient(vault_url=kv_uri, credential=credential)
    retrieved_secret = secret_client.get_secret(secret_name)
    return retrieved_secret.value

@app.route("/", methods=["GET", "POST"])
def chat():
    answer = None
    question = None
    temperature = "0.7"  # default
    banner = None
    banner_class = ""

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        temperature = request.form.get("temperature", "0.7")

        # Set banner for risky/safe modes
        if temperature == "1.5":
            banner = "⚠ Risky mode active: High hallucination risk!"
            banner_class = "warning"
        elif temperature == "0.2":
            banner = "✅ Safe mode active: Low hallucination risk."
            banner_class = "safe"

        try:
            if question.lower().startswith("get secret"):
                parts = question.split(" ", 2)
                if len(parts) >= 3:
                    secret_name = parts[2]
                    secret_value = get_kv_secret(secret_name)
                    answer = f"Secret '{secret_name}': {secret_value}"
                else:
                    answer = "Please specify the secret name. Example: get secret MySecret"
            else:
                openai_api_key = get_kv_secret(OPENAI_SECRET_NAME)
                client = OpenAI(api_key=openai_api_key)
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=float(temperature),
                    messages=[
                        {"role": "system", "content": "You are a concise assistant."},
                        {"role": "user", "content": question}
                    ],
                    max_tokens=100
                )
                answer = completion.choices[0].message.content

        except Exception as e:
            answer = f"Error: {e}"

    return render_template_string(
        HTML_PAGE,
        answer=answer,
        question=question,
        temperature=temperature,
        banner=banner,
        banner_class=banner_class
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
