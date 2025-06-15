import os
from dotenv import load_dotenv
from google.generativeai import GenerativeModel, configure, GenerationConfig
from typing import Dict, Any, Optional, List
import json
import re
import traceback
import asyncio
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_gemini_api_key() -> str:
    """Loads the Gemini API key from the environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY not found in environment variables.")
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    return api_key

def escape_json_string(text: str) -> str:
    """Escapes special characters in a string for safe JSON embedding."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

def parse_gemini_response(response_text: str) -> Optional[List[Dict[str, Any]]]:
    """Parses the Gemini API text response (non-JSON)"""
    questions = []
    try:
        lines = response_text.strip().split('\n')
        for line in lines:
            parts = line.split('|')
            if len(parts) == 4:
                question_text, options_str, correct_answer, explanation = parts
                options = [opt.strip() for opt in options_str.split(',')]

                if len(options) == 4 and correct_answer.strip() in options:
                    questions.append({
                        "question": escape_json_string(question_text.strip()),
                        "options": [escape_json_string(opt) for opt in options],
                        "correctAnswer": escape_json_string(correct_answer.strip()),
                        "explanation": escape_json_string(explanation.strip())
                    })
                else:
                    logging.warning(f"Invalid question format: {line}")
            else:
                logging.warning(f"Skipping invalid line: {line}")

        return questions if questions else None  # Return None if no valid questions

    except Exception as e:
        logging.error(f"Error parsing response: {e}")
        logging.error(traceback.format_exc())
        return None

async def fetch_trivia_question_from_gemini(category: str, num_questions: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches multiple trivia questions from the Gemini API.
    """
    try:
        api_key = get_gemini_api_key()
        configure(api_key=api_key)
        model = GenerativeModel(model_name="gemini-2.5-flash-preview-04-17") # double check this model name is still valid

        prompt = f"""
    You are a fun and engaging trivia game host for "Gemini Quest".
    Generate {num_questions} trivia questions for the category: "{category}".

    For each question, provide the following information, separated by the '|' character:
    1. The trivia question text.
    2. Four distinct and plausible multiple-choice options, separated by commas. Ensure no option contains a comma within it.
    3. The correct answer (which MUST EXACTLY MATCH one of the options).
    4. A brief explanation (under 50 words) for the correct answer.

    Return each question on a new line.  Do NOT include any surrounding text, JSON, or markdown.
    Ensure there are exactly four options, and the correct answer is one of them.
    If you cannot provide the information in the specified format, skip the question.

    Example format:
    Question text|Option A,Option B,Option C,Option D|Correct Answer|Explanation text

    Ensure the options are distinct and plausible. The questions should be engaging and fit the category.
    For "Brain Teasers", make it a riddle or short puzzle.
    """
        generation_config = GenerationConfig(temperature=0.7)
        response = model.generate_content(prompt, generation_config=generation_config)
        parsed_response = parse_gemini_response(response.text)

        if parsed_response:
            # Return exactly the number of questions requested
            return parsed_response
        else:
            logging.warning(f"Failed to parse response: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error fetching trivia questions: {e}")
        logging.error(traceback.format_exc())
        return None