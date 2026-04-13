import os
from dotenv import load_dotenv
from agent_base import AggressiveTrader, SmoothDiplomat, DataDrivenAnalyst, GroqLlama, extract_price

# Load environment variables from .env (Override system variables if they exist)
load_dotenv(override=True)

# --------------------------------------------------------
# API KEY LOADED FROM .ENV
# --------------------------------------------------------
API_KEY = os.getenv("GROQ_API_KEY")
model = GroqLlama(API_KEY)

# Create two agents
seller = AggressiveTrader("SellerX", "seller", limit=150000, model=model)
buyer = DataDrivenAnalyst("BuyerY", "buyer", limit=220000, model=model)

print("\n=== AI NEGOTIATION MATCH STARTED ===\n")

received = ""

for round in range(8):
    print(f"\n---------------- ROUND {round+1} ----------------")

    # Seller speaks
    seller_msg = seller.generate_offer(received)
    print("\nSeller:", seller_msg)
    buyer.receive(seller_msg)

    # Buyer speaks
    buyer_msg = buyer.generate_offer(seller_msg)
    print("\nBuyer :", buyer_msg)
    seller.receive(buyer_msg)

    # Check deal
    price = extract_price(buyer_msg)

    if price and seller.is_valid_final_deal(price) and buyer.is_valid_final_deal(price):
        print("\n🎉 DEAL CLOSED AT PRICE:", price)
        print("Match Ended.\n")
        break
else:
    print("\n❌ No deal reached. Both score 0.\n")
