"""
Dashboard module with modern UI, charts and analytics.
All amounts displayed in Indian Rupee format.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from db import (
    get_transactions, get_totals, delete_transaction,
    get_budget, set_budget, get_monthly_expense, get_category_totals,
)
from ai_parser import generate_monthly_insight
from utils import format_inr, safe_percentage, safe_subtract


def render_dashboard(user):
    """Render the main dashboard with modern UI and INR formatting."""

    # Hero header
    st.markdown(
        f"""
    <div class="hero-card">
        <h1>👋 Welcome back, {user['username']}!</h1>
        <p>Here's your financial overview — Stay on top of your money 💪🇮🇳</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    totals = get_totals(user["id"])

    # KPI Metric Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card metric-income">
            <div class="metric-icon">💰</div>
            <div class="metric-label">Total Income</div>
            <div class="metric-value">{format_inr(totals['income'])}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card metric-expense">
            <div class="metric-icon">💸</div>
            <div class="metric-label">Total Expenses</div>
            <div class="metric-value">{format_inr(totals['expense'])}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        balance_class = (
            "metric-balance-positive"
            if totals["balance"] >= 0
            else "metric-balance-negative"
        )
        st.markdown(
            f"""
        <div class="metric-card {balance_class}">
            <div class="metric-icon">🏦</div>
            <div class="metric-label">Balance</div>
            <div class="metric-value">{format_inr(totals['balance'])}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        savings_rate = (
            safe_percentage(totals["balance"], totals["income"])
            if totals["income"] > 0
            else 0
        )
        st.markdown(
            f"""
        <div class="metric-card metric-savings">
            <div class="metric-icon">📈</div>
            <div class="metric-label">Savings Rate</div>
            <div class="metric-value">{savings_rate:.1f}%</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Budget section
    render_budget_section(user)
    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    transactions = get_transactions(user["id"])
    if not transactions:
        st.info("📊 No transactions yet. Add some to see beautiful analytics!")
        return

    df = pd.DataFrame(transactions)
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    col1, col2 = st.columns(2)

    # Pie chart - expenses by category
    with col1:
        st.markdown("### 🥧 Expenses by Category")
        expense_df = df[df["type"] == "expense"]
        if not expense_df.empty:
            cat_sum = expense_df.groupby("category")["amount"].sum().reset_index()
            cat_sum["amount_formatted"] = cat_sum["amount"].apply(format_inr)

            fig = px.pie(
                cat_sum,
                values="amount",
                names="category",
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Set3,
                custom_data=["amount_formatted"],
            )
            fig.update_traces(
                textposition="outside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Amount: %{customdata[0]}<br>Share: %{percent}<extra></extra>",
            )
            fig.update_layout(
                showlegend=True,
                height=400,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses recorded yet.")

    # Bar chart - monthly income vs expenses
    with col2:
        st.markdown("### 📊 Monthly Income vs Expenses")
        df["month"] = df["date"].dt.strftime("%b %Y")
        df["month_sort"] = df["date"].dt.strftime("%Y-%m")

        monthly = (
            df.groupby(["month", "month_sort", "type"])["amount"]
            .sum()
            .reset_index()
        )
        monthly = monthly.sort_values("month_sort")
        monthly["amount_formatted"] = monthly["amount"].apply(format_inr)

        fig = px.bar(
            monthly,
            x="month",
            y="amount",
            color="type",
            barmode="group",
            color_discrete_map={"income": "#10b981", "expense": "#ef4444"},
            custom_data=["amount_formatted"],
        )
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>%{customdata[0]}<extra></extra>"
        )
        fig.update_layout(
            height=400,
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis_title="",
            yaxis_title="Amount (₹)",
            legend_title="",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Category breakdown table
    st.markdown("### 💼 Category-wise Breakdown")
    exp_totals = get_category_totals(user["id"], "expense")
    if exp_totals:
        breakdown_df = pd.DataFrame(
            [
                {
                    "Category": cat,
                    "Amount": format_inr(amt),
                    "Share": f"{safe_percentage(amt, totals['expense']):.1f}%",
                }
                for cat, amt in sorted(exp_totals.items(), key=lambda x: -x[1])
            ]
        )
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # AI Insights
    with st.expander("🤖 AI-Powered Monthly Insights", expanded=False):
        if st.button("✨ Generate AI Insight", use_container_width=True):
            with st.spinner("🧠 Analyzing your finances..."):
                insight = generate_monthly_insight(transactions)
                st.markdown(
                    f"""
                <div class="insight-box">
                    {insight}
                </div>
                """,
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # Transaction history
    render_transactions_table(user)


def render_budget_section(user):
    """Modern budget section with progress bar and alerts."""
    st.markdown("### 🎯 Monthly Budget Tracker")

    current_budget = get_budget(user["id"])
    monthly_expense = get_monthly_expense(user["id"])

    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        new_budget = st.number_input(
            "Set Monthly Budget (₹)",
            min_value=0.0,
            value=float(current_budget),
            step=500.0,
            format="%.2f",
        )
        if st.button("💾 Save Budget", use_container_width=True):
            set_budget(user["id"], new_budget)
            st.success("✅ Budget updated!")
            st.rerun()

    with col2:
        st.markdown(
            f"""
        <div class="budget-stat">
            <div class="budget-label">This Month's Expenses</div>
            <div class="budget-value">{format_inr(monthly_expense)}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        remaining = safe_subtract(current_budget, monthly_expense)
        label = "Remaining" if remaining >= 0 else "Over Budget"
        color_class = "budget-value-good" if remaining >= 0 else "budget-value-bad"
        st.markdown(
            f"""
        <div class="budget-stat">
            <div class="budget-label">{label}</div>
            <div class="budget-value {color_class}">{format_inr(abs(remaining))}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if current_budget > 0:
        usage = safe_percentage(monthly_expense, current_budget)
        progress = min(monthly_expense / current_budget, 1.0)

        if usage >= 100:
            msg = f"🚨 **Budget Exceeded!** You've spent {usage:.1f}% of your budget."
            st.progress(progress)
            st.error(msg)
        elif usage >= 80:
            msg = f"⚠️ **Warning!** You've used {usage:.1f}% of your budget."
            st.progress(progress)
            st.warning(msg)
        elif usage >= 50:
            msg = f"📊 You've used {usage:.1f}% of your budget."
            st.progress(progress)
            st.info(msg)
        else:
            msg = f"✅ Only {usage:.1f}% used. You're doing great!"
            st.progress(progress)
            st.success(msg)
    else:
        st.info("💡 Set a monthly budget to track your spending better.")


def render_transactions_table(user):
    """Enhanced transaction history with filters and INR formatting."""
    st.markdown("### 📜 Transaction History")

    with st.expander("🔍 Filter Transactions", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            start_date = st.date_input(
                "From Date", value=date.today() - timedelta(days=30)
            )
        with c2:
            end_date = st.date_input("To Date", value=date.today())
        with c3:
            category = st.selectbox(
                "Category",
                [
                    "All", "Food", "Travel", "Bills", "Shopping",
                    "Entertainment", "Health", "Education",
                    "Salary", "Investment", "Other",
                ],
            )
        with c4:
            type_ = st.selectbox("Type", ["All", "income", "expense"])

    transactions = get_transactions(
        user["id"],
        start_date=start_date,
        end_date=end_date,
        category=category,
        type_=type_,
    )

    if not transactions:
        st.info("📭 No transactions match your filters.")
        return

    # Filtered summary
    total_filtered_income = sum(
        t["amount"] for t in transactions if t["type"] == "income"
    )
    total_filtered_expense = sum(
        t["amount"] for t in transactions if t["type"] == "expense"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("📥 Filtered Income", format_inr(total_filtered_income))
    c2.metric("📤 Filtered Expense", format_inr(total_filtered_expense))
    c3.metric(
        "💼 Net",
        format_inr(safe_subtract(total_filtered_income, total_filtered_expense)),
    )

    # Table
    df = pd.DataFrame(transactions)
    df_display = df[["date", "type", "category", "amount", "description"]].copy()
    df_display["amount"] = df_display["amount"].apply(format_inr)
    df_display["type"] = df_display["type"].apply(
        lambda x: f"📥 {x.title()}" if x == "income" else f"📤 {x.title()}"
    )
    df_display.columns = [
        "📅 Date", "Type", "🏷️ Category", "💰 Amount", "📝 Description",
    ]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Delete option
    with st.expander("🗑️ Delete a Transaction"):
        options = {
            f"{t['date']} | {t['type'].title()} | {format_inr(t['amount'])} | {t['category']}": t[
                "id"
            ]
            for t in transactions
        }
        if options:
            selected = st.selectbox(
                "Select a transaction to delete", list(options.keys())
            )
            if st.button("🗑️ Delete Selected", use_container_width=True):
                delete_transaction(options[selected], user["id"])
                st.success("✅ Transaction deleted.")
                st.rerun()
