import os
from flask import Flask, request, session, redirect, url_for, render_template_string
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "replace_this_with_random_secret")

KEYVAULT_NAME = os.environ.get("KEYVAULT_NAME")
OPENAI_SECRET_NAME = os.environ.get("OPENAI_SECRET_NAME")

if not KEYVAULT_NAME or not OPENAI_SECRET_NAME:
    print("⚠ Missing KEYVAULT_NAME or OPENAI_SECRET_NAME in environment variables.")

# HTML template for the chat interface
CHAT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AgenticAI Chat</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; background: #f5f5f5; }
        h1 { text-align: center; }
        .chat-box { background: white; padding: 20px; border-radius: 10px; min-height: 400px; display: flex; flex-direction: column; }
        .message { margin: 8px 0; padding: 10px; border-radius: 8px; max-width: 70%; }
        .user { background: #DCF8C6; align-self: flex-end; }
        .assistant { background: #E8E8E8; align-self: flex-start; }
        form { display: flex; margin-top: 15px; }
        input[type=text] { flex: 1; padding: 10px; font-size: 16px; border-radius: 8px; border: 1px solid #ccc; }
        input[type=submit] { padding: 10px 20px; font-size: 16px; margin-left: 5px; border-radius: 8px; background: #0078D7; color: white; border: none; cursor: pointer; }
        input[type=submit]:hover { background: #005A9E; }
    </style>
</head>
<body>
    <h1>AgenticAI Chat</h1>
    <div class="chat-box">
        {% for role, content in chat_history %}
            <div class="message {{ 'user' if role == 'user' else 'assistant' }}">
                <strong>{{ 'You' if role == 'user' else 'AgenticAI' }}:</strong> {{ content }}
            </div>
        {% endfor %}
    </div>
    <form method="POST">
        <input type="text" name="question" placeholder="Type your message..." required>
        <input type="submit" value="Send">
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def chat():
    if "chat_history" not in session:
        session["chat_history"] = []

    if request.method == "POST":
        question = request.form.get("question")
        if question:
            # Add user message to history
            session["chat_history"].append(("user", question))

            try:
                # Authenticate with Managed Identity
                credential = DefaultAzureCredential()
                kv_uri = f"https://{KEYVAULT_NAME}.vault.azure.net"
                secret_client = SecretClient(vault_url=kv_uri, credential=credential)

                # Get OpenAI API key from Key Vault
                retrieved_secret = secret_client.get_secret(OPENAI_SECRET_NAME)
                openai_api_key = retrieved_secret.value

                # Initialize OpenAI client
                client = OpenAI(api_key=openai_api_key)

                # Send conversation history to OpenAI
                messages = [{"role": role, "content": content} for role, content in session["chat_history"]]
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=200
                )
                answer = completion.choices[0].message.content

                # Add assistant reply to history
                session["chat_history"].append(("assistant", answer))

            except Exception as e:
                session["chat_history"].append(("assistant", f"Error: {e}"))

            # Save session
            session.modified = True

        return redirect(url_for("chat"))

    return render_template_string(CHAT_TEMPLATE, chat_history=session["chat_history"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
