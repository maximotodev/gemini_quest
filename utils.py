# backend/utils.py
import os
from dotenv import load_dotenv
from google.generativeai import GenerativeModel, configure, GenerationConfig
from typing import Dict, Any, Optional, List
import json
import re
import traceback  # Import for printing tracebacks
import asyncio  # Import for async retry

load_dotenv()

def get_gemini_api_key() -> str:
    """Loads the Gemini API key from the environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    return api_key

def parse_gemini_response(response_text: str) -> Optional[List[Dict[str, Any]]]:  # Return a list
    """Parses the Gemini API JSON response, handling potential errors and cleaning up."""
    # Correctly handle code fences (```json ... ```)
    fence_regex = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(fence_regex, response_text, re.DOTALL)
    if match:
        response_text = match.group(1).strip()

    try:
        questions = json.loads(response_text)
        if not isinstance(questions, list):
            print(f"Invalid JSON format: expected a list, got: {type(questions)}")
            return None

        # Validate each question
        valid_questions = []
        for question in questions:
            if (
                isinstance(question, dict) and
                "question" in question and
                "options" in question and
                isinstance(question["options"], list) and
                len(question["options"]) == 4 and
                "correctAnswer" in question
            ):
              # Trim whitespace from correctAnswer for more robust comparison
              correct_answer = question["correctAnswer"].strip()
              # Check if the correct answer is *contained within* any option (case-insensitive)
              found_match = False
              for option in question["options"]:
                  if correct_answer.lower() in option.strip().lower():
                      found_match = True
                      question["correctAnswer"] = option.strip()  # Use the actual option
                      break # Stop searching once a match is found
              if found_match:
                  valid_questions.append(question)
              else:
                  print(f"Invalid question format: correctAnswer '{correct_answer}' not found (or not close enough) in options: {question['options']}")
            else:
                print(f"Invalid question format: {question}")
        if len(valid_questions) == len(questions):  # Only return if all questions are valid
          return valid_questions
        else:
          print(f"Only {len(valid_questions)} out of {len(questions)} questions were valid.")
          return None
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}\nRaw response: {response_text}")
        print(traceback.format_exc())  # Print full traceback
        return None
    except Exception as e:
        print(f"Unexpected error during JSON parsing: {e}\nRaw response: {response_text}")
        print(traceback.format_exc())  # Print full traceback
        return None

async def fetch_trivia_question_from_gemini(category: str, num_questions: int = 10, max_retries: int = 3) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches multiple trivia questions from the Gemini API with retries.
    """
    for attempt in range(max_retries):
        try:
            api_key = get_gemini_api_key()
            configure(api_key=api_key)
            model = GenerativeModel(model_name="gemini-2.5-flash-preview-04-17")

            prompt = f"""
                You are a fun and engaging trivia game host for "Gemini Quest".
                Generate {num_questions} trivia questions for the category: "{category}".
                Provide each question, 4 multiple-choice options, and clearly indicate the correct answer.
                The value for "correctAnswer" MUST EXACTLY MATCH one of the strings in the "options" array, *without any leading or trailing whitespace*.
                Return your response as a single, valid JSON object.  The JSON structure should be an array of question objects.  Each question object should have the following structure:
                [
                    {{
                      "question": "The actual trivia question text?",
                      "options": ["Option A Text", "Option B Text", "Option C Text", "Option D Text"],
                      "correctAnswer": "The text of the correct option"
                    }},
                    {{
                      "question": "Another question?",
                      "options": ["Option A", "Option B", "Option C", "Option D"],
                      "correctAnswer": "Option B"
                    }},
                    // ... more questions
                ]
                Ensure the options are distinct and plausible. The questions should be engaging and fit the category.
                For "Brain Teasers", make it a riddle or short puzzle.
                Ensure the entire response is ONLY the JSON array, without any surrounding text or markdown.
                """
            generation_config = GenerationConfig(temperature=0.7)
            response = model.generate_content(prompt, generation_config=generation_config)
            parsed_response = parse_gemini_response(response.text)

            if parsed_response:
                return parsed_response
            else:
                print(f"Failed to parse response (attempt {attempt + 1}/{max_retries}): {response.text}")
        except Exception as e:
            print(f"Error fetching trivia questions (attempt {attempt + 1}/{max_retries}): {e}")
            print(traceback.format_exc())  # Print the full traceback
        await asyncio.sleep(1)  # Wait before retrying (e.g., 1 second)
    print("Max retries reached.  Failed to fetch questions.")
    return None