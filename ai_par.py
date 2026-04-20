import os
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Category keyword mapping for fallback
CATEGORY_KEYWORDS = {
    "Food": ["food", "groceries", "lunch", "dinner", "breakfast", "restaurant", "snack", "coffee", "pizza", "burger"],
    "Travel": ["travel", "uber", "taxi", "flight", "train", "bus", "fuel", "petrol", "gas", "cab"],
    "Bills": ["bill", "electricity", "water", "internet", "wifi", "phone", "rent", "gas bill"],
    "Shopping": ["shopping", "clothes", "shoes", "amazon", "flipkart", "dress"],
    "Entertainment": ["movie", "netflix", "spotify", "game", "concert"],
    "Health": ["medicine", "doctor", "hospital", "medical", "pharmacy"],
    "Education": ["book", "course", "tuition", "school", "college"],
    "Salary": ["salary", "paycheck", "wage"],
    "Investment": ["stock", "dividend", "mutual fund", "investment return"],
}

INCOME_KEYWORDS = ["received", "earned", "salary", "got paid", "income", "bonus", "refund", "credited"]


def rule_based_parser(text: str) -> dict:
    """Fallback rule-based parser."""
    text_lower = text.lower()

    # Amount extraction
    amount_match = re.search(r"(?:rs\.?|inr|usd|\$|₹)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", text_lower)
    amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0.0

    # Type detection
    type_ = "income" if any(kw in text_lower for kw in INCOME_KEYWORDS) else "expense"

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
    else:
        date = today

    return {
        "amount": amount,
        "category": category,
        "type": type_,
        "date": str(date),
        "description": text.strip(),
    }


def parse_with_llm(text: str) -> dict:
    """Use LangChain + Gemini to parse input."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain.prompts import PromptTemplate

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_gemini_api_key_here":
            return rule_based_parser(text)

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0,
        )

        today_str = datetime.now().strftime("%Y-%m-%d")
        prompt = PromptTemplate.from_template("""
You are a financial transaction parser. Extract structured data from the user's input.
Return ONLY a valid JSON object (no markdown, no explanations) with these keys:
- amount (number)
- category (one of: Food, Travel, Bills, Shopping, Entertainment, Health, Education, Salary, Investment, Other)
- type (either "income" or "expense")
- date (YYYY-MM-DD format; today is {today})
- description (string)

User input: "{text}"

JSON:
""")

        chain = prompt | llm
        response = chain.invoke({"text": text, "today": today_str})
        content = response.content.strip()

        # Clean JSON from possible markdown fences
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()

        data = json.loads(content)

        # Validate
        data["amount"] = float(data.get("amount", 0))
        data["type"] = data.get("type", "expense").lower()
        if data["type"] not in ["income", "expense"]:
            data["type"] = "expense"
        data["category"] = data.get("category", "Other")
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

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "AIzaSyCAmmcSnP1uX1KQ_YVmPZrphFHGJv0KDzY":
            return _basic_insight(transactions)

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.3,
        )

        summary = _transactions_summary(transactions)
        prompt = f"""You are a friendly financial advisor. Based on this user's transaction summary, give 3-4 short, actionable insights and tips in a friendly tone. Keep it under 150 words.

{summary}

Insights:"""

        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        return _basic_insight(transactions)


def _transactions_summary(transactions):
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    categories = {}
    for t in transactions:
        if t["type"] == "expense":
            categories[t["category"]] = categories.get(t["category"], 0) + t["amount"]
    top_cat = sorted(categories.items(), key=lambda x: -x[1])[:3]
    return (
        f"Total Income: {total_income:.2f}\nTotal Expense: {total_expense:.2f}\n"
        f"Balance: {total_income - total_expense:.2f}\n"
        f"Top spending categories: {top_cat}\nNum transactions: {len(transactions)}"
    )


def _basic_insight(transactions):
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expense
    if balance < 0:
        return "⚠️ You're spending more than you earn. Consider cutting down on non-essential expenses."
    elif total_expense > 0.7 * total_income:
        return "💡 You're spending over 70% of your income. Try saving at least 20% each month."
    else:
        return "✅ Great job! Your spending looks healthy. Keep saving and tracking!"