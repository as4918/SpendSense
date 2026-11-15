# SpendSense feature notes

## Safe-to-Spend
Daily estimate = max(0, min(monthly cash remaining, remaining category budget)) / days left in current month.

## Roommate Splitter
Each shared expense is divided equally among unique participant names. The payer receives credit for the full amount; each participant is charged their equal share. Positive net balance means they should receive money; negative means they owe money.

## Budget Alerts
A notification is shown when a newly entered expense crosses 70%, 90% or 100% of the category's configured budget.

## Spending Insights
Shows this calendar week's expenses against the previous calendar week, the largest recorded expense category, and simple budget observations.

## Savings Challenges
Users can create a named target and record contributions. Progress is retained in SQLite.
