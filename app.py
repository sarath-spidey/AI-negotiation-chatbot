import os
from flask import Flask, request, jsonify, render_template
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env (Override system variables if they exist)
load_dotenv(override=True)

app = Flask(__name__)

# Initialize client if API key is present
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

# Global chat history to maintain context
chat_history = []

@app.route("/")
def home():
    # Clear history on refresh to start new negotiation
    global chat_history
    chat_history = []
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    if not client:
        return jsonify({"error": "GROQ_API_KEY is not configured on Render. Please add it to your Environment Variables."})
    
    global chat_history
    data = request.get_json()
    user_message = data.get("message", "")

    # Append user message to history
    chat_history.append({"role": "user", "content": user_message})

    try:
        # Define the system prompt once
        system_prompt = {
            "role": "system",
            "content": (
                "You are a professional business negotiator. "
                "Your goal is to negotiate deals effectively for your client. "
                "CRITICAL RULES: "
                "1. Only refer to information provided in the CURRENT conversation history. "
                "2. DO NOT invent previous discussions, prices, or terms that haven't happened yet. "
                "3. Stay focused on the product being discussed (e.g., if mangoes, don't switch to software). "
                "4. Keep responses under 3 sentences. Be professional and firm."
            )
        }

        # Combine system prompt with recent history (last 10 messages)
        engine_messages = [system_prompt] + chat_history[-10:]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=engine_messages
        )

        ai_reply = response.choices[0].message.content

        # Append AI response to history
        chat_history.append({"role": "assistant", "content": ai_reply})

        return jsonify({"reply": ai_reply})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
