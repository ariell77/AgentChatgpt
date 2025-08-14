import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello from AgenticAI!"

if __name__ == "__main__":
    # Azure sets the PORT env variable (usually 8000)
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
