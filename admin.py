"""
Admin Panel module.
Accessible only with a special hardcoded admin password.
Provides platform-wide analytics and user management.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from db import (
    get_all_users, get_all_transactions, get_user_count,
    get_transaction_count, get_platform_totals, get_user_stats,
    toggle_user_status, delete_user, admin_delete_transaction,
)
from utils import format_inr, safe_percentage

# ╔══════════════════════════════════════════════════════╗
# ║           🔐 ADMIN PASSWORD (CHANGE THIS!)          ║
# ║     Only this password grants admin access.          ║
# ╚══════════════════════════════════════════════════════╝
ADMIN_PASSWORD = "SuperAdmin@2025#Secure"


def verify_admin_password(password: str) -> bool:
    """Verify if the given password matches the admin password."""
    return password == ADMIN_PASSWORD


def render_admin_login():
    """Render admin login page."""
    st.markdown(
        """
    <div style="text-align:center; padding:2rem 0;">
        <div style="font-size:4rem;">🛡️</div>
        <h1 style="color:#1f2937;">Admin Panel</h1>
        <p style="color:#6b7280;">Enter admin credentials to access the control center</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("admin_login_form"):
            admin_pass = st.text_input(
                "🔐 Admin Password",
                type="password",
                placeholder="Enter admin password",
            )
            submit = st.form_submit_button(
                "🚀 Access Admin Panel", use_container_width=True
            )
            if submit:
                if verify_admin_password(admin_pass):
                    st.session_state.is_admin = True
                    st.success("✅ Admin access granted!")
                    st.rerun()
                else:
                    st.error("❌ Invalid admin password. Access denied.")
                    st.session_state.is_admin = False


def render_admin_panel():
    """Main admin panel with all management features."""

    # Admin header
    st.markdown(
        """
    <div class="admin-header">
        <h1>🛡️ Admin Control Center</h1>
        <p>Platform-wide analytics and user management</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Platform KPIs
    user_count = get_user_count()
    txn_count = get_transaction_count()
    platform_totals = get_platform_totals()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
        <div class="admin-metric">
            <div class="admin-metric-icon">👥</div>
            <div class="admin-metric-label">Total Users</div>
            <div class="admin-metric-value">{user_count}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="admin-metric">
            <div class="admin-metric-icon">📋</div>
            <div class="admin-metric-label">Total Transactions</div>
            <div class="admin-metric-value">{txn_count}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="admin-metric admin-income">
            <div class="admin-metric-icon">💰</div>
            <div class="admin-metric-label">Platform Income</div>
            <div class="admin-metric-value">{format_inr(platform_totals['income'])}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
        <div class="admin-metric admin-expense">
            <div class="admin-metric-icon">💸</div>
            <div class="admin-metric-label">Platform Expenses</div>
            <div class="admin-metric-value">{format_inr(platform_totals['expense'])}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            f"""
        <div class="admin-metric admin-balance">
            <div class="admin-metric-icon">🏦</div>
            <div class="admin-metric-label">Platform Balance</div>
            <div class="admin-metric-value">{format_inr(platform_totals['balance'])}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Admin tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["👥 User Management", "📋 All Transactions", "📊 Analytics", "⚙️ Settings"]
    )

    with tab1:
        render_user_management()

    with tab2:
        render_all_transactions()

    with tab3:
        render_admin_analytics()

    with tab4:
        render_admin_settings()


def render_user_management():
    """User management section."""
    st.markdown("### 👥 User Management")

    user_stats = get_user_stats()

    if not user_stats:
        st.info("No users registered yet.")
        return

    # User stats table
    df = pd.DataFrame(user_stats)
    df["total_income"] = df["total_income"].apply(format_inr)
    df["total_expense"] = df["total_expense"].apply(format_inr)
    df["status"] = df["is_active"].apply(
        lambda x: "🟢 Active" if x else "🔴 Inactive"
    )

    display_df = df[
        [
            "id", "username", "status", "total_transactions",
            "total_income", "total_expense", "created_at",
        ]
    ].copy()
    display_df.columns = [
        "ID", "Username", "Status", "Transactions",
        "Total Income", "Total Expense", "Joined",
    ]

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # User actions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔄 Toggle User Status")
        users_list = get_all_users()
        user_options = {
            f"{u['username']} ({'Active' if u['is_active'] else 'Inactive'}) [ID: {u['id']}]": u[
                "id"
            ]
            for u in users_list
        }
        if user_options:
            selected_user = st.selectbox(
                "Select User", list(user_options.keys()), key="toggle_user"
            )
            if st.button("🔄 Toggle Active/Inactive", use_container_width=True):
                toggle_user_status(user_options[selected_user])
                st.success("✅ User status updated!")
                st.rerun()

    with col2:
        st.markdown("#### 🗑️ Delete User")
        st.warning("⚠️ This will permanently delete the user and all their data!")
        user_options_del = {
            f"{u['username']} [ID: {u['id']}]": u["id"] for u in users_list
        }
        if user_options_del:
            selected_del = st.selectbox(
                "Select User to Delete",
                list(user_options_del.keys()),
                key="del_user",
            )
            confirm_del = st.text_input(
                "Type 'DELETE' to confirm", key="confirm_delete"
            )
            if st.button("🗑️ Delete User Permanently", use_container_width=True):
                if confirm_del == "DELETE":
                    delete_user(user_options_del[selected_del])
                    st.success("✅ User deleted permanently.")
                    st.rerun()
                else:
                    st.error("❌ Type 'DELETE' to confirm.")


def render_all_transactions():
    """Show all platform transactions."""
    st.markdown("### 📋 All Platform Transactions")

    all_txns = get_all_transactions()

    if not all_txns:
        st.info("No transactions on the platform yet.")
        return

    st.markdown(f"**Total: {len(all_txns)} transactions**")

    df = pd.DataFrame(all_txns)
    df_display = df[
        ["id", "username", "date", "type", "category", "amount", "description"]
    ].copy()
    df_display["amount"] = df_display["amount"].apply(format_inr)
    df_display["type"] = df_display["type"].apply(
        lambda x: f"📥 {x.title()}" if x == "income" else f"📤 {x.title()}"
    )
    df_display.columns = [
        "ID", "👤 User", "📅 Date", "Type",
        "🏷️ Category", "💰 Amount", "📝 Description",
    ]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Admin delete transaction
    with st.expander("🗑️ Delete a Transaction"):
        txn_options = {
            f"[{t['id']}] {t['username']} | {t['date']} | {t['type']} | {format_inr(t['amount'])} | {t['category']}": t[
                "id"
            ]
            for t in all_txns
        }
        if txn_options:
            selected_txn = st.selectbox(
                "Select Transaction", list(txn_options.keys()), key="admin_del_txn"
            )
            if st.button(
                "🗑️ Delete This Transaction", use_container_width=True, key="btn_del_txn"
            ):
                admin_delete_transaction(txn_options[selected_txn])
                st.success("✅ Transaction deleted.")
                st.rerun()


def render_admin_analytics():
    """Platform-wide analytics and charts."""
    st.markdown("### 📊 Platform Analytics")

    all_txns = get_all_transactions()

    if not all_txns:
        st.info("No data to analyze yet.")
        return

    df = pd.DataFrame(all_txns)
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    col1, col2 = st.columns(2)

    # Users activity pie chart
    with col1:
        st.markdown("#### 👥 Transactions per User")
        user_txn = df.groupby("username")["id"].count().reset_index()
        user_txn.columns = ["User", "Transactions"]
        fig = px.pie(
            user_txn,
            values="Transactions",
            names="User",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_layout(
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Category distribution
    with col2:
        st.markdown("#### 🏷️ Platform Expense by Category")
        expense_df = df[df["type"] == "expense"]
        if not expense_df.empty:
            cat_sum = expense_df.groupby("category")["amount"].sum().reset_index()
            cat_sum["amount_formatted"] = cat_sum["amount"].apply(format_inr)
            fig = px.bar(
                cat_sum.sort_values("amount", ascending=True),
                x="amount",
                y="category",
                orientation="h",
                color="amount",
                color_continuous_scale="Reds",
                custom_data=["amount_formatted"],
            )
            fig.update_traces(
                hovertemplate="<b>%{y}</b><br>%{customdata[0]}<extra></extra>"
            )
            fig.update_layout(
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis_title="Amount (₹)",
                yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Monthly trend
    st.markdown("#### 📈 Monthly Platform Trends")
    df["month"] = df["date"].dt.strftime("%b %Y")
    df["month_sort"] = df["date"].dt.strftime("%Y-%m")
    monthly = df.groupby(["month", "month_sort", "type"])["amount"].sum().reset_index()
    monthly = monthly.sort_values("month_sort")
    monthly["amount_formatted"] = monthly["amount"].apply(format_inr)

    fig = px.line(
        monthly,
        x="month",
        y="amount",
        color="type",
        markers=True,
        color_discrete_map={"income": "#10b981", "expense": "#ef4444"},
        custom_data=["amount_formatted"],
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{customdata[0]}<extra></extra>",
        line=dict(width=3),
    )
    fig.update_layout(
        height=400,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="Amount (₹)",
        legend_title="",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Top spenders
    st.markdown("#### 🏆 Top Spenders")
    user_stats = get_user_stats()
    top_spenders = sorted(user_stats, key=lambda x: x["total_expense"], reverse=True)[
        :5
    ]
    for i, u in enumerate(top_spenders, 1):
        medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"#{i}"))
        st.markdown(
            f"""
        <div class="top-spender-card">
            <span class="top-spender-rank">{medal}</span>
            <span class="top-spender-name">{u['username']}</span>
            <span class="top-spender-amount">{format_inr(u['total_expense'])}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_admin_settings():
    """Admin settings and info."""
    st.markdown("### ⚙️ Admin Settings")

    st.markdown(
        """
    <div class="settings-card">
        <h3>🔐 Security Info</h3>
        <ul>
            <li>Admin password is hardcoded in <code>admin.py</code></li>
            <li>Change <code>ADMIN_PASSWORD</code> variable to update</li>
            <li>User passwords are hashed with bcrypt</li>
            <li>API keys are stored in Streamlit Secrets</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="settings-card">
        <h3>📊 Database Info</h3>
        <ul>
            <li>Database: SQLite (<code>expense_tracker.db</code>)</li>
            <li>Tables: users, transactions, budgets</li>
            <li>All amounts stored with 2 decimal precision</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### 🚪 Admin Logout")
    if st.button("🚪 Exit Admin Panel", use_container_width=True):
        st.session_state.is_admin = False
        st.rerun()