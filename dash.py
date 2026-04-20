import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from db import (
    get_transactions, get_totals, delete_transaction,
    get_budget, set_budget, get_monthly_expense
)
from ai_parser import generate_monthly_insight


def render_dashboard(user):
    """Render the main dashboard."""
    st.title(f"👋 Welcome back, {user['username']}!")

    totals = get_totals(user["id"])

    # KPI Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Income", f"₹ {totals['income']:.2f}")
    col2.metric("💸 Total Expenses", f"₹ {totals['expense']:.2f}")
    col3.metric("🏦 Balance", f"₹ {totals['balance']:.2f}",
                delta=f"{totals['balance']:.2f}")

    st.divider()

    # Budget alerts
    render_budget_section(user)

    st.divider()

    # Charts
    transactions = get_transactions(user["id"])
    if not transactions:
        st.info("📊 No transactions yet. Add some to see analytics!")
        return

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])

    col1, col2 = st.columns(2)

    # Pie chart - expenses by category
    with col1:
        st.subheader("🥧 Expenses by Category")
        expense_df = df[df["type"] == "expense"]
        if not expense_df.empty:
            cat_sum = expense_df.groupby("category")["amount"].sum().reset_index()
            fig = px.pie(cat_sum, values="amount", names="category", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.RdBu)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses yet.")

    # Bar chart - monthly income vs expenses
    with col2:
        st.subheader("📊 Monthly Income vs Expenses")
        df["month"] = df["date"].dt.strftime("%Y-%m")
        monthly = df.groupby(["month", "type"])["amount"].sum().reset_index()
        fig = px.bar(monthly, x="month", y="amount", color="type",
                     barmode="group", color_discrete_map={"income": "#2ecc71", "expense": "#e74c3c"})
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # AI Insights
    with st.expander("🤖 AI Monthly Insights", expanded=True):
        if st.button("Generate AI Insight"):
            with st.spinner("Analyzing your finances..."):
                insight = generate_monthly_insight(transactions)
                st.success(insight)

    st.divider()

    # Recent transactions
    render_transactions_table(user)


def render_budget_section(user):
    """Budget setting and alerts."""
    st.subheader("🎯 Monthly Budget")

    current_budget = get_budget(user["id"])
    monthly_expense = get_monthly_expense(user["id"])

    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        new_budget = st.number_input(
            "Set Monthly Budget (₹)",
            min_value=0.0, value=float(current_budget), step=500.0,
        )
        if st.button("💾 Save Budget"):
            set_budget(user["id"], new_budget)
            st.success("Budget updated!")
            st.rerun()

    with col2:
        st.metric("This Month's Expenses", f"₹ {monthly_expense:.2f}")

    with col3:
        if current_budget > 0:
            usage = (monthly_expense / current_budget) * 100
            st.metric("Budget Used", f"{usage:.1f}%")
            if usage >= 100:
                st.error("🚨 You exceeded your monthly budget!")
            elif usage >= 80:
                st.warning("⚠️ You've used over 80% of your budget.")
            else:
                st.success("✅ You're within budget.")

    if current_budget > 0:
        progress = min(monthly_expense / current_budget, 1.0)
        st.progress(progress)


def render_transactions_table(user):
    """Recent transactions with filters."""
    st.subheader("📜 Transactions")

    with st.expander("🔍 Filters"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            start_date = st.date_input("From", value=date.today() - timedelta(days=30))
        with c2:
            end_date = st.date_input("To", value=date.today())
        with c3:
            category = st.selectbox("Category", [
                "All", "Food", "Travel", "Bills", "Shopping",
                "Entertainment", "Health", "Education", "Salary", "Investment", "Other"
            ])
        with c4:
            type_ = st.selectbox("Type", ["All", "income", "expense"])

    transactions = get_transactions(
        user["id"], start_date=start_date, end_date=end_date,
        category=category, type_=type_
    )

    if not transactions:
        st.info("No transactions match your filters.")
        return

    df = pd.DataFrame(transactions)
    df_display = df[["date", "type", "category", "amount", "description"]].copy()
    df_display.columns = ["Date", "Type", "Category", "Amount", "Description"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Delete option
    with st.expander("🗑️ Delete a transaction"):
        options = {f"{t['date']} | {t['type']} | ₹{t['amount']} | {t['category']}": t["id"] for t in transactions}
        if options:
            selected = st.selectbox("Select transaction", list(options.keys()))
            if st.button("Delete Selected"):
                delete_transaction(options[selected], user["id"])
                st.success("Transaction deleted.")
                st.rerun()