# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from utils import fetch_trivia_question_from_gemini
import os
# from flask_caching import Cache  # Remove Caching
from typing import List, Dict, Any, Optional
import random

app = Flask(__name__)
CORS(app, origins=["https://gemini-quest.netlify.app", "http://localhost:5173"])

# Remove Cache initialization
# cache = Cache(app, config={'CACHE_TYPE': 'simple'})  # Remove Caching

# backend/app.py
@app.route("/api/questions", methods=["POST"])
async def get_questions():
    data = request.get_json()
    category = data.get("category", "General Knowledge")
    num_questions = data.get("num_questions", 10)

    all_questions = await fetch_trivia_question_from_gemini(category, num_questions)
    if not all_questions:
        return jsonify({"error": "Failed to generate questions"}), 500
    return jsonify(all_questions)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)