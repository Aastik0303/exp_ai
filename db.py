import sqlite3
from datetime import datetime

DB_NAME = "expense_tracker.db"


def get_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transactions table
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

    # Budget table (for alerts)
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


def add_transaction(user_id, amount, category, type_, date, description=""):
    """Add a new transaction."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, amount, category, type, date, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, amount, category, type_, date, description))
    conn.commit()
    conn.close()


def get_transactions(user_id, start_date=None, end_date=None, category=None, type_=None):
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
    """Delete a transaction."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
    conn.commit()
    conn.close()


def get_totals(user_id):
    """Get total income, expense and balance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT type, COALESCE(SUM(amount), 0) as total
        FROM transactions WHERE user_id = ? GROUP BY type
    """, (user_id,))
    data = {"income": 0.0, "expense": 0.0}
    for row in cursor.fetchall():
        data[row["type"]] = row["total"]
    conn.close()
    data["balance"] = data["income"] - data["expense"]
    return data


def set_budget(user_id, limit):
    """Set monthly budget limit."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO budgets (user_id, monthly_limit) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET monthly_limit = excluded.monthly_limit
    """, (user_id, limit))
    conn.commit()
    conn.close()


def get_budget(user_id):
    """Get user's monthly budget."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT monthly_limit FROM budgets WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["monthly_limit"] if row else 0.0


def get_monthly_expense(user_id):
    """Get current month expense total."""
    conn = get_connection()
    cursor = conn.cursor()
    current_month = datetime.now().strftime("%Y-%m")
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total FROM transactions
        WHERE user_id = ? AND type = 'expense' AND date LIKE ?
    """, (user_id, f"{current_month}%"))
    row = cursor.fetchone()
    conn.close()
    return row["total"]