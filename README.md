1. **Setup and Installation:**
   Clone the repository: git clone https://github.com/your_username/gemini_quest-backend.git
2. **Create a virtual environment:** python3 -m venv venv

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the `backend` directory and add your Gemini API key:

   ```    3. Activate the virtual environment:
   - On Linux/macOS: `source venv/bin/activate`
   - On Windows: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables:
   GEMINI_API_KEY=YOUR_ACTUAL_API_KEY
   ```

## Running the Backend

```bash
python app.py
```

The backend will run on `http://127.0.0.1:5000` by
   - Create a `.env` file in the backend directory.
   - Add your Gemini API key to the `.env` file: `GEMINI_API_KEY=YOUR_ACTUAL_API_KEY`
6. Run the app: `python app.py`

## API End default.

## API Endpoints

*   `/api/question (POST)`:  Fetches a trivia question.  Send a JSON payload with a `category` field (e.g., `{"category": "Science"}`).

## Deployment

This backend is designed to be deployedpoints

* `/api/question (POST)`:
    - Expects a JSON payload with a `category` field (e.g., `"category": "Science"`).
    - Returns a JSON object containing the trivia question, options, and correct answer.

## Dependencies

See ` on platforms like Render or Heroku.  See the deployment documentation for your chosen platform for specific instructions.


## Contributing

If you'd like to contribute to this project, please open an issue or submit a pull request.


## License

[Specify your license here, e.g.,requirements.txt` for a list of project dependencies.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

[Choose a license and include it here]
```
