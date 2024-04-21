from flask import Flask, jsonify, request
from flask_cors import CORS
from threading import Thread
import json
import os

from gemini import Gemini

app = Flask(__name__)

# Enable CORS
CORS(app)

# Define the path to the JSON file to store conversation history
CONVERSATION_HISTORY_FILE = "conversation_history.json"

# Check if the conversation history file exists, if not, create an empty dictionary
if not os.path.exists(CONVERSATION_HISTORY_FILE):
    with open(CONVERSATION_HISTORY_FILE, "w") as f:
        json.dump({}, f)

# Load conversation history from the file
with open(CONVERSATION_HISTORY_FILE, "r") as f:
    conversation_history = json.load(f)

# Cookies needed for Gemini API
cookies = {
    # Your cookies here
}

# Initialize the Gemini client with the provided cookies
GeminiClient = Gemini(cookies=cookies)

@app.route('/')
def home():
    return "I'm alive"

@app.route('/gemini', methods=['POST'])
def generate_content():
    if request.is_json:
        data = request.get_json()
        if data is not None and 'prompt' in data:
            prompt = data['prompt']
            uid = data.get('uid')  # Unique identifier for the user
            if prompt.strip():  # Check if prompt is not empty
                # Get conversation history for the user
                user_history = conversation_history.get(uid, [])
                # Concatenate the user's prompts from history
                user_prompts = ' '.join([entry['prompt'] for entry in user_history])
                # Generate content from Gemini using the concatenated prompts
                response = GeminiClient.generate_content(user_prompts + ' ' + prompt)
              
                resJson = response.payload

                message = response.candidates[0].text # Accessing the text from the response
                # Update conversation history for the user
                if uid:
                    if uid not in conversation_history:
                        conversation_history[uid] = []

                    # Add the prompt and response to the conversation history
                    conversation_history[uid].append({'prompt': prompt, 'response': message})

                    # Limit the conversation history to the last few entries (e.g., 5)
                    conversation_history[uid] = conversation_history[uid][-5:]

                    # Save conversation history to the file
                    with open(CONVERSATION_HISTORY_FILE, "w") as f:
                        json.dump(conversation_history, f)

                # Create a conversational response by appending the prompt to the message

                return jsonify(resJson), 200
            else:
                return jsonify({'error': 'Prompt is empty'}), 400
        else:
            return jsonify({'error': 'Invalid JSON data or missing "prompt" field'}), 400
    else:
        return jsonify({'error': 'Unsupported Media Type. Expecting application/json'}), 415

@app.route('/gemini/clear', methods=['POST'])
def clear_history():
    if request.method == 'POST':
        user_id = request.args.get('userid')
        if user_id:
            if user_id in conversation_history:
                # Clear conversation history for the specified user ID
                conversation_history[user_id] = []
                # Save conversation history to the file
                with open(CONVERSATION_HISTORY_FILE, "w") as f:
                    json.dump(conversation_history, f)
                return jsonify({'message': f'Conversation history cleared for user ID: {user_id}'}), 200
            else:
                return jsonify({'error': f'User ID {user_id} not found in conversation history'}), 404
        else:
            return jsonify({'error': 'User ID not provided in query parameter "userid"'}), 400
    else:
        return jsonify({'error': 'Method not allowed. Only POST method is supported for clearing history'}), 405

def run():
    app.run(host='0.0.0.0', port=7210)

if __name__ == '__main__':
    t = Thread(target=run)
    t.start()
