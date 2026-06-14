# ============================================================
#  Student Expense Tracker
#  Author : Vashistha Rathore
#  GitHub : github.com/rathorevashi28
# ============================================================

from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.linear_model import LinearRegression
from datetime import datetime, date
import os
import json
import calendar

app = Flask(__name__)
app.secret_key = 'expense_tracker_secret_key_2026'

# ── Database config ──────────────────────────────────────
DB = dict(
    host     = os.environ.get('DB_HOST',     'localhost'),
    user     = os.environ.get('DB_USER',     'root'),
    password = os.environ.get('DB_PASSWORD', 'vashi128'),
    database    = os.environ.get('DB_NAME',     'expense_tracker'),
    charset  = 'utf8mb4',
    cursorclass = pymysql.cursors.DictCursor
)

CATEGORIES = ['Food', 'Travel', 'Books', 'Entertainment',
              'Shopping', 'Other']

CAT_COLORS = {
    'Food': '#3B82F6', 'Travel': '#10B981', 'Books': '#F59E0B',
    'Entertainment': '#8B5CF6', 'Shopping': '#EF4444', 'Other': '#6B7280'
}

# ── DB helpers ────────────────────────────────────────────
def get_db():
    return pymysql.connect(**DB)

def init_db():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80)  UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            budget   FLOAT DEFAULT 5000,
            created  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            user_id    INT NOT NULL,
            type       ENUM('expense','income') NOT NULL,
            amount     FLOAT NOT NULL,
            category   VARCHAR(50),
            note       VARCHAR(200),
            date       DATE NOT NULL,
            created    DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            user_id  INT NOT NULL,
            month    INT NOT NULL,
            year     INT NOT NULL,
            amount   FLOAT NOT NULL,
            UNIQUE KEY uniq_budget (user_id, month, year),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

# ── Auth helpers ──────────────────────────────────────────
def logged_in():
    return 'user_id' in session

def current_user():
    if not logged_in():
        return None
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    u = cur.fetchone()
    conn.close()
    return u

# ── Budget helpers ────────────────────────────────────────
def get_budget(user_id, month, year):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        "SELECT amount FROM budgets WHERE user_id=%s AND month=%s AND year=%s",
        (user_id, month, year))
    row = cur.fetchone()
    if not row:
        # fallback to default budget on user profile
        cur.execute("SELECT budget FROM users WHERE id=%s", (user_id,))
        u = cur.fetchone()
        conn.close()
        return u['budget'] if u else 5000
    conn.close()
    return row['amount']

def get_monthly_spent(user_id, month, year):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(amount),0) as total
        FROM expenses
        WHERE user_id=%s AND type='expense'
          AND MONTH(date)=%s AND YEAR(date)=%s
    """, (user_id, month, year))
    row = cur.fetchone()
    conn.close()
    return row['total']

def get_monthly_income(user_id, month, year):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(amount),0) as total
        FROM expenses
        WHERE user_id=%s AND type='income'
          AND MONTH(date)=%s AND YEAR(date)=%s
    """, (user_id, month, year))
    row = cur.fetchone()
    conn.close()
    return row['total']

def budget_alert(user_id):
    today = date.today()
    budget = get_budget(user_id, today.month, today.year)
    spent  = get_monthly_spent(user_id, today.month, today.year)
    if budget == 0:
        return 'green', 0, budget, spent
    pct = (spent / budget) * 100
    if pct >= 80:
        level = 'red'
    elif pct >= 60:
        level = 'yellow'
    else:
        level = 'green'
    return level, round(pct, 1), budget, spent

