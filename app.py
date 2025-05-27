# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from utils import fetch_trivia_question_from_gemini
import os

app = Flask(__name__)
CORS(app, origins="http://localhost:5173")  # Replace with your frontend URL

@app.route("/api/question", methods=["POST"])
async def get_question():
    try:
        data = request.get_json()
        category = data.get("category", "General Knowledge")  # Default category

        question_data = await fetch_trivia_question_from_gemini(category)

        if question_data:
            return jsonify(question_data)
        else:
            return jsonify({"error": "Failed to generate a question"}), 500
    except Exception as e:
        print(f"Error in /api/question: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port) #host specified for render deploy