# SpendSense – Student Money Companion

A Python + Tkinter desktop application designed around common student money-management problems.

## Features

1. **Safe-to-Spend Calculator** – estimates a daily spending amount using this month's recorded income, expenses, category budgets and remaining days.
2. **Roommate Expense Splitter** – records shared bills, divides them equally among participants and calculates net balances (who should receive or pay money).
3. **Smart Budget Alerts** – displays alerts when a new expense crosses 70%, 90% or 100% of its category budget.
4. **Spending Behaviour Insights** – compares this week with last week, highlights the highest-spending category and identifies categories near/over budget.
5. **Savings Challenges** – create a savings target and add contributions to track progress.
6. Existing dashboard, transactions, category-coloured expense wheel, budget planner and budgeting guide.
7. **SQLite persistence** – transactions, shared expenses and savings challenges remain saved after closing the app.

## Run

Requirements: Python 3.9+ with Tkinter available.

```bash
python main.py
```

Open this folder in VS Code and run `main.py` using the Python extension or terminal.

## Data storage

The app creates `spendsense.db` in the same folder as `main.py` on first run. Keep this file to retain your records. To reset demo data, close the app and delete `spendsense.db`; the sample transactions will be loaded again on next launch.

## Notes / limitations

- Roommate expenses are split equally between the listed participants. This version calculates net balances but does not process payments.
- Safe-to-spend is an estimate based on entries recorded in the current calendar month; add allowance/income transactions for a useful calculation.
- Weekly insights use recorded transaction dates and simple comparisons, not predictive AI.
- This is an educational budgeting tool, not professional financial advice.
