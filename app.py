from flask import Flask, jsonify, request
from flask_cors import CORS
from utils import fetch_trivia_question_from_gemini
import os
from typing import List, Dict, Any, Optional
import logging

app = Flask(__name__)
CORS(app, origins=["https://gemini-quest.netlify.app", "http://localhost:5173"])

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route("/api/questions", methods=["POST"])
async def get_questions():
    """
    Fetches trivia questions from the Gemini API based on the provided category and number of questions.

    Returns:
        A JSON response containing the trivia questions or an error message.
    """
    try:
        data = request.get_json()
        if not data:
            logging.error("No JSON data received in the request.")
            return jsonify({"error": "Invalid request.  Please provide JSON data."}), 400

        category = data.get("category", "General Knowledge")
        num_questions = data.get("num_questions", 10)

        logging.info(f"Fetching {num_questions} questions for category: {category}")
        all_questions = await fetch_trivia_question_from_gemini(category, num_questions)

        if all_questions:
            logging.info(f"Successfully fetched {len(all_questions)} questions.")
            return jsonify(all_questions)
        else:
            logging.warning("Failed to generate questions from Gemini API.")
            return jsonify({"error": "Failed to generate questions.  Please try again or select a different category."}, 500)  # More user-friendly message

    except Exception as e:
        logging.exception("An unexpected error occurred while processing the request.") # Log the full exception
        return jsonify({"error": f"An unexpected server error occurred: {str(e)}"}, 500)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)