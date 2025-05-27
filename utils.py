import os
from dotenv import load_dotenv
from google.generativeai import GenerativeModel, configure
from google.generativeai import GenerationConfig
from typing import Dict, Any, Optional

load_dotenv()

def get_gemini_api_key() -> str:
    """Loads the Gemini API key from the environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    return api_key

def parse_gemini_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parses the Gemini API JSON response, handling potential errors and cleaning up.
    """
    import json
    json_str = response_text.strip()
    # Correctly handle code fences (```json ... ```)
    fence_regex = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    import re
    match = re.search(fence_regex, json_str, re.DOTALL)
    if match:
        json_str = match.group(1).strip()

    # Clean up problematic Unicode characters
    json_str = json_str.replace(u"\uE000", "")  # Example: removing a specific private use character
    json_str = json_str.replace(u"\uF121", "")  #Removing a specific private use character

    try:
        parsed_data = json.loads(json_str)
        if (
            isinstance(parsed_data, dict) and
            "question" in parsed_data and
            "options" in parsed_data and
            isinstance(parsed_data["options"], list) and
            len(parsed_data["options"]) == 4 and
            "correctAnswer" in parsed_data and
            parsed_data["correctAnswer"] in parsed_data["options"]
        ):
            return parsed_data
        else:
            print(f"Invalid JSON format: {parsed_data}") # Debugging
            return None
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}\nRaw response: {response_text}\nProcessed string: {json_str}")  # Debugging
        return None
    except Exception as e:
        print(f"Unexpected error during JSON parsing: {e}\nRaw response: {response_text}") # Debugging
        return None


async def fetch_trivia_question_from_gemini(category: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a trivia question from the Gemini API.
    """
    try:
        api_key = get_gemini_api_key()
        configure(api_key=api_key) #Configure must occur before the model is created

        model = GenerativeModel(model_name="gemini-2.5-flash-preview-04-17")
        prompt = f"""
            You are a fun and engaging trivia game host for "Gemini Quest".
            Generate a trivia question for the category: "{category}".
            Provide the question, 4 multiple-choice options, and clearly indicate the correct answer.
            The value for "correctAnswer" MUST EXACTLY MATCH one of the strings in the "options" array.
            Return your response as a single, valid JSON object with the following structure:
            {{
              "question": "The actual trivia question text?",
              "options": ["Option A Text", "Option B Text", "Option C Text", "Option D Text"],
              "correctAnswer": "The text of the correct option"
            }}
            Ensure the options are distinct and plausible. The question should be engaging and fit the category.
            For "Brain Teasers", make it a riddle or short puzzle.
            Ensure the entire response is ONLY the JSON object, without any surrounding text or markdown.
            """
        generation_config = GenerationConfig(temperature=0.7)
        response =  model.generate_content(prompt, generation_config=generation_config)
        parsed_response = parse_gemini_response(response.text)

        if parsed_response:
            return parsed_response
        else:
            print(f"Failed to parse response: {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching trivia question: {e}")
        return None