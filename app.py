import streamlit as st
from datetime import date
from db import init_db, add_transaction
from auth import login_user, signup_user
from ai_parser import parse_transaction
from dashboard import render_dashboard

# Init DB
init_db()

st.set_page_config(
    page_title="AI Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 12px;
        color: white;
    }
    [data-testid="stMetricLabel"] { color: white !important; }
    [data-testid="stMetricValue"] { color: white !important; }
</style>
""", unsafe_allow_html=True)

# Session state
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Login"


def login_page():
    st.title("💰 AI Expense Tracker")
    st.markdown("### Track your finances smartly with AI")

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            if submit:
                ok, user = login_user(username, password)
                if ok:
                    st.session_state.user = user
                    st.success(f"Welcome back, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with tab2:
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            submit = st.form_submit_button("Sign Up")
            if submit:
                if new_password != confirm:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = signup_user(new_username, new_password)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


def add_transaction_page(user):
    st.title("➕ Add Transaction")

    tab1, tab2 = st.tabs(["🤖 AI Input", "📝 Manual Entry"])

    # AI-powered input
    with tab1:
        st.markdown("**Describe your transaction in plain English:**")
        st.caption('E.g., "I spent 500 on groceries today" or "Received salary of 50000"')

        text_input = st.text_area("Your input", height=100)

        if st.button("🧠 Parse with AI"):
            if text_input.strip():
                with st.spinner("AI is parsing your input..."):
                    parsed = parse_transaction(text_input)
                    st.session_state.parsed = parsed
            else:
                st.warning("Please enter something.")

        if "parsed" in st.session_state and st.session_state.parsed:
            parsed = st.session_state.parsed
            st.success("✨ Parsed successfully! Review and confirm:")
            st.json(parsed)

            with st.form("confirm_ai"):
                amount = st.number_input("Amount", value=float(parsed.get("amount", 0)), min_value=0.0)
                category = st.selectbox("Category", [
                    "Food", "Travel", "Bills", "Shopping", "Entertainment",
                    "Health", "Education", "Salary", "Investment", "Other"
                ], index=0 if parsed.get("category") not in [
                    "Food", "Travel", "Bills", "Shopping", "Entertainment",
                    "Health", "Education", "Salary", "Investment", "Other"
                ] else [
                    "Food", "Travel", "Bills", "Shopping", "Entertainment",
                    "Health", "Education", "Salary", "Investment", "Other"
                ].index(parsed["category"]))
                type_ = st.selectbox("Type", ["expense", "income"],
                                     index=0 if parsed.get("type") == "expense" else 1)
                try:
                    dt = date.fromisoformat(parsed.get("date", str(date.today())))
                except Exception:
                    dt = date.today()
                entry_date = st.date_input("Date", value=dt)
                desc = st.text_input("Description", value=parsed.get("description", ""))

                if st.form_submit_button("✅ Save Transaction"):
                    add_transaction(user["id"], amount, category, type_, str(entry_date), desc)
                    st.success("Transaction saved!")
                    st.session_state.parsed = None
                    st.rerun()

    # Manual entry
    with tab2:
        with st.form("manual_form"):
            amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
            category = st.selectbox("Category", [
                "Food", "Travel", "Bills", "Shopping", "Entertainment",
                "Health", "Education", "Salary", "Investment", "Other"
            ])
            type_ = st.radio("Type", ["expense", "income"], horizontal=True)
            entry_date = st.date_input("Date", value=date.today())
            desc = st.text_input("Description (optional)")

            if st.form_submit_button("💾 Save Transaction"):
                if amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    add_transaction(user["id"], amount, category, type_, str(entry_date), desc)
                    st.success("Transaction added successfully!")


def main():
    if st.session_state.user is None:
        login_page()
        return

    user = st.session_state.user

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user['username']}")
        st.divider()

        page = st.radio("Navigation", ["🏠 Dashboard", "➕ Add Transaction"], label_visibility="collapsed")

        st.divider()
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.pop("parsed", None)
            st.rerun()

        st.caption("Made with ❤️ using Streamlit + LangChain")

    # Route pages
    if page == "🏠 Dashboard":
        render_dashboard(user)
    elif page == "➕ Add Transaction":
        add_transaction_page(user)


if __name__ == "__main__":
    main()