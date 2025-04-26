from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages
DATABASE = 'expense_tracker.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize Database
def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                payment_mode TEXT NOT NULL
            );
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE NOT NULL,
                limit_amount REAL NOT NULL
            );
        ''')

@app.route('/')
def index():
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses ORDER BY date DESC').fetchall()
    total_expense = conn.execute('SELECT SUM(amount) FROM expenses').fetchone()[0] or 0
    upi_expense = conn.execute("SELECT SUM(amount) FROM expenses WHERE payment_mode = 'UPI'").fetchone()[0] or 0
    cash_expense = conn.execute("SELECT SUM(amount) FROM expenses WHERE payment_mode = 'Cash'").fetchone()[0] or 0
    card_expense = conn.execute("SELECT SUM(amount) FROM expenses WHERE payment_mode = 'Card'").fetchone()[0] or 0
    conn.close()
    return render_template('index.html', expenses=expenses, total_expense=total_expense,
                           upi_expense=upi_expense, cash_expense=cash_expense, card_expense=card_expense)

@app.route('/add', methods=('GET', 'POST'))
def add_expense():
    if request.method == 'POST':
        date = request.form['date']
        category = request.form['category']
        amount = request.form['amount']
        description = request.form['description']
        payment_mode = request.form['payment_mode']

        conn = get_db_connection()
        conn.execute('INSERT INTO expenses (date, category, amount, description, payment_mode) VALUES (?, ?, ?, ?, ?)',
                     (date, category, amount, description, payment_mode))
        conn.commit()
        conn.close()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_expense.html')

@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit_expense(id):
    conn = get_db_connection()
    expense = conn.execute('SELECT * FROM expenses WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        date = request.form['date']
        category = request.form['category']
        amount = request.form['amount']
        description = request.form['description']
        payment_mode = request.form['payment_mode']

        conn.execute('UPDATE expenses SET date = ?, category = ?, amount = ?, description = ?, payment_mode = ? WHERE id = ?',
                     (date, category, amount, description, payment_mode, id))
        conn.commit()
        conn.close()
        flash('Expense updated successfully!', 'info')
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_expense.html', expense=expense)

@app.route('/delete/<int:id>')
def delete_expense(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM expenses WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Expense deleted!', 'danger')
    return redirect(url_for('index'))

@app.route('/report')
def report():
    conn = get_db_connection()
    report_data = conn.execute('SELECT category, SUM(amount) as total FROM expenses GROUP BY category').fetchall()
    budget_data = conn.execute('SELECT * FROM budget').fetchall()
    conn.close()
    return render_template('report.html', report_data=report_data, budget_data=budget_data)

@app.route('/set_budget', methods=('POST',))
def set_budget():
    category = request.form['category']
    limit_amount = request.form['limit_amount']

    conn = get_db_connection()
    conn.execute('INSERT OR REPLACE INTO budget (category, limit_amount) VALUES (?, ?)',
                 (category, limit_amount))
    conn.commit()
    conn.close()
    flash('Budget set successfully!', 'success')
    return redirect(url_for('report'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
