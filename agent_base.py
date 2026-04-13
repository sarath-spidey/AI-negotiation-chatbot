import time
import requests
import random
import re


# --------------------------------------------------------------------------
# GROQ LLAMA MODEL CLIENT
# --------------------------------------------------------------------------

class GroqLlama:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def complete(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        r = requests.post(self.url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


# --------------------------------------------------------------------------
# HELPER – EXTRACT PRICE
# --------------------------------------------------------------------------

def extract_price(text):
    if not text:
        return None
    nums = re.findall(r"\d+", text.replace(",", ""))
    return int(nums[-1]) if nums else None


# --------------------------------------------------------------------------
# BASE NEGOTIATION AGENT
# --------------------------------------------------------------------------

class NegotiationAgent:
    def __init__(self, name, role, limit, model: GroqLlama):
        self.name = name
        self.role = role
        self.limit = limit
        self.model = model
        self.history = []
        self.start_time = time.time()

    def persona_prompt(self):
        raise NotImplementedError

    def generate_offer(self, received_msg):
        raise NotImplementedError

    def time_remaining(self, max_round_time=180):
        return max_round_time - (time.time() - self.start_time)

    def send(self, message):
        self.history.append({"self": message})
        return message

    def receive(self, message):
        self.history.append({"opponent": message})

    def is_valid_final_deal(self, price):
        if price is None:
            return False

        if self.role == "seller":
            return price >= self.limit
        return price <= self.limit


# --------------------------------------------------------------------------
# AGENT PERSONAS
# --------------------------------------------------------------------------

class AggressiveTrader(NegotiationAgent):

    def persona_prompt(self):
        return (
            "You are an aggressive negotiator. "
            "You pressure, bluff, push fast decisions. "
            "Use bold and strong language. Speak confidently."
        )

    def generate_offer(self, received_msg):
        opp_price = extract_price(received_msg)

        if self.role == "seller":
            anchor = self.limit + random.randint(20000, 40000)
        else:
            anchor = self.limit - random.randint(20000, 40000)

        if opp_price:
            if self.role == "seller":
                counter = max(self.limit, opp_price + random.randint(2000, 8000))
            else:
                counter = min(self.limit, opp_price - random.randint(2000, 8000))
        else:
            counter = anchor

        prompt = f"""
{self.persona_prompt()}
Role: {self.role}
Your limit: {self.limit}
Opponent said: {received_msg}
Your counter price: {counter}

Respond aggressively and INCLUDE the price clearly.
"""

        return self.model.complete(prompt)


class SmoothDiplomat(NegotiationAgent):

    def persona_prompt(self):
        return (
            "You are calm, friendly and cooperative. "
            "You push win-win deals and maintain harmony."
        )

    def generate_offer(self, received_msg):
        opp_price = extract_price(received_msg)

        if opp_price:
            counter = int((opp_price + self.limit) / 2)
        else:
            counter = self.limit + 10000 if self.role == "seller" else self.limit - 10000

        prompt = f"""
{self.persona_prompt()}
Role: {self.role}
Your limit: {self.limit}
Opponent: {received_msg}
Counter: {counter}

Respond warmly and INCLUDE the price clearly.
"""

        return self.model.complete(prompt)


class DataDrivenAnalyst(NegotiationAgent):

    def persona_prompt(self):
        return (
            "You speak like an analyst. Use logic, data and market reasoning. "
            "Explain your decisions."
        )

    def generate_offer(self, received_msg):
        opp_price = extract_price(received_msg)

        if opp_price:
            if self.role == "seller":
                counter = max(self.limit, opp_price + 3000)
            else:
                counter = min(self.limit, opp_price - 3000)
        else:
            counter = self.limit + 15000 if self.role == "seller" else self.limit - 15000

        prompt = f"""
{self.persona_prompt()}
Role: {self.role}
Limit: {self.limit}
Opponent: {received_msg}
Counter: {counter}

Respond analytically and INCLUDE the price.
"""

        return self.model.complete(prompt)
