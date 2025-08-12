from flask import Flask, request, jsonify
from azure.identity import DefaultAzureCredential
from azure.openai import OpenAIClient
import os

app = Flask(__name__)

# Load environment variables from App Settings
endpoint = os.environ["OPENAI_ENDPOINT"]
deployment_name = os.environ["DEPLOYMENT_NAME"]

# Use system-assigned managed identity for auth
credential = DefaultAzureCredential()
client = OpenAIClient(endpoint=endpoint, credential=credential)

@app.route("/")
def home():
    return "App is running"

@app.route("/agent", methods=["POST"])
def agent():
    data = request.get_json()
    instruction = data.get("instruction", "")

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a helpful cloud agent that makes decisions."},
            {"role": "user", "content": instruction}
        ]
    )

    ai_response = response.choices[0].message.content

    return jsonify({
        "instruction": instruction,
        "agent_decision": ai_response
    })
