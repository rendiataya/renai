import os
import json
import re
from flask import Flask, render_template, request, jsonify
from groq import Groq
from google import genai
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

def load_models_from_json():
    try:
        with open('models.json', 'r') as file:
            data = json.load(file)
        return data['models']
    except Exception as e:
        print(f"Gagal membaca models.json: {e}")
        return []

# Endpoint "/" untuk menu awal website
# dan mengload model dari json
@app.route('/')
def home():
    models = load_models_from_json()
    return render_template('index.html', models=models)

# Endpoint "/chat" sebagai logic untuk respon bot
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    selected_model_id = request.json.get('model_id')
    
    models = load_models_from_json()
    groq_model_id = "qwen/qwen3.6-27b"
    provider = "groq"

    # Load model dari json ke dalam bot
    for m in models:
        if m['id'] == selected_model_id:
            groq_model_id = m['groq_id']
            provider = m.get('provider', 'groq')
            break
            
    try:
        # Penggunaan API Gemini jika user memilih model gemini
        if provider == "google":
            chat_session = gemini_client.chats.create(model=groq_model_id)
            response = chat_session.send_message(user_message)
            ai_response = response.text
        else:
        # Penggunaan API Groq jika user memilih model dari groq
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": user_message}],
                model=groq_model_id,
                max_completion_tokens=800,
                reasoning_format="hidden"
            )
            ai_response = chat_completion.choices[0].message.content

        # Menghilangkan fase berfikir dalam model qwen3.6
        cleaned_response = re.sub(r'<\/?think>|.*?<\/think>', '', ai_response, flags=re.DOTALL | re.IGNORECASE).strip()
        
        return jsonify({"success": True, "reply": cleaned_response})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    # Membaca port dinamis dari server produksi, default ke 5000 jika dijalankan lokal
    port = int(os.environ.get("PORT", 5000))
    # Menonaktifkan debug=True demi keamanan di server produksi
    app.run(host="0.0.0.0", port=port)
