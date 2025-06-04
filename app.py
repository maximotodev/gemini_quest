# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from utils import fetch_trivia_question_from_gemini
import os
from flask_caching import Cache  # Import Flask-Caching
from typing import List, Dict, Any, Optional
import random  # Import for random question selection

app = Flask(__name__)
CORS(app, origins=["https://gemini-quest.netlify.app", "http://localhost:5173"])
# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'}) # Use 'simple' for development, consider 'redis' for production

# Keep track of used questions (in-memory)
used_questions = {}

@app.route("/api/questions", methods=["POST"])
@cache.cached(timeout=3600, key_prefix='trivia_questions') # Cache for 1 hour
async def get_questions():
    data = request.get_json()
    category = data.get("category", "General Knowledge")
    num_questions = data.get("num_questions", 10)

    # Fetch or retrieve from cache
    cached_questions: Optional[List[Dict[str, Any]]] = cache.get(f'trivia_questions:{category}')
    if cached_questions is None:  # Not in cache
        all_questions = await fetch_trivia_question_from_gemini(category, num_questions * 2) # Fetch more than needed
        if not all_questions:
            return jsonify({"error": "Failed to generate questions"}), 500
        cache.set(f'trivia_questions:{category}', all_questions)  # Cache all questions for category
        cached_questions = all_questions

    # Ensure we have enough unique, unused questions
    available_questions = []
    if category not in used_questions:
        used_questions[category] = set()

    for question in cached_questions:
      if question["question"] not in used_questions[category]:
        available_questions.append(question)

    if len(available_questions) < num_questions:
      # Refetch from Gemini if needed.  Important to avoid running out of questions.
      print(f"Not enough unique questions in cache, refetching for {category}")
      refreshed_questions = await fetch_trivia_question_from_gemini(category, num_questions * 2)
      if refreshed_questions:
        # Add to cache, replacing the old data
        cache.set(f'trivia_questions:{category}', refreshed_questions)
        cached_questions = refreshed_questions
        # Reset available questions
        available_questions = []
        for question in cached_questions:
          if question["question"] not in used_questions[category]:
            available_questions.append(question)


    if len(available_questions) < num_questions:
        print(f"Not enough unique questions available after refetch. Returning what's available. Requested {num_questions}, Available {len(available_questions)} for category {category}")
        selected_questions = available_questions
    else:
        selected_questions = random.sample(available_questions, num_questions) # Randomly select the questions

    # Mark questions as used
    for question in selected_questions:
        used_questions[category].add(question["question"])

    return jsonify(selected_questions)


@app.route("/api/clear_cache", methods=["POST"])  # New endpoint
def clear_cache_route():
    cache.clear()
    global used_questions #Access global variable
    used_questions = {} #reset the used_questions set
    print("Cache cleared and used_questions reset.")
    return jsonify({"message": "Cache cleared"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)