# app.py
from flask import Flask, request, jsonify
from azure.identity import DefaultAzureCredential
from azure.ai.openai import OpenAIClient
import os

app = Flask(__name__)

# Load Azure OpenAI environment config
endpoint = os.environ.get("OPENAI_ENDPOINT")
deployment_name = os.environ.get("DEPLOYMENT_NAME")

# Initialize Azure OpenAI client
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
                {"role": "system", "content": "You are a helpful AI agent."},
                {"role": "user", "content": instruction}
            ]
        )

        decision = response.choices[0].message.content

        return jsonify({
            "instruction": instruction,
            "agent_decision": decision
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