# ── Chart generator ───────────────────────────────────────
def make_chart(user_id):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id=%s AND type='expense'
          AND MONTH(date)=MONTH(CURDATE()) AND YEAR(date)=YEAR(CURDATE())
        GROUP BY category
    """, (user_id,))
    rows = cur.fetchall()

    cur.execute("""
        SELECT MONTH(date) as m, YEAR(date) as y, SUM(amount) as total
        FROM expenses
        WHERE user_id=%s AND type='expense'
        GROUP BY YEAR(date), MONTH(date)
        ORDER BY y, m
        LIMIT 6
    """, (user_id,))
    monthly = cur.fetchall()
    conn.close()

    os.makedirs('static/charts', exist_ok=True)

    # Pie chart — category breakdown
    fig, ax = plt.subplots(figsize=(5, 4))
    if rows:
        labels = [r['category'] for r in rows]
        sizes  = [r['total']    for r in rows]
        colors = [CAT_COLORS.get(l, '#6B7280') for l in labels]
        ax.pie(sizes, labels=labels, colors=colors,
               autopct='%1.1f%%', startangle=140,
               textprops={'fontsize': 9})
        ax.set_title('This Month by Category', fontsize=11, fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No data yet', ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='grey')
        ax.set_title('This Month by Category', fontsize=11)
    plt.tight_layout()
    plt.savefig(f'static/charts/pie_{user_id}.png', dpi=120)
    plt.close()

    # Bar chart — last 6 months
    fig, ax = plt.subplots(figsize=(6, 3.5))
    if monthly:
        labels = [f"{calendar.month_abbr[r['m']]} {r['y']}" for r in monthly]
        vals   = [r['total'] for r in monthly]
        bars   = ax.bar(labels, vals, color='#3B82F6', alpha=0.85, width=0.5)
        ax.bar_label(bars, fmt='₹%.0f', fontsize=7, padding=2)
        ax.set_ylabel('Amount (₹)')
        ax.set_title('Monthly Spending (Last 6 Months)',
                     fontsize=11, fontweight='bold')
        ax.tick_params(axis='x', labelsize=8)
    else:
        ax.text(0.5, 0.5, 'No data yet', ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='grey')
        ax.set_title('Monthly Spending', fontsize=11)
    plt.tight_layout()
    plt.savefig(f'static/charts/bar_{user_id}.png', dpi=120)
    plt.close()

# ── ML Prediction ─────────────────────────────────────────
def predict_next_month(user_id):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT MONTH(date) as m, YEAR(date) as y,
               SUM(amount) as total
        FROM expenses
        WHERE user_id=%s AND type='expense'
        GROUP BY YEAR(date), MONTH(date)
        ORDER BY y, m
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()

    if len(rows) < 2:
        return None, None

    df = pd.DataFrame(rows)
    df['index'] = range(len(df))

    X = df[['index']].values
    y = df['total'].values

    model = LinearRegression()
    model.fit(X, y)

    next_idx = np.array([[len(df)]])
    prediction = model.predict(next_idx)[0]
    prediction = max(0, round(prediction, 2))

    return prediction, df['total'].tolist()

# ════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════

# ── Register ──────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        budget   = float(request.form.get('budget', 5000))
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')
        hashed = generate_password_hash(password)
        try:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password, budget) VALUES (%s,%s,%s)",
                (username, hashed, budget))
            conn.commit()
            conn.close()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except pymysql.err.IntegrityError:
            flash('Username already taken.', 'error')
    return render_template('register.html')

# ── Login ─────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def login():
    if logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id']  = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        flash('Wrong username or password.', 'error')
    return render_template('login.html')

# ── Logout ────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Dashboard ─────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if not logged_in():
        return redirect(url_for('login'))
    user  = current_user()
    today = date.today()
    spent  = get_monthly_spent(user['id'], today.month, today.year)
    income = get_monthly_income(user['id'], today.month, today.year)
    budget = get_budget(user['id'], today.month, today.year)
    balance = income - spent
    level, pct, bud, sp = budget_alert(user['id'])
    make_chart(user['id'])

    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT * FROM expenses WHERE user_id=%s
        ORDER BY date DESC LIMIT 5
    """, (user['id'],))
    recent = cur.fetchall()
    conn.close()

    return render_template('dashboard.html',
        user=user, spent=spent, income=income,
        budget=budget, balance=balance,
        alert_level=level, alert_pct=pct,
        recent=recent, month=today.strftime('%B %Y'))

# ── Add Transaction ───────────────────────────────────────
@app.route('/add', methods=['GET', 'POST'])
def add():
    if not logged_in():
        return redirect(url_for('login'))
    level, pct, bud, sp = budget_alert(session['user_id'])
    if request.method == 'POST':
        tx_type  = request.form['type']
        amount   = float(request.form['amount'])
        category = request.form.get('category', 'Other')
        note     = request.form.get('note', '')
        tx_date  = request.form.get('date', date.today().isoformat())
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO expenses (user_id, type, amount, category, note, date)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (session['user_id'], tx_type, amount, category, note, tx_date))
        conn.commit()
        conn.close()
        flash('Transaction added!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add.html',
        categories=CATEGORIES,
        alert_level=level, alert_pct=pct, budget=bud, spent=sp)

