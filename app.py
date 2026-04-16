import os
from flask import Flask, request, jsonify, render_template
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env (Override system variables if they exist)
load_dotenv(override=True)

app = Flask(__name__)

def get_groq_client():
    """Helper to initialize client only when needed."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

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
    client = get_groq_client()
    if not client:
        # Diagnostic: check all environment variable keys for anything similar
        all_keys = os.environ.keys()
        groq_related_keys = [k for k in all_keys if "GROQ" in k.upper()]
        
        print(f"DEBUG: GROQ_API_KEY not found. Related keys found in environment: {groq_related_keys}")
        
        raw_key = os.getenv("GROQ_API_KEY")
        return jsonify({
            "error": "GROQ_API_KEY is missing.",
            "diagnostics": {
                "detected_groq_keys": groq_related_keys,
                "found_exact_match": raw_key is not None
            }
        })
    
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
