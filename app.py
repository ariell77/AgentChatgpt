import os
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# Configure OpenAI with Azure settings
openai.api_type = "azure"
openai.api_base = os.environ["AZURE_OPENAI_ENDPOINT"]          # e.g. https://al-openai-resource.openai.azure.com/
openai.api_version = "2024-02-15-preview"                       # Confirm your API version
openai.api_key = os.environ["AZURE_OPENAI_API_KEY"]            # Set in GitHub Secrets

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_input = request.json.get("message", "")
        if not user_input:
            return jsonify({"error": "No input provided"}), 400

        response = openai.ChatCompletion.create(
            engine=os.environ["AZURE_OPENAI_DEPLOYMENT"],       # e.g. gpt-4-deployment-name
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ]
        )
        reply = response["choices"][0]["message"]["content"]
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
