from flask import Flask, request, jsonify
from azure.identity import DefaultAzureCredential
from azure.ai.openai import OpenAIClient  # ✅ from the preview package
import os

app = Flask(__name__)

endpoint = os.environ.get("OPENAI_ENDPOINT")
deployment_name = os.environ.get("DEPLOYMENT_NAME")

credential = DefaultAzureCredential()
client = OpenAIClient(endpoint=endpoint, credential=credential)

@app.route("/")
def home():
    return "App is running!"

@app.route("/agent", methods=["POST"])
def agent():
    try:
        data = request.get_json()
        instruction = data.get("instruction", "").strip()

        if not instruction:
            return jsonify({"error": "Missing instruction"}), 400

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful cloud agent."},
                {"role": "user", "content": instruction}
            ]
        )

        result = response.choices[0].message.content

        return jsonify({
            "instruction": instruction,
            "agent_decision": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
