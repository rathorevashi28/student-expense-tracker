# Student Expense Tracker

A full-stack web application built with Python and Flask where students can track their daily expenses, set monthly budgets, and predict next month's spending using Machine Learning.

**Live Demo:**  https://web-production-eb9f7.up.railway.app

---

## Features

- Register and Login — each user sees only their own data
- Add expenses and money received (transfers in/out)
- Dashboard with spending summary and charts
- Budget alerts — turns yellow at 60%, red at 80% usage
- Full transaction history with Edit and Delete
- Set monthly budget manually or let it auto-reset
- Predict next month's spending using Linear Regression
- REST API — get expense data as JSON

---

## Pages

| Page | What it does |
|---|---|
| Login / Register | User authentication |
| Dashboard | Overview — cards, charts, recent transactions |
| Add Transaction | Add expense or money received |
| History | All transactions with edit and delete |
| Set Budget | Set budget for any month |
| Predict | Next month spending prediction with warning |

---

## REST API

```
GET /api/expenses  → all transactions as JSON
GET /api/summary   → spending summary, budget, prediction
```

Must be logged in to use the API.

---

## Tech Stack

| Tech | Use |
|---|---|
| Python | Main language |
| Flask | Web framework — routes and pages |
| MySQL | Database — users, expenses, budgets |
| Pandas | Data processing for charts and prediction |
| NumPy | Numerical calculations |
| Scikit-learn | Linear Regression for prediction |
| Matplotlib | Generating spending charts |
| Werkzeug | Password hashing for security |

---

## How to Run Locally

**Step 1 — Install MySQL** and create the database:
```sql
CREATE DATABASE expense_tracker;
```

**Step 2 — Clone the repo**
```bash
git clone https://github.com/rathorevashi28/student-expense-tracker
cd student-expense-tracker
```

**Step 3 — Install libraries**
```bash
pip install -r requirements.txt
```

**Step 4 — Configure database** in `app.py`:
```python
DB = dict(
    host     = 'localhost',
    user     = 'root',
    password = 'your_mysql_password',
    db       = 'expense_tracker',
)
```

**Step 5 — Run**
```bash
python app.py
```

Open `http://localhost:5000` in your browser.

---

## Project Structure

```
expense_tracker/
├── app.py               ← main Flask application
├── requirements.txt     ← all libraries
├── Procfile             ← for Railway deployment
├── railway.json         ← Railway config
├── database.sql         ← database setup
├── templates/
│   ├── base.html        ← shared layout with navbar
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── add.html
│   ├── history.html
│   ├── edit.html
│   ├── budget.html
│   └── predict.html
└── static/
    ├── css/style.css
    └── charts/          ← auto-generated chart images
```

---

## Author

**Vashistha Rathore**
- GitHub: [github.com/rathorevashi28](https://github.com/rathorevashi28)
- LinkedIn: [linkedin.com/in/vashistha-rathore-715050289](https://linkedin.com/in/vashistha-rathore-715050289)
