# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS # Нужен для работы с вашего HTML-сайта
from google import genai
from google.genai.errors import APIError

app = Flask(__name__)
# Разрешаем CORS, чтобы ваш HTML-сайт мог обращаться к этому API
CORS(app) 

# Ключ Gemini берется из переменных окружения Render
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = None

if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Ошибка инициализации клиента Gemini: {e}")

# Простая in-memory реализация памяти чата
# В реальном приложении лучше использовать базу данных (Redis/Postgres)
# Ключ: chat_id (генерируется случайным образом), Значение: объект Chat Session
chat_sessions = {}

# Генерируем простой ID для сессии (для сайта)
def get_session_id(request):
    # В простом примере используем случайный ID, который должен передавать сайт
    # В более сложном случае можно использовать куки или JWT
    return request.headers.get('X-Session-ID', 'default_session')


@app.route('/ask_gemini', methods=['POST'])
def ask_gemini():
    if not client:
        return jsonify({"error": "Gemini client is not initialized"}), 503

    session_id = get_session_id(request)
    prompt = request.json.get('prompt')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # Создаем или получаем сессию чата
    if session_id not in chat_sessions:
        try:
            chat_sessions[session_id] = client.chats.create(model="gemini-2.5-flash")
        except Exception as e:
            return jsonify({"error": f"Failed to create chat session: {str(e)}"}), 500
    
    current_chat = chat_sessions[session_id]

    try:
        # Отправляем сообщение в сессию
        response = current_chat.send_message(prompt)
        return jsonify({"response": response.text})
        
    except APIError as e:
        # Улучшенная обработка ошибок
        error_msg = f"API Error: {e.args[0]}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return jsonify({"error": "An unexpected server error occurred."}), 500

if __name__ == '__main__':
    # Render использует порт, указанный в переменной окружения PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
