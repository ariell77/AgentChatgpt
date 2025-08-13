import os
from flask import Flask, request, jsonify
from azure.identity import DefaultAzureCredential
from azure.ai.openai import OpenAIClient

app = Flask(__name__)

# Set up OpenAI client
client = OpenAIClient(
    endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    credential=DefaultAzureCredential()
)

@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.json.get("prompt", "")
    deployment = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
    response = client.get_chat_completions(
        deployment_id=deployment,
        messages=[{"role": "user", "content": prompt}]
    )
    return jsonify({"response": response.choices[0].message.content})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