# ── History ───────────────────────────────────────────────
@app.route('/history')
def history():
    if not logged_in():
        return redirect(url_for('login'))
    level, pct, bud, sp = budget_alert(session['user_id'])
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT * FROM expenses WHERE user_id=%s
        ORDER BY date DESC
    """, (session['user_id'],))
    records = cur.fetchall()
    conn.close()
    return render_template('history.html',
        records=records,
        alert_level=level, alert_pct=pct, budget=bud, spent=sp)

# ── Edit ─────────────────────────────────────────────────
@app.route('/edit/<int:eid>', methods=['GET', 'POST'])
def edit(eid):
    if not logged_in():
        return redirect(url_for('login'))
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE id=%s AND user_id=%s",
                (eid, session['user_id']))
    rec = cur.fetchone()
    if not rec:
        conn.close()
        return redirect(url_for('history'))
    if request.method == 'POST':
        tx_type  = request.form['type']
        amount   = float(request.form['amount'])
        category = request.form.get('category', 'Other')
        note     = request.form.get('note', '')
        tx_date  = request.form['date']
        cur.execute("""
            UPDATE expenses
            SET type=%s, amount=%s, category=%s, note=%s, date=%s
            WHERE id=%s AND user_id=%s
        """, (tx_type, amount, category, note, tx_date,
              eid, session['user_id']))
        conn.commit()
        conn.close()
        flash('Transaction updated!', 'success')
        return redirect(url_for('history'))
    conn.close()
    level, pct, bud, sp = budget_alert(session['user_id'])
    return render_template('edit.html', rec=rec,
        categories=CATEGORIES,
        alert_level=level, alert_pct=pct, budget=bud, spent=sp)

# ── Delete ────────────────────────────────────────────────
@app.route('/delete/<int:eid>')
def delete(eid):
    if not logged_in():
        return redirect(url_for('login'))
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=%s AND user_id=%s",
                (eid, session['user_id']))
    conn.commit()
    conn.close()
    flash('Transaction deleted.', 'success')
    return redirect(url_for('history'))

# ── Set Budget ────────────────────────────────────────────
@app.route('/budget', methods=['GET', 'POST'])
def set_budget():
    if not logged_in():
        return redirect(url_for('login'))
    today = date.today()
    level, pct, bud, sp = budget_alert(session['user_id'])
    if request.method == 'POST':
        amount = float(request.form['amount'])
        month  = int(request.form.get('month', today.month))
        year   = int(request.form.get('year',  today.year))
        set_default = request.form.get('set_default') == 'on'
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO budgets (user_id, month, year, amount)
            VALUES (%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE amount=%s
        """, (session['user_id'], month, year, amount, amount))
        if set_default:
            cur.execute("UPDATE users SET budget=%s WHERE id=%s",
                        (amount, session['user_id']))
        conn.commit()
        conn.close()
        flash('Budget updated!', 'success')
        return redirect(url_for('dashboard'))
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years  = list(range(today.year - 1, today.year + 3))
    return render_template('budget.html',
        months=months, years=years,
        current_month=today.month, current_year=today.year,
        alert_level=level, alert_pct=pct, budget=bud, spent=sp)

# ── Predict ───────────────────────────────────────────────
@app.route('/predict')
def predict():
    if not logged_in():
        return redirect(url_for('login'))
    level, pct, bud, sp = budget_alert(session['user_id'])
    prediction, history = predict_next_month(session['user_id'])
    today  = date.today()
    budget = get_budget(session['user_id'], today.month, today.year)
    warn   = prediction and prediction > budget
    return render_template('predict.html',
        prediction=prediction, history=history,
        budget=budget, warn=warn,
        alert_level=level, alert_pct=pct, spent=sp)

# ════════════════════════════════════════════════════════
# REST API ENDPOINTS
# ════════════════════════════════════════════════════════

@app.route('/api/expenses', methods=['GET'])
def api_expenses():
    """Returns all expenses for logged-in user as JSON"""
    if not logged_in():
        return jsonify({'error': 'Not authenticated'}), 401
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
    "SELECT id, type, amount, category, note,"
    " DATE_FORMAT(date, '%%Y-%%m-%%d') as date"
    " FROM expenses WHERE user_id=%s"
    " ORDER BY date DESC",
    (session['user_id'],))
    rows = cur.fetchall()
    conn.close()
    return jsonify({
        'user'    : session['username'],
        'count'   : len(rows),
        'expenses': rows
    })

@app.route('/api/summary', methods=['GET'])
def api_summary():
    """Returns spending summary for logged-in user as JSON"""
    if not logged_in():
        return jsonify({'error': 'Not authenticated'}), 401
    today  = date.today()
    uid    = session['user_id']
    spent  = get_monthly_spent(uid, today.month, today.year)
    income = get_monthly_income(uid, today.month, today.year)
    budget = get_budget(uid, today.month, today.year)
    prediction, _ = predict_next_month(uid)

    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id=%s AND type='expense'
          AND MONTH(date)=MONTH(CURDATE())
          AND YEAR(date)=YEAR(CURDATE())
        GROUP BY category
    """, (uid,))
    cats = cur.fetchall()
    conn.close()

    return jsonify({
        'user'            : session['username'],
        'month'           : today.strftime('%B %Y'),
        'budget'          : budget,
        'spent_this_month': spent,
        'income_this_month': income,
        'balance'         : income - spent,
        'budget_used_pct' : round((spent/budget*100), 1) if budget else 0,
        'category_breakdown': cats,
        'next_month_prediction': prediction
    })

# ════════════════════════════════════════════════════════
# Create tables on startup always
init_db()

if __name__ == '__main__':
    app.run(debug=True)
