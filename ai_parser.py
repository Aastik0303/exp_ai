"""
AI-powered natural language transaction parser.
Uses LangChain + Google Gemini with st.secrets for API key management.
Falls back to rule-based parsing if API is unavailable.
"""

import os
import json
import re
import streamlit as st
from datetime import datetime, timedelta

# Category keyword mapping for fallback rule-based parser
CATEGORY_KEYWORDS = {
    "Food": [
        "food", "groceries", "lunch", "dinner", "breakfast",
        "restaurant", "snack", "coffee", "pizza", "burger",
        "zomato", "swiggy", "biryani", "dosa", "chai",
    ],
    "Travel": [
        "travel", "uber", "taxi", "flight", "train",
        "bus", "fuel", "petrol", "gas", "cab", "ola",
        "metro", "auto", "rickshaw",
    ],
    "Bills": [
        "bill", "electricity", "water", "internet", "wifi",
        "phone", "rent", "gas bill", "recharge", "emi",
        "insurance", "maintenance",
    ],
    "Shopping": [
        "shopping", "clothes", "shoes", "amazon", "flipkart",
        "dress", "myntra", "mall", "shirt", "jeans",
    ],
    "Entertainment": [
        "movie", "netflix", "spotify", "game", "concert",
        "hotstar", "prime", "youtube", "outing",
    ],
    "Health": [
        "medicine", "doctor", "hospital", "medical", "pharmacy",
        "gym", "fitness", "yoga", "health",
    ],
    "Education": [
        "book", "course", "tuition", "school", "college",
        "udemy", "coaching", "exam", "fees",
    ],
    "Salary": ["salary", "paycheck", "wage"],
    "Investment": [
        "stock", "dividend", "mutual fund", "investment return",
        "sip", "fd", "fixed deposit", "ppf", "nps",
    ],
}

INCOME_KEYWORDS = [
    "received", "earned", "salary", "got paid", "income",
    "bonus", "refund", "credited", "cashback", "reward",
    "freelance", "payment received",
]


def get_api_key(key_name: str) -> str:
    """
    Safely get API key from st.secrets (Streamlit Cloud) or environment variables.
    Priority: st.secrets > os.environ
    """
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name, "")


def rule_based_parser(text: str) -> dict:
    """Fallback rule-based parser with Indian number format support."""
    text_lower = text.lower()

    # Remove common INR symbols for cleaner parsing
    clean_text = (
        text_lower.replace("₹", "")
        .replace("rs.", "")
        .replace("rs ", "")
        .replace("inr", "")
    )

    # Enhanced amount extraction - handles lakh, crore, k
    amount = 0.0

    crore_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:crore|cr)\b", clean_text)
    lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b", clean_text)
    k_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", clean_text)

    if crore_match:
        amount = float(crore_match.group(1)) * 10000000
    elif lakh_match:
        amount = float(lakh_match.group(1)) * 100000
    elif k_match:
        amount = float(k_match.group(1)) * 1000
    else:
        amount_match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)", clean_text)
        if amount_match:
            amount = float(amount_match.group(1).replace(",", ""))

    # Type detection
    type_ = (
        "income" if any(kw in text_lower for kw in INCOME_KEYWORDS) else "expense"
    )

    # Category detection
    category = "Other"
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            category = cat
            break
    if type_ == "income" and category == "Other":
        category = "Salary"

    # Date detection
    today = datetime.now().date()
    if "yesterday" in text_lower:
        date = today - timedelta(days=1)
    elif "tomorrow" in text_lower:
        date = today + timedelta(days=1)
    elif "last week" in text_lower:
        date = today - timedelta(days=7)
    else:
        date = today

    return {
        "amount": round(amount, 2),
        "category": category,
        "type": type_,
        "date": str(date),
        "description": text.strip(),
    }


def parse_with_llm(text: str) -> dict:
    """Use LangChain + Google Gemini to parse natural language input."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain.prompts import PromptTemplate

        api_key = get_api_key("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_gemini_api_key_here":
            print("[AI Parser] No Google API key found, using rule-based parser.")
            return rule_based_parser(text)

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0,
        )

        today_str = datetime.now().strftime("%Y-%m-%d")
        prompt = PromptTemplate.from_template(
            """You are a financial transaction parser for an Indian user.
Extract structured data from the user's input.
All amounts are in Indian Rupees (INR).
Return ONLY a valid JSON object (no markdown, no explanations, no code fences) with these exact keys:
- amount (number in INR, convert lakh/crore to numbers)
- category (one of: Food, Travel, Bills, Shopping, Entertainment, Health, Education, Salary, Investment, Other)
- type (either "income" or "expense")
- date (YYYY-MM-DD format; today is {today})
- description (string)

User input: "{text}"

JSON:"""
        )

        chain = prompt | llm
        response = chain.invoke({"text": text, "today": today_str})
        content = response.content.strip()

        # Clean JSON from markdown fences
        content = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE
        ).strip()
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            content = json_match.group(0)

        data = json.loads(content)

        # Validate & sanitize
        data["amount"] = float(data.get("amount", 0))
        data["type"] = data.get("type", "expense").lower()
        if data["type"] not in ["income", "expense"]:
            data["type"] = "expense"

        valid_categories = [
            "Food", "Travel", "Bills", "Shopping", "Entertainment",
            "Health", "Education", "Salary", "Investment", "Other",
        ]
        if data.get("category") not in valid_categories:
            data["category"] = "Other"

        data["date"] = data.get("date", today_str)
        data["description"] = data.get("description", text)
        return data

    except Exception as e:
        print(f"[AI Parser] LLM failed: {e}. Falling back to rule-based.")
        return rule_based_parser(text)


def parse_transaction(text: str) -> dict:
    """Main parser entry point."""
    return parse_with_llm(text)


def generate_monthly_insight(transactions: list) -> str:
    """Generate AI-based monthly summary insights."""
    if not transactions:
        return "No transactions yet. Start tracking to get insights!"

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = get_api_key("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_gemini_api_key_here":
            return _basic_insight(transactions)

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.3,
        )

        summary = _transactions_summary(transactions)
        prompt = f"""You are a friendly Indian financial advisor. Based on this user's transaction summary,
give 4-5 line summary according to data and based on information and analyse the data and provide solutions acording to data 

{summary}

Insights:"""

        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"[AI Insight] Failed: {e}")
        return _basic_insight(transactions)


def _transactions_summary(transactions):
    """Create a text summary of transactions for the AI."""
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    categories = {}
    for t in transactions:
        if t["type"] == "expense":
            categories[t["category"]] = (
                categories.get(t["category"], 0) + t["amount"]
            )
    top_cat = sorted(categories.items(), key=lambda x: -x[1])[:3]
    return (
        f"Total Income: ₹{total_income:.2f}\nTotal Expense: ₹{total_expense:.2f}\n"
        f"Balance: ₹{total_income - total_expense:.2f}\n"
        f"Top spending categories: {top_cat}\nNum transactions: {len(transactions)}"
    )


def _basic_insight(transactions):
    """Fallback basic insight when AI is unavailable."""
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expense
    if balance < 0:
        return "⚠️ You're spending more than you earn. Consider cutting down on non-essential expenses."
    elif total_expense > 0.7 * total_income and total_income > 0:
        return "💡 You're spending over 70% of your income. Try the 50-30-20 rule!"
    else:
        return "✅ Great job! Your spending looks healthy. Keep saving and tracking!"
