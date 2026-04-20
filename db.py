"""
Database module with SQLite.
Uses Decimal arithmetic for accurate money calculations.
"""

import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

DB_NAME = "expense_tracker.db"


def get_connection():
    """Get SQLite database connection with row factory."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize all database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            date TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            monthly_limit REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def _round_money(value):
    """Round a monetary value to 2 decimals accurately."""
    try:
        return float(
            Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )
    except Exception:
        return 0.0


def add_transaction(user_id, amount, category, type_, date, description=""):
    """Add a new transaction with rounded amount."""
    amount = _round_money(amount)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO transactions (user_id, amount, category, type, date, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (user_id, amount, category, type_, date, description),
    )
    conn.commit()
    conn.close()


def get_transactions(
    user_id, start_date=None, end_date=None, category=None, type_=None
):
    """Fetch transactions with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM transactions WHERE user_id = ?"
    params = [user_id]

    if start_date:
        query += " AND date >= ?"
        params.append(str(start_date))
    if end_date:
        query += " AND date <= ?"
        params.append(str(end_date))
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if type_ and type_ != "All":
        query += " AND type = ?"
        params.append(type_)

    query += " ORDER BY date DESC, id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_transaction(transaction_id, user_id):
    """Delete a transaction by id and user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, user_id),
    )
    conn.commit()
    conn.close()


def get_totals(user_id):
    """Get accurate income, expense and balance totals using Decimal."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT type, amount FROM transactions WHERE user_id = ?", (user_id,)
    )

    income = Decimal("0")
    expense = Decimal("0")

    for row in cursor.fetchall():
        amt = Decimal(str(row["amount"]))
        if row["type"] == "income":
            income += amt
        else:
            expense += amt

    conn.close()

    return {
        "income": float(income.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "expense": float(expense.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "balance": float(
            (income - expense).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        ),
    }


def set_budget(user_id, limit):
    """Set or update monthly budget limit."""
    limit = _round_money(limit)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO budgets (user_id, monthly_limit) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET monthly_limit = excluded.monthly_limit
    """,
        (user_id, limit),
    )
    conn.commit()
    conn.close()


def get_budget(user_id):
    """Get user's monthly budget limit."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT monthly_limit FROM budgets WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return _round_money(row["monthly_limit"]) if row else 0.0


def get_monthly_expense(user_id):
    """Get current month total expense using Decimal for accuracy."""
    conn = get_connection()
    cursor = conn.cursor()
    current_month = datetime.now().strftime("%Y-%m")
    cursor.execute(
        """
        SELECT amount FROM transactions
        WHERE user_id = ? AND type = 'expense' AND date LIKE ?
    """,
        (user_id, f"{current_month}%"),
    )

    total = Decimal("0")
    for row in cursor.fetchall():
        total += Decimal(str(row["amount"]))

    conn.close()
    return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def get_category_totals(user_id, type_="expense"):
    """Get category-wise totals with Decimal accuracy."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT category, amount FROM transactions
        WHERE user_id = ? AND type = ?
    """,
        (user_id, type_),
    )

    totals = {}
    for row in cursor.fetchall():
        cat = row["category"]
        amt = Decimal(str(row["amount"]))
        totals[cat] = totals.get(cat, Decimal("0")) + amt

    conn.close()
    return {
        k: float(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for k, v in totals.items()
    }


# ==================== ADMIN DATABASE FUNCTIONS ====================


def get_all_users():
    """Fetch all registered users for admin panel."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, is_active, created_at FROM users ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_transactions():
    """Fetch all transactions across all users for admin panel."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.*, u.username
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        ORDER BY t.date DESC, t.id DESC
    """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_user_count():
    """Get total number of registered users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    row = cursor.fetchone()
    conn.close()
    return row["count"]


def get_transaction_count():
    """Get total number of transactions."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM transactions")
    row = cursor.fetchone()
    conn.close()
    return row["count"]


def get_platform_totals():
    """Get platform-wide income, expense, balance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT type, amount FROM transactions")

    income = Decimal("0")
    expense = Decimal("0")

    for row in cursor.fetchall():
        amt = Decimal(str(row["amount"]))
        if row["type"] == "income":
            income += amt
        else:
            expense += amt

    conn.close()
    return {
        "income": float(income.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "expense": float(expense.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "balance": float(
            (income - expense).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        ),
    }


def get_user_stats():
    """Get per-user statistics for admin."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            u.id,
            u.username,
            u.is_active,
            u.created_at,
            COUNT(t.id) as total_transactions,
            COALESCE(SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END), 0) as total_expense
        FROM users u
        LEFT JOIN transactions t ON u.id = t.user_id
        GROUP BY u.id
        ORDER BY u.id ASC
    """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def toggle_user_status(user_id):
    """Activate or deactivate a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_status = 0 if row["is_active"] else 1
        cursor.execute(
            "UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id)
        )
        conn.commit()
    conn.close()


def delete_user(user_id):
    """Delete a user and all their data."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM budgets WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def admin_delete_transaction(transaction_id):
    """Admin can delete any transaction."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()
