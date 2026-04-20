"""
AI Expense Tracker - Main Application
Features: Auth, Dashboard, AI Parser, Admin Panel
All amounts in Indian Rupees (₹) with accurate math.
"""

import streamlit as st
from datetime import date
from db import init_db, add_transaction
from auth import login_user, signup_user
from ai_parser import parse_transaction
from dash import render_dashboard
from admin import render_admin_login, render_admin_panel
from utils import format_inr

# Initialize database
init_db()

# Page config
st.set_page_config(
    page_title="AI Expense Tracker 🇮🇳",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== COMPLETE CSS ====================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* ===== HERO CARD ===== */
    .hero-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    .hero-card::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: rgba(255,255,255,0.08);
        border-radius: 50%;
    }
    .hero-card h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        position: relative;
        z-index: 1;
    }
    .hero-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
        font-size: 1rem;
        position: relative;
        z-index: 1;
    }

    /* ===== METRIC CARDS ===== */
    .metric-card {
        padding: 1.5rem;
        border-radius: 16px;
        color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), box-shadow 0.3s;
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: "";
        position: absolute;
        top: -30%;
        right: -20%;
        width: 120px;
        height: 120px;
        background: rgba(255,255,255,0.1);
        border-radius: 50%;
    }
    .metric-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    .metric-icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .metric-label {
        font-size: 0.8rem;
        opacity: 0.9;
        font-weight: 600;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .metric-income {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    .metric-expense {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    .metric-balance-positive {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    }
    .metric-balance-negative {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
    }
    .metric-savings {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    }

    /* ===== BUDGET STATS ===== */
    .budget-stat {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 1.2rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        text-align: center;
    }
    .budget-label {
        font-size: 0.78rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .budget-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1e293b;
        margin-top: 0.4rem;
    }
    .budget-value-good { color: #10b981 !important; }
    .budget-value-bad { color: #ef4444 !important; }

    /* ===== INSIGHT BOX ===== */
    .insight-box {
        background: linear-gradient(135deg, #fef9c3 0%, #fde68a 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        border-left: 5px solid #f59e0b;
        color: #1c1917;
        line-height: 1.8;
        font-size: 0.95rem;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.15);
    }

    /* ===== ADMIN STYLES ===== */
    .admin-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 40px rgba(15, 23, 42, 0.4);
        text-align: center;
    }
    .admin-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .admin-header p {
        margin: 0.5rem 0 0 0;
        color: #94a3b8;
    }
    .admin-metric {
        background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
        padding: 1.2rem;
        border-radius: 14px;
        color: #e2e8f0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    .admin-metric:hover { transform: translateY(-4px); }
    .admin-metric-icon { font-size: 1.8rem; }
    .admin-metric-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #94a3b8;
        margin: 0.3rem 0;
    }
    .admin-metric-value {
        font-size: 1.2rem;
        font-weight: 700;
        color: white;
    }
    .admin-income { border-bottom: 3px solid #10b981; }
    .admin-expense { border-bottom: 3px solid #ef4444; }
    .admin-balance { border-bottom: 3px solid #3b82f6; }

    .top-spender-card {
        display: flex;
        align-items: center;
        padding: 0.8rem 1.2rem;
        margin: 0.4rem 0;
        background: #f8fafc;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    .top-spender-rank { font-size: 1.5rem; margin-right: 1rem; }
    .top-spender-name { flex: 1; font-weight: 600; color: #1e293b; }
    .top-spender-amount { font-weight: 700; color: #ef4444; }

    .settings-card {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .settings-card h3 { margin-top: 0; color: #1e293b; }
    .settings-card ul { color: #475569; }
    .settings-card code {
        background: #e2e8f0;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-size: 0.85rem;
    }

    /* ===== BUTTONS ===== */
    .stButton>button {
        border-radius: 10px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    .stButton>button:active {
        transform: translateY(0);
    }

    /* ===== INPUTS ===== */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        transition: border-color 0.3s;
    }
    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1);
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f1f5f9;
        padding: 0.5rem;
        border-radius: 14px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 0.5rem 1.2rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1rem;
        border-radius: 10px;
    }

    /* ===== DATAFRAME ===== */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ===== HIDE DEFAULTS ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# ==================== SESSION STATE ====================
if "user" not in st.session_state:
    st.session_state.user = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "page" not in st.session_state:
    st.session_state.page = "login"


# ==================== AUTH PAGES ====================
def login_page():
    """Modern login/signup page with admin access."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
        <div style="text-align:center; padding:2rem 0;">
            <div style="font-size:4rem;">💰</div>
            <h1 style="margin:0.5rem 0; color:#1e293b; font-weight:800;">AI Expense Tracker</h1>
            <p style="color:#64748b; font-size:1.1rem;">
                Smart finance tracking with AI • Made for India 🇮🇳
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🛡️ Admin"])

        with tab1:
            with st.form("login_form"):
                username = st.text_input(
                    "👤 Username", placeholder="Enter your username"
                )
                password = st.text_input(
                    "🔒 Password", type="password", placeholder="Enter your password"
                )
                submit = st.form_submit_button("🚀 Login", use_container_width=True)
                if submit:
                    if not username or not password:
                        st.error("❌ Please fill in all fields.")
                    else:
                        ok, result = login_user(username, password)
                        if ok:
                            st.session_state.user = result
                            st.success(f"Welcome back, {result['username']}! 🎉")
                            st.rerun()
                        elif result == "deactivated":
                            st.error(
                                "🚫 Your account has been deactivated. Contact admin."
                            )
                        else:
                            st.error("❌ Invalid username or password.")

        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input(
                    "👤 Choose Username", placeholder="e.g., rahul123"
                )
                new_password = st.text_input(
                    "🔒 Choose Password",
                    type="password",
                    placeholder="Min 4 characters",
                )
                confirm = st.text_input(
                    "🔒 Confirm Password",
                    type="password",
                    placeholder="Re-enter password",
                )
                submit = st.form_submit_button(
                    "✨ Create Account", use_container_width=True
                )
                if submit:
                    if new_password != confirm:
                        st.error("❌ Passwords do not match.")
                    else:
                        ok, msg = signup_user(new_username, new_password)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.balloons()
                        else:
                            st.error(f"❌ {msg}")

        with tab3:
            render_admin_login()

        st.markdown(
            """
        <div style="text-align:center; margin-top:2rem; color:#94a3b8; font-size:0.85rem;">
            🔒 Passwords encrypted with bcrypt • API keys secured via Streamlit Secrets
        </div>
        """,
            unsafe_allow_html=True,
        )


# ==================== ADD TRANSACTION PAGE ====================
def add_transaction_page(user):
    """Enhanced add transaction page with AI and manual input."""
    st.markdown(
        """
    <div class="hero-card">
        <h1>➕ Add New Transaction</h1>
        <p>Record your income or expense quickly in Indian Rupees (₹)</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["🤖 AI Smart Input", "📝 Manual Entry"])

    with tab1:
        st.markdown("**💬 Describe your transaction in plain English:**")
        st.caption(
            """
        Examples:  
        • "I spent ₹500 on groceries today"  
        • "Received salary of 50000"  
        • "Paid 1200 for electricity bill yesterday"  
        • "Bought movie ticket for 350"  
        • "Got 2.5 lakh from freelance project"
        """
        )

        text_input = st.text_area(
            "Your input",
            height=100,
            placeholder="Type your transaction here...",
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            parse_btn = st.button("🧠 Parse with AI", use_container_width=True)

        if parse_btn:
            if text_input.strip():
                with st.spinner("🤖 AI is understanding your input..."):
                    parsed = parse_transaction(text_input)
                    st.session_state.parsed = parsed
            else:
                st.warning("⚠️ Please enter something.")

        if "parsed" in st.session_state and st.session_state.parsed:
            parsed = st.session_state.parsed
            st.success("✨ Parsed successfully! Review and confirm:")

            preview_col1, preview_col2 = st.columns(2)
            with preview_col1:
                st.info(f"💰 **Amount:** {format_inr(parsed.get('amount', 0))}")
                st.info(f"🏷️ **Category:** {parsed.get('category', 'Other')}")
            with preview_col2:
                st.info(f"📊 **Type:** {parsed.get('type', 'expense').title()}")
                st.info(f"📅 **Date:** {parsed.get('date', str(date.today()))}")

            with st.form("confirm_ai"):
                st.markdown("#### ✏️ Edit before saving (if needed)")
                c1, c2 = st.columns(2)
                with c1:
                    amount = st.number_input(
                        "Amount (₹)",
                        value=float(parsed.get("amount", 0)),
                        min_value=0.0,
                        format="%.2f",
                    )
                    categories = [
                        "Food", "Travel", "Bills", "Shopping", "Entertainment",
                        "Health", "Education", "Salary", "Investment", "Other",
                    ]
                    default_cat = parsed.get("category", "Other")
                    cat_idx = (
                        categories.index(default_cat)
                        if default_cat in categories
                        else len(categories) - 1
                    )
                    category = st.selectbox("Category", categories, index=cat_idx)
                with c2:
                    type_ = st.selectbox(
                        "Type",
                        ["expense", "income"],
                        index=0 if parsed.get("type") == "expense" else 1,
                    )
                    try:
                        dt = date.fromisoformat(
                            parsed.get("date", str(date.today()))
                        )
                    except Exception:
                        dt = date.today()
                    entry_date = st.date_input("Date", value=dt)

                desc = st.text_input(
                    "Description", value=parsed.get("description", "")
                )

                if st.form_submit_button(
                    "✅ Save Transaction", use_container_width=True
                ):
                    if amount <= 0:
                        st.error("❌ Amount must be greater than 0.")
                    else:
                        add_transaction(
                            user["id"],
                            amount,
                            category,
                            type_,
                            str(entry_date),
                            desc,
                        )
                        st.success(f"🎉 Saved {format_inr(amount)} as {type_}!")
                        st.session_state.parsed = None
                        st.balloons()
                        st.rerun()

    with tab2:
        st.markdown("#### 📝 Fill the details manually")
        with st.form("manual_form"):
            c1, c2 = st.columns(2)
            with c1:
                amount = st.number_input(
                    "💰 Amount (₹)", min_value=0.0, step=10.0, format="%.2f"
                )
                category = st.selectbox(
                    "🏷️ Category",
                    [
                        "Food", "Travel", "Bills", "Shopping", "Entertainment",
                        "Health", "Education", "Salary", "Investment", "Other",
                    ],
                )
            with c2:
                type_ = st.radio("📊 Type", ["expense", "income"], horizontal=True)
                entry_date = st.date_input("📅 Date", value=date.today())

            desc = st.text_input(
                "📝 Description (optional)",
                placeholder="e.g., Grocery shopping at DMart",
            )

            if st.form_submit_button(
                "💾 Save Transaction", use_container_width=True
            ):
                if amount <= 0:
                    st.error("❌ Amount must be greater than ₹0.")
                else:
                    add_transaction(
                        user["id"], amount, category, type_, str(entry_date), desc
                    )
                    st.success(f"✅ Added {format_inr(amount)} as {type_}!")
                    st.balloons()


# ==================== MAIN APP ====================
def main():
    """Main application entry point with routing."""

    # If admin is logged in, show admin panel
    if st.session_state.is_admin:
        with st.sidebar:
            st.markdown(
                """
            <div style="text-align:center; padding:1rem 0;">
                <div style="font-size:3rem;">🛡️</div>
                <h3 style="margin:0.5rem 0;">Admin Panel</h3>
                <p style="color:#94a3b8; font-size:0.8rem;">Superuser Access</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
            st.divider()
            if st.button("🚪 Exit Admin", use_container_width=True):
                st.session_state.is_admin = False
                st.rerun()
        render_admin_panel()
        return

    # If no user logged in, show auth page
    if st.session_state.user is None:
        login_page()
        return

    user = st.session_state.user

    # Sidebar for logged-in user
    with st.sidebar:
        st.markdown(
            f"""
        <div style="text-align:center; padding:1.5rem 0; border-bottom:1px solid rgba(255,255,255,0.1);">
            <div style="font-size:3rem;">👤</div>
            <h3 style="margin:0.5rem 0; color:white; font-weight:700;">{user['username']}</h3>
            <p style="color:#94a3b8; font-size:0.82rem; margin:0;">
                🟢 Active • Premium User
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "➕ Add Transaction"],
            label_visibility="collapsed",
        )

        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.pop("parsed", None)
            st.rerun()

        st.markdown(
            """
        <div style="text-align:center; padding:1rem 0; font-size:0.75rem; color:#64748b;">
            Made with ❤️ for 🇮🇳<br>
            Powered by AI & Streamlit<br>
            v2.0 — Enhanced Edition
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Route to pages
    if page == "🏠 Dashboard":
        render_dashboard(user)
    elif page == "➕ Add Transaction":
        add_transaction_page(user)


if __name__ == "__main__":
    main()
