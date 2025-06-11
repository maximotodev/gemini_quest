import os
from dotenv import load_dotenv
from google.generativeai import GenerativeModel, configure, GenerationConfig
from typing import Dict, Any, Optional, List
import json
import re
import traceback
import asyncio

load_dotenv()

def get_gemini_api_key() -> str:
    """Loads the Gemini API key from the environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    return api_key

def escape_json_string(text: str) -> str:
    """Escapes special characters in a string for safe JSON embedding."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

def clean_gemini_json(json_string: str) -> str:
    """Aggressively cleans up Gemini's JSON output using regex."""

    # Remove code fences
    json_string = re.sub(r"```(?:json)?\s*\n?(.*?)\n?\s*```", r"\1", json_string, flags=re.DOTALL)

    # Find JSON boundaries
    start_match = re.search(r"\[", json_string)
    end_match = re.search(r"\]", json_string[::-1])  # Find last bracket from the reversed string
    if not start_match or not end_match:
        print("Could not find JSON start or end markers.")
        return ""

    start_index = start_match.start()
    end_index = len(json_string) - end_match.start()  # Adjust for reversed string

    json_string = json_string[start_index:end_index]

    # Remove invalid key-value pairs inserted by Gemini (NEW!)
    json_string = re.sub(r'\s*"\w+":\s*\[.*?\]\s*}', '}', json_string)

    # Remove any text before a closing brace '}' (general cleanup)
    json_string = re.sub(r'\s*[^"}\n]+\s*}', '}', json_string)

    # Remove trailing commas
    json_string = re.sub(r',\s*}', '}', json_string)
    json_string = re.sub(r'}\s*,', '},', json_string)

    # Remove json} or other similar endings
    json_string = re.sub(r'\s*json}', '}', json_string)

    return json_string

def parse_gemini_response(response_text: str) -> Optional[List[Dict[str, Any]]]:
    """Parses the Gemini API JSON response, handling potential errors and cleaning up."""
    try:
        cleaned_json = clean_gemini_json(response_text)
        if not cleaned_json:
            print("Could not clean JSON.")
            return None

        questions = json.loads(cleaned_json)

        if not isinstance(questions, list):
            print(f"Invalid JSON format: expected a list, got: {type(questions)}")
            return None

        valid_questions = []
        for question in questions:
            if (isinstance(question, dict) and
                "question" in question and isinstance(question["question"], str) and
                "options" in question and isinstance(question["options"], list) and len(question["options"]) == 4 and all(isinstance(opt, str) for opt in question["options"]) and
                "correctAnswer" in question and isinstance(question["correctAnswer"], str) and
                "explanation" in question and isinstance(question["explanation"], str)):

                correct_answer = question["correctAnswer"].strip()
                if correct_answer in [opt.strip() for opt in question["options"]]:
                     valid_questions.append({
                         "question": escape_json_string(question["question"]),
                         "options": [escape_json_string(opt) for opt in question["options"]],
                         "correctAnswer": escape_json_string(question["correctAnswer"]),
                         "explanation": escape_json_string(question["explanation"])
                      })
                else:
                    print(f"Invalid question format: correctAnswer '{correct_answer}' not found exactly in options: {question['options']}")
            else:
                print(f"Invalid question format: {question}")

        if len(valid_questions) > 0:
            return valid_questions
        else:
            print("No valid questions found after validation.")
            return None

    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}\nRaw response: {response_text}")
        print(traceback.format_exc())
        return None
    except Exception as e:
        print(f"Unexpected error during JSON parsing: {e}\nRaw response: {response_text}")
        print(traceback.format_exc())
        return None

async def fetch_trivia_question_from_gemini(category: str, num_questions: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches multiple trivia questions from the Gemini API.
    """
    try:
        api_key = get_gemini_api_key()
        configure(api_key=api_key)
        model = GenerativeModel(model_name="gemini-2.5-flash-preview-04-17")

        prompt = f"""
            You are a fun and engaging trivia game host for "Gemini Quest".
            Generate {num_questions} trivia questions for the category: "{category}".
            Provide each question, 4 multiple-choice options, the clearly indicated correct answer, *and a brief explanation (under 50 words) for the correct answer*.
            The value for "correctAnswer" MUST EXACTLY MATCH one of the strings in the "options" array, *without any leading or trailing whitespace*.
            Return your response as a single, valid JSON object.  The JSON structure should be an array of question objects.  Each question object should have the following structure:
            [
                {{
                  "question": "The actual trivia question text?",
                  "options": ["Option A Text", "Option B Text", "Option C Text", "Option D Text"],
                  "correctAnswer": "The text of the correct option",
                  "explanation": "Brief explanation of why the answer is correct."
                }},
                {{
                  "question": "Another question?",
                  "options": ["Option A", "Option B", "Option C Text", "Option D Text"],
                  "correctAnswer": "Option B Text",
                  "explanation": "Brief explanation of why the answer is correct."
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
            # Return exactly the number of questions requested
            return parsed_response
        else:
            print(f"Failed to parse response: {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching trivia questions: {e}")
        return None