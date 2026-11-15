import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, timedelta
from collections import defaultdict
from pathlib import Path
import sqlite3
import calendar
import ctypes
import sys


def enable_windows_dpi_awareness():
    """Ask Windows to render Tk widgets at the display's native DPI."""
    if sys.platform != "win32":
        return
    try:
        # Per-monitor DPI awareness (Windows 10, newer APIs).
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            # System DPI awareness fallback.
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


enable_windows_dpi_awareness()

# SpendSense - White Edition
# Python + Tkinter student money companion. Transactions, shared bills and goals persist in SQLite.

BG = "#F5F7FB"
WHITE = "#FFFFFF"
SIDEBAR = "#FFFFFF"
TEXT = "#263247"
MUTED = "#718096"
BORDER = "#E3E8F0"
PURPLE = "#7357C8"
PURPLE_LIGHT = "#F0ECFC"
GREEN = "#2E9D62"
RED = "#D9535F"
BLUE = "#3478C8"
ORANGE = "#D99032"
TEAL = "#199B94"
GREY = "#8794A8"
PINK = "#D66A9A"

CATEGORY_COLORS = {
    # Each category has its own distinct colour for quick visual recognition.
    "Groceries": "#2E9D62",       # Green
    "Beauty": "#D9535F",          # Red
    "Food": "#3478C8",            # Blue
    "Shopping": "#8B63C7",        # Purple
    "Transport": "#E39A32",       # Orange
    "Education": "#159DAD",       # Cyan
    "Bills": "#687386",           # Slate grey
    "Entertainment": "#D65A9A",   # Pink
    "Health": "#A58A18",          # Mustard
    "Other": "#9A6848",           # Brown
    "Income": "#263247",          # Navy
}
EXPENSE_CATEGORIES = [c for c in CATEGORY_COLORS if c != "Income"]
ALL_CATEGORIES = EXPENSE_CATEGORIES + ["Income"]

SAMPLE_TRANSACTIONS = [
    {"date": date.today() - timedelta(days=5), "title": "Monthly allowance", "category": "Income", "amount": 12000.0, "kind": "Income"},
    {"date": date.today() - timedelta(days=4), "title": "Weekly groceries", "category": "Groceries", "amount": 1250.0, "kind": "Expense"},
    {"date": date.today() - timedelta(days=3), "title": "Lunch with friends", "category": "Food", "amount": 480.0, "kind": "Expense"},
    {"date": date.today() - timedelta(days=3), "title": "Skincare essentials", "category": "Beauty", "amount": 790.0, "kind": "Expense"},
    {"date": date.today() - timedelta(days=2), "title": "Cab ride", "category": "Transport", "amount": 260.0, "kind": "Expense"},
    {"date": date.today() - timedelta(days=1), "title": "Online shopping", "category": "Shopping", "amount": 1100.0, "kind": "Expense"},
    {"date": date.today(), "title": "Freelance project", "category": "Income", "amount": 2500.0, "kind": "Income"},
]

class SpendSenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SpendSense | Smart Expense Tracker")
        self.geometry("1450x900")
        self.minsize(1250, 760)
        self.configure(bg=BG)
        self.db_path = Path(__file__).with_name("spendsense.db")
        self._init_database()
        self.transactions = self._load_transactions()
        if not self.transactions:
            self.transactions = [dict(t) for t in SAMPLE_TRANSACTIONS]
            self._save_transactions()
        self.budgets = {
            "Groceries": 4500, "Beauty": 1800, "Food": 3000,
            "Shopping": 2500, "Transport": 1800, "Education": 1500,
            "Bills": 2500, "Entertainment": 1500, "Health": 1200, "Other": 1000
        }
        self.goals = [
            {"name": "New laptop", "saved": 18000.0, "target": 45000.0},
            {"name": "Emergency fund", "saved": 7500.0, "target": 15000.0},
        ]
        self.active_page = "Overview"
        self._setup_styles()
        self._build_shell()
        self.show_page("Overview")

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("White.Treeview", background=WHITE, foreground=TEXT,
                        fieldbackground=WHITE, rowheight=36, borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("White.Treeview.Heading", background="#F0F3F8",
                        foreground=MUTED, relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("White.Treeview", background=[("selected", "#E9E2FC")],
                  foreground=[("selected", TEXT)])
        style.configure("White.TCombobox", fieldbackground=WHITE, background=WHITE,
                        foreground=TEXT, arrowcolor=TEXT, bordercolor=BORDER,
                        lightcolor=WHITE, darkcolor=WHITE)
        style.map("White.TCombobox",
                  fieldbackground=[("readonly", WHITE), ("focus", WHITE)],
                  background=[("readonly", WHITE), ("active", WHITE)],
                  foreground=[("readonly", TEXT), ("disabled", MUTED)],
                  selectbackground=[("readonly", WHITE)],
                  selectforeground=[("readonly", TEXT)])
        self.option_add("*TCombobox*Listbox.background", WHITE)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", PURPLE_LIGHT)
        self.option_add("*TCombobox*Listbox.selectForeground", TEXT)

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width= 350,
                                highlightbackground=BORDER, highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="◈  SpendSense", bg=SIDEBAR, fg=PURPLE,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=22, pady=(27, 8))
        tk.Label(self.sidebar, text="YOUR MONEY, IN PERSPECTIVE", bg=SIDEBAR, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=24, pady=(0, 30))
        tk.Label(self.sidebar, text="WORKSPACE", bg=SIDEBAR, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=23, pady=(0, 10))
        self.nav_buttons = {}
        nav_items = [
            ("Overview", "▦"), ("Transactions", "⇄"), ("Expense Analysis", "◔"),
            ("Safe to Spend", "₹"), ("Roommate Splitter", "⇄"),
            ("Budget Planner", "◷"), ("Spending Insights", "✧"),
            ("Budgeting Guide", "✦"), ("Savings Challenges", "◎")
        ]
        for name, icon in nav_items:
            btn = tk.Button(self.sidebar, text=f"{icon}   {name}", anchor="w",
                            command=lambda n=name: self.show_page(n),
                            bg=SIDEBAR, fg=MUTED, activebackground=PURPLE_LIGHT,
                            activeforeground=PURPLE, relief="flat", bd=0,
                            padx=17, pady=12, font=("Segoe UI", 10),
                            cursor="hand2")
            btn.pack(fill="x", padx=11, pady=3)
            self.nav_buttons[name] = btn
        tk.Frame(self.sidebar, bg=SIDEBAR).pack(expand=True, fill="both")
        tk.Label(self.sidebar, text="Make every rupee count.", bg=SIDEBAR,
                 fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=23, pady=(0, 7))
        tk.Label(self.sidebar, text="SPENDSENSE  •  WHITE EDITION", bg=SIDEBAR,
                 fg="#A0A9B8", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=23, pady=(0, 22))

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self.header = tk.Frame(self.main, bg=BG)
        self.header.pack(fill="x", padx=30, pady=(25, 18))
        self.title_label = tk.Label(self.header, text="Overview", bg=BG, fg=TEXT,
                                    font=("Segoe UI", 25, "bold"))
        self.title_label.pack(side="left")
        self.add_btn = self.button(self.header, "+  Add transaction", self.open_transaction_dialog,
                                   bg=PURPLE, fg=WHITE, padx=17, pady=10)
        self.add_btn.pack(side="right")
        self.body = tk.Frame(self.main, bg=BG)
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 25))

    def button(self, parent, text, command, bg=WHITE, fg=TEXT, padx=13, pady=8):
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground=PURPLE_LIGHT, activeforeground=PURPLE,
                         relief="flat", bd=0, padx=padx, pady=pady,
                         font=("Segoe UI", 9, "bold"), cursor="hand2")

    def card(self, parent, padx=18, pady=17):
        frame = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        frame.configure(padx=padx, pady=pady)
        return frame

    def label(self, parent, text, size=11, color=TEXT, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", WHITE), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def clear_body(self):
        for child in self.body.winfo_children():
            child.destroy()

    def show_page(self, page):
        self.active_page = page
        self.title_label.config(text=page)
        for name, btn in self.nav_buttons.items():
            selected = name == page
            btn.config(bg=PURPLE_LIGHT if selected else SIDEBAR,
                       fg=PURPLE if selected else MUTED,
                       font=("Segoe UI", 10, "bold" if selected else "normal"))
        self.clear_body()
        if page in ("Overview", "Transactions"):
            self.add_btn.pack(side="right")
        else:
            self.add_btn.pack_forget()
        {
            "Overview": self._overview,
            "Transactions": self._transactions_page,
            "Expense Analysis": self._analytics_page,
            "Safe to Spend": self._safe_to_spend_page,
            "Roommate Splitter": self._roommate_splitter_page,
            "Budget Planner": self._budgets_page,
            "Spending Insights": self._spending_insights_page,
            "Budgeting Guide": self._budget_guide_page,
            "Savings Challenges": self._goals_page,
        }[page]()

    def total(self, kind):
        return sum(t["amount"] for t in self.transactions if t["kind"] == kind)

    def money(self, value):
        return f"₹{value:,.0f}"

    def category_total(self):
        totals = defaultdict(float)
        for t in self.transactions:
            if t["kind"] == "Expense":
                totals[t["category"]] += t["amount"]
        return dict(totals)

    def stat_card(self, parent, heading, value, note, accent):
        p = self.card(parent)
        self.label(p, heading.upper(), 9, MUTED, True).pack(anchor="w")
        self.label(p, value, 23, TEXT, True).pack(anchor="w", pady=(11, 4))
        self.label(p, note, 10, accent).pack(anchor="w")
        return p

    def _overview(self):
        income, expense = self.total("Income"), self.total("Expense")
        stats = tk.Frame(self.body, bg=BG)
        stats.pack(fill="x")
        cards = [
            ("TOTAL BALANCE", self.money(income-expense), "Income minus expenses", PURPLE),
            ("TOTAL INCOME", self.money(income), "Money received", GREEN),
            ("TOTAL EXPENSES", self.money(expense), "Money spent", RED),
        ]
        for i, item in enumerate(cards):
            stats.grid_columnconfigure(i, weight=1, uniform="stats")
            self.stat_card(stats, *item).grid(row=0, column=i, sticky="nsew",
                padx=(0 if i == 0 else 9, 0 if i == 2 else 9))

        lower = tk.Frame(self.body, bg=BG)
        lower.pack(fill="both", expand=True, pady=(17, 0))
        lower.grid_columnconfigure(0, weight=1, uniform="lower")
        lower.grid_columnconfigure(1, weight=1, uniform="lower")
        lower.grid_rowconfigure(0, weight=1)

        chart_card = self.card(lower)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        self.label(chart_card, "Expense breakdown", 14, TEXT, True).pack(anchor="w")
        self.label(chart_card, "BY CATEGORY", 8, MUTED, True).pack(anchor="w", pady=(3, 8))
        chart = tk.Canvas(chart_card, bg=WHITE, highlightthickness=0, height=350)
        chart.pack(fill="both", expand=True)
        self.draw_pie_chart(chart, compact=True)

        recent = self.card(lower)
        recent.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self.label(recent, "Recent transactions", 14, TEXT, True).pack(anchor="w", pady=(0, 10))
        self._make_tree(recent, compact=True)

    def draw_pie_chart(self, canvas, compact=False):
        def draw(_event=None):
            canvas.delete("all")
            totals = self.category_total()
            totals = {k:v for k,v in totals.items() if v > 0}
            w, h = max(canvas.winfo_width(), 400), max(canvas.winfo_height(), 300)
            if not totals:
                canvas.create_text(w/2, h/2, text="No expense data yet", fill=MUTED,
                                   font=("Segoe UI", 10))
                return
            total = sum(totals.values())
            if compact:
                # Larger dashboard wheel while reserving a clear legend column.
                d = min(245, h-34, w*0.55)
                x0, y0 = 8, (h-d)/2
            else:
                d = min(330, h-42, w*0.58)
                x0, y0 = 22, (h-d)/2
            start = 90
            for cat, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True):
                extent = amount / total * 360
                canvas.create_arc(x0, y0, x0+d, y0+d, start=start, extent=extent,
                                  fill=CATEGORY_COLORS.get(cat, GREY), outline=WHITE, width=2,
                                  style=tk.PIESLICE)
                start += extent
            canvas.create_oval(x0+d*.31, y0+d*.31, x0+d*.69, y0+d*.69,
                               fill=WHITE, outline=WHITE)
            canvas.create_text(x0+d/2, y0+d/2-7, text=self.money(total),
                               fill=TEXT, font=("Segoe UI", 10, "bold"))
            canvas.create_text(x0+d/2, y0+d/2+13, text="TOTAL SPENT",
                               fill=MUTED, font=("Segoe UI", 6, "bold"))
            lx = x0+d+18
            ly = max(18, (h-len(totals)*25)/2)
            for cat, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True):
                pct = amount/total*100
                canvas.create_oval(lx, ly+3, lx+10, ly+13,
                                   fill=CATEGORY_COLORS.get(cat, GREY), outline="")
                canvas.create_text(lx+17, ly+8, anchor="w",
                                   text=f"{cat}  {pct:.0f}%",
                                   fill=TEXT, font=("Segoe UI", 9))
                ly += 25
        canvas.bind("<Configure>", draw)
        self.after(80, draw)

    def _make_tree(self, parent, compact=False):
        wrap = tk.Frame(parent, bg=WHITE)
        wrap.pack(fill="both", expand=True)
        cols = ("date", "title", "category", "kind", "amount")
        tree = ttk.Treeview(wrap, columns=cols, show="headings",
                            height=6 if compact else 13, style="White.Treeview")
        headings = {"date":"DATE", "title":"DESCRIPTION", "category":"CATEGORY",
                    "kind":"TYPE", "amount":"AMOUNT"}
        if compact:
            # Compact dashboard table: keep every column visible without horizontal clipping.
            widths = {"date":58, "title":112, "category":82, "kind":62, "amount":88}
        else:
            widths = {"date":90, "title":190, "category":130, "kind":90, "amount":125}
        for col in cols:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], minwidth=48, anchor="e" if col == "amount" else "w", stretch=True)
        for index, t in enumerate(reversed(self.transactions[-5:] if compact else self.transactions)):
            sign = "+" if t["kind"] == "Income" else "−"
            item = tree.insert("", "end", values=(t["date"].strftime("%d %b"), t["title"],
                t["category"], t["kind"], f"{sign} {self.money(t['amount'])}"))
            tree.tag_configure(t["category"], foreground=CATEGORY_COLORS.get(t["category"], TEXT))
            tree.item(item, tags=(t["category"],))
        tree.pack(fill="both", expand=True)
        return tree

    def _transactions_page(self):
        panel = self.card(self.body)
        panel.pack(fill="both", expand=True)
        top = tk.Frame(panel, bg=WHITE)
        top.pack(fill="x", pady=(0, 12))
        self.label(top, "All transactions", 14, TEXT, True).pack(side="left")
        self.tx_tree = self._make_tree(panel)
        actions = tk.Frame(panel, bg=WHITE)
        actions.pack(fill="x", pady=(12, 0))
        self.button(actions, "Edit selected", self.edit_selected, bg=PURPLE_LIGHT, fg=PURPLE).pack(side="right", padx=(8,0))
        self.button(actions, "Delete selected", self.delete_selected, bg="#FCEBED", fg=RED).pack(side="right")

    def _analytics_page(self):
        wrap = tk.Frame(self.body, bg=BG)
        wrap.pack(fill="both", expand=True)
        wrap.grid_columnconfigure(0, weight=3)
        wrap.grid_columnconfigure(1, weight=2)
        wrap.grid_rowconfigure(0, weight=1)
        chart_card = self.card(wrap)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        self.label(chart_card, "Your expense analysis", 15, TEXT, True).pack(anchor="w")
        self.label(chart_card, "A live view of how your expenses are distributed", 10, MUTED).pack(anchor="w", pady=(4, 5))
        canvas = tk.Canvas(chart_card, bg=WHITE, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        self.draw_pie_chart(canvas, compact=False)

        detail = self.card(wrap)
        detail.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self.label(detail, "Category breakdown", 14, TEXT, True).pack(anchor="w", pady=(0, 15))
        totals = self.category_total()
        total = sum(totals.values())
        if not totals:
            self.label(detail, "Add an expense to see your analysis.", 10, MUTED).pack(anchor="w")
        else:
            for cat, amount in sorted(totals.items(), key=lambda item:item[1], reverse=True):
                row = tk.Frame(detail, bg=WHITE)
                row.pack(fill="x", pady=7)
                tk.Label(row, text="●", fg=CATEGORY_COLORS.get(cat, GREY),
                         bg=WHITE, font=("Segoe UI", 12)).pack(side="left")
                self.label(row, cat, 10, TEXT, True).pack(side="left", padx=7)
                self.label(row, f"{self.money(amount)}  ({amount/total*100:.1f}%)",
                           9, MUTED).pack(side="right")
        tk.Frame(detail, bg=BORDER, height=1).pack(fill="x", pady=15)
        self.label(detail, "TOTAL SPENT", 9, MUTED, True).pack(anchor="w")
        self.label(detail, self.money(total), 22, TEXT, True).pack(anchor="w", pady=(4,0))

    def _budgets_page(self):
        wrap = tk.Frame(self.body, bg=BG)
        wrap.pack(fill="both", expand=True)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_columnconfigure(1, weight=1)
        for i, (cat, limit) in enumerate(self.budgets.items()):
            row, col = divmod(i, 2)
            used = self.category_total().get(cat, 0)
            p = self.card(wrap)
            p.grid(row=row, column=col, sticky="nsew",
                   padx=(0 if col == 0 else 9, 9 if col == 0 else 0), pady=(0, 12))
            head = tk.Frame(p, bg=WHITE)
            head.pack(fill="x")
            tk.Label(head, text="●", bg=WHITE, fg=CATEGORY_COLORS.get(cat, GREY),
                     font=("Segoe UI", 13)).pack(side="left")
            self.label(head, cat, 12, TEXT, True).pack(side="left", padx=7)
            self.label(head, f"{self.money(used)} / {self.money(limit)}", 10, MUTED).pack(side="right")
            pct = min(100, int(used/limit*100)) if limit else 0
            bar = tk.Canvas(p, height=10, bg="#EDF0F5", highlightthickness=0)
            bar.pack(fill="x", pady=(13, 7))
            bar.bind("<Configure>", lambda e, c=bar, v=pct, co=CATEGORY_COLORS.get(cat, PURPLE): self._draw_progress(c,v,co))
            status = "Over budget" if used > limit else ("Almost at limit" if pct >= 80 else "On track")
            status_color = RED if used > limit else (ORANGE if pct >= 80 else GREEN)
            self.label(p, f"{pct}% used  •  {status}", 9, status_color).pack(anchor="w")
        footer = self.card(wrap)
        footer.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(3,0))
        self.label(footer, "Adjust your monthly limits", 12, TEXT, True).pack(side="left")
        self.button(footer, "Edit budgets", self.edit_budgets, bg=PURPLE_LIGHT, fg=PURPLE).pack(side="right")

    def _draw_progress(self, canvas, pct, color):
        canvas.delete("all")
        w = canvas.winfo_width()
        canvas.create_rectangle(0, 0, w, 10, fill="#EDF0F5", outline="")
        canvas.create_rectangle(0, 0, w*pct/100, 10, fill=color, outline="")

    def edit_budgets(self):
        dialog = tk.Toplevel(self)
        dialog.title("Edit monthly budgets")
        dialog.configure(bg=WHITE)
        dialog.transient(self); dialog.grab_set()
        frame = tk.Frame(dialog, bg=WHITE, padx=22, pady=20); frame.pack()
        self.label(frame, "Set category budget limits", 15, TEXT, True).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,12))
        entries = {}
        for i,(cat,amount) in enumerate(self.budgets.items(), start=1):
            self.label(frame, cat, 10, TEXT).grid(row=i,column=0,sticky="w",pady=5,padx=(0,15))
            e=tk.Entry(frame,bg="#F6F8FB",fg=TEXT,relief="flat",width=18,font=("Segoe UI",10))
            e.insert(0,str(amount)); e.grid(row=i,column=1,ipady=6); entries[cat]=e
        def save():
            try:
                new_values={cat:float(e.get()) for cat,e in entries.items()}
                if any(v<=0 for v in new_values.values()): raise ValueError
                self.budgets.update(new_values); dialog.destroy(); self.show_page("Budget Planner")
            except ValueError:
                messagebox.showwarning("Invalid budget","Enter a positive number for every category.",parent=dialog)
        self.button(frame,"Save budgets",save,bg=PURPLE,fg=WHITE).grid(row=len(entries)+1,column=0,columnspan=2,sticky="e",pady=(14,0))
        dialog.update_idletasks()
        dialog.geometry(f"+{self.winfo_rootx()+180}+{self.winfo_rooty()+100}")

    def _budget_guide_page(self):
        wrap = tk.Frame(self.body, bg=BG)
        wrap.pack(fill="both", expand=True)
        intro = self.card(wrap)
        intro.pack(fill="x", pady=(0,13))
        self.label(intro, "A simple way to plan your money", 17, TEXT, True).pack(anchor="w")
        self.label(intro, "The 50/30/20 rule is a popular starting point. It divides your take-home income into needs, wants and savings.",
                   10, MUTED, wraplength=850, justify="left").pack(anchor="w", pady=(7,0))
        grid=tk.Frame(wrap,bg=BG); grid.pack(fill="x")
        sections=[
            ("50%  NEEDS", "Essentials you need to live and study: groceries, rent, utilities, transport and required bills.", BLUE),
            ("30%  WANTS", "Flexible spending: eating out, beauty, entertainment, hobbies and non-essential shopping.", PINK),
            ("20%  SAVINGS", "Savings, emergency fund contributions and paying down debt where applicable.", GREEN)
        ]
        for i,(title,body,color) in enumerate(sections):
            p=self.card(grid); p.grid(row=0,column=i,sticky="nsew",padx=(0 if i==0 else 7,7 if i<2 else 0))
            grid.grid_columnconfigure(i,weight=1)
            self.label(p,title,13,color,True).pack(anchor="w")
            self.label(p,body,10,MUTED,wraplength=230,justify="left").pack(anchor="w",pady=(10,0))
        tips=self.card(wrap); tips.pack(fill="both",expand=True,pady=(13,0))
        self.label(tips,"Practical budgeting guide",15,TEXT,True).pack(anchor="w",pady=(0,8))
        guide=[
            "1. Calculate your monthly take-home income.",
            "2. List essential expenses first and set realistic limits.",
            "3. Choose a spending limit for flexible categories such as food, beauty and shopping.",
            "4. Set a savings target and move that amount aside regularly.",
            "5. Review your expense analysis every week and adjust categories when needed.",
            "6. If the 50/30/20 split does not fit your situation, customise it to your priorities."
        ]
        for line in guide:
            self.label(tips,line,10,TEXT).pack(anchor="w",pady=5)
        self.label(tips,"Example: With ₹20,000 monthly take-home income → ₹10,000 needs, ₹6,000 wants and ₹4,000 savings.",
                   10,PURPLE,True,wraplength=850,justify="left").pack(anchor="w",pady=(12,0))

    def _goals_page(self):
        self._load_goals()
        top = tk.Frame(self.body, bg=BG)
        top.pack(fill="x", pady=(0, 12))
        self.label(top, "Build a savings habit, one step at a time.", 11, MUTED).pack(side="left")
        self.button(top, "+ Create challenge", self._add_savings_challenge,
                    bg=PURPLE, fg=WHITE).pack(side="right")
        wrap=tk.Frame(self.body,bg=BG); wrap.pack(fill="both",expand=True)
        for i,goal in enumerate(self.goals):
            p=self.card(wrap); p.grid(row=0,column=i,sticky="nsew",padx=(0 if i==0 else 9,9 if i==0 else 0))
            wrap.grid_columnconfigure(i,weight=1)
            self.label(p,"SAVINGS GOAL",9,MUTED,True).pack(anchor="w")
            self.label(p,goal["name"],18,TEXT,True).pack(anchor="w",pady=(15,6))
            self.label(p,f'{self.money(goal["saved"])} saved of {self.money(goal["target"])}',10,MUTED).pack(anchor="w",pady=(0,14))
            pct=min(100,int(goal["saved"]/goal["target"]*100)) if goal["target"] else 0
            bar=tk.Canvas(p,height=10,bg="#EDF0F5",highlightthickness=0); bar.pack(fill="x")
            bar.bind("<Configure>",lambda e,c=bar,v=pct:self._draw_progress(c,v,GREEN))
            self.label(p,f"{pct}% complete",9,GREEN,True).pack(anchor="w",pady=(8,0))
            self.button(p, "+ Add savings", lambda g=goal: self._add_savings_contribution(g),
                        bg=PURPLE_LIGHT, fg=PURPLE).pack(anchor="w", pady=(12, 0))
        note=self.card(wrap); note.grid(row=1,column=0,columnspan=2,sticky="ew",pady=(15,0))
        self.label(note,"Keep your goals visible",13,TEXT,True).pack(anchor="w")
        self.label(note,"Track a target amount and check your progress regularly. Consistent small contributions can add up over time.",10,MUTED).pack(anchor="w",pady=(6,0))

    def open_transaction_dialog(self, existing=None):
        dialog=tk.Toplevel(self); dialog.title("Edit transaction" if existing else "Add transaction")
        dialog.configure(bg=WHITE); dialog.resizable(False,False); dialog.transient(self); dialog.grab_set()
        frame=tk.Frame(dialog,bg=WHITE,padx=24,pady=22); frame.pack(fill="both",expand=True)
        self.label(frame,"Edit transaction" if existing else "New transaction",16,TEXT,True).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,15))
        fields={}
        names=["Description","Amount (₹)","Category","Type"]
        for r,name in enumerate(names,start=1):
            self.label(frame,name,10,MUTED).grid(row=r,column=0,sticky="w",pady=7,padx=(0,15))
            if name=="Category":
                widget=ttk.Combobox(frame,values=ALL_CATEGORIES,state="readonly",width=25,style="White.TCombobox")
                widget.set(existing["category"] if existing else "Food")
            elif name=="Type":
                widget=ttk.Combobox(frame,values=["Expense","Income"],state="readonly",width=25,style="White.TCombobox")
                widget.set(existing["kind"] if existing else "Expense")
            else:
                widget=tk.Entry(frame,bg="#F6F8FB",fg=TEXT,insertbackground=TEXT,relief="flat",width=28,font=("Segoe UI",10))
                if existing: widget.insert(0,existing["title"] if name=="Description" else str(existing["amount"]))
            widget.grid(row=r,column=1,sticky="ew",pady=7,ipady=7); fields[name]=widget
        def save():
            title=fields["Description"].get().strip()
            try:
                amount=float(fields["Amount (₹)"].get())
                if not title or amount<=0: raise ValueError
            except ValueError:
                messagebox.showwarning("Invalid details","Enter a description and an amount greater than zero.",parent=dialog); return
            kind=fields["Type"].get(); category=fields["Category"].get()
            if kind=="Income": category="Income"
            elif category=="Income": category="Other"
            record={"date":existing["date"] if existing else date.today(),"title":title,
                    "category":category,"amount":amount,"kind":kind}
            old_category_spend = self.category_total().get(category, 0)
            if existing:
                existing.update(record)
            else:
                self.transactions.append(record)
            self._save_transactions()
            dialog.destroy()
            self.show_page(self.active_page)
            if kind == "Expense":
                self._check_budget_alert(category, old_category_spend)
        buttons=tk.Frame(frame,bg=WHITE); buttons.grid(row=5,column=0,columnspan=2,sticky="e",pady=(16,0))
        self.button(buttons,"Cancel",dialog.destroy,bg="#F0F3F8",fg=TEXT).pack(side="left",padx=5)
        self.button(buttons,"Save transaction",save,bg=PURPLE,fg=WHITE).pack(side="left",padx=5)
        dialog.update_idletasks()
        dialog.geometry(f"+{self.winfo_rootx()+180}+{self.winfo_rooty()+100}")


    # ------------------------- DATABASE / PERSISTENCE -------------------------
    def _connect_db(self):
        return sqlite3.connect(self.db_path)

    def _init_database(self):
        with self._connect_db() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tx_date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    kind TEXT NOT NULL
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS shared_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL,
                    paid_by TEXT NOT NULL,
                    participants TEXT NOT NULL
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS savings_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    saved REAL NOT NULL DEFAULT 0,
                    target REAL NOT NULL
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL
                )
            """)
            count = con.execute("SELECT COUNT(*) FROM savings_goals").fetchone()[0]
            if count == 0:
                con.executemany(
                    "INSERT INTO savings_goals(name, saved, target) VALUES (?, ?, ?)",
                    [("New laptop", 18000, 45000), ("Emergency fund", 7500, 15000)]
                )

    def _load_transactions(self):
        with self._connect_db() as con:
            rows = con.execute(
                "SELECT tx_date, title, category, amount, kind FROM transactions ORDER BY tx_date, id"
            ).fetchall()
        return [
            {"date": date.fromisoformat(r[0]), "title": r[1], "category": r[2],
             "amount": float(r[3]), "kind": r[4]}
            for r in rows
        ]

    def _save_transactions(self):
        with self._connect_db() as con:
            con.execute("DELETE FROM transactions")
            con.executemany(
                "INSERT INTO transactions(tx_date, title, category, amount, kind) VALUES (?, ?, ?, ?, ?)",
                [(t["date"].isoformat(), t["title"], t["category"], t["amount"], t["kind"])
                 for t in self.transactions]
            )

    def _load_goals(self):
        with self._connect_db() as con:
            rows = con.execute("SELECT name, saved, target FROM savings_goals ORDER BY id").fetchall()
        self.goals = [{"name": r[0], "saved": float(r[1]), "target": float(r[2])} for r in rows]

    def _save_goals(self):
        with self._connect_db() as con:
            con.execute("DELETE FROM savings_goals")
            con.executemany(
                "INSERT INTO savings_goals(name, saved, target) VALUES (?, ?, ?)",
                [(g["name"], g["saved"], g["target"]) for g in self.goals]
            )

    def _month_transactions(self):
        today = date.today()
        return [t for t in self.transactions
                if t["date"].year == today.year and t["date"].month == today.month]

    def _check_budget_alert(self, category, previous_amount):
        limit = self.budgets.get(category)
        if not limit:
            return
        current = self.category_total().get(category, 0)
        previous_pct = previous_amount / limit * 100
        current_pct = current / limit * 100
        crossed = [threshold for threshold in (70, 90, 100)
                   if previous_pct < threshold <= current_pct]
        if crossed:
            threshold = max(crossed)
            if threshold >= 100:
                messagebox.showwarning("Budget exceeded",
                    f"{category} spending has reached {current_pct:.0f}% of its budget.\n"
                    f"Spent: {self.money(current)} / Budget: {self.money(limit)}")
            else:
                messagebox.showinfo("Budget alert",
                    f"You have used {current_pct:.0f}% of your {category} budget.\n"
                    f"Spent: {self.money(current)} / Budget: {self.money(limit)}")

    # ------------------------- FEATURE 1: SAFE TO SPEND -------------------------
    def _safe_to_spend_page(self):
        month_items = self._month_transactions()
        income = sum(t["amount"] for t in month_items if t["kind"] == "Income")
        spent = sum(t["amount"] for t in month_items if t["kind"] == "Expense")
        category_spend = defaultdict(float)
        for t in month_items:
            if t["kind"] == "Expense":
                category_spend[t["category"]] += t["amount"]
        budget_left = sum(self.budgets.values()) - sum(category_spend.values())
        cash_left = income - spent
        days_left = calendar.monthrange(date.today().year, date.today().month)[1] - date.today().day + 1
        safe_pool = max(0, min(cash_left, budget_left))
        daily = safe_pool / max(days_left, 1)

        hero = self.card(self.body, padx=24, pady=22)
        hero.pack(fill="x", pady=(0, 14))
        self.label(hero, "YOUR DAILY SAFE-TO-SPEND AMOUNT", 10, MUTED, True).pack(anchor="w")
        self.label(hero, self.money(daily), 34, GREEN if daily > 0 else RED, True).pack(anchor="w", pady=(8, 4))
        self.label(hero, f"Based on {days_left} day(s) remaining in {date.today():%B}. "
                         "This estimate uses recorded income, expenses and category budgets.",
                   10, MUTED, wraplength=850, justify="left").pack(anchor="w")

        cards = tk.Frame(self.body, bg=BG)
        cards.pack(fill="x")
        for i, (heading, value, note, accent) in enumerate([
            ("Income this month", self.money(income), "Recorded income", GREEN),
            ("Spent this month", self.money(spent), "Recorded expenses", RED),
            ("Cash remaining", self.money(cash_left), "Income minus expenses", PURPLE),
            ("Budget remaining", self.money(budget_left), "Across all categories", BLUE),
        ]):
            cards.grid_columnconfigure(i, weight=1)
            self.stat_card(cards, heading, value, note, accent).grid(
                row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 7 if i < 3 else 0))
        note = self.card(self.body)
        note.pack(fill="x", pady=(14, 0))
        self.label(note, "How this number works", 13, TEXT, True).pack(anchor="w")
        self.label(note,
            "Safe-to-spend = the lower of (income − expenses) and (category budgets − expenses), "
            "divided by the number of days left in the month. Add your allowance or income as an "
            "Income transaction to improve the estimate.",
            10, MUTED, wraplength=900, justify="left").pack(anchor="w", pady=(7, 0))

    # ------------------------- FEATURE 2: ROOMMATE SPLITTER -------------------------
    def _roommate_splitter_page(self):
        top = self.card(self.body)
        top.pack(fill="x", pady=(0, 13))
        self.label(top, "Split shared hostel and outing expenses", 15, TEXT, True).pack(anchor="w")
        self.label(top, "Add who paid, the total amount and the people sharing it. SpendSense calculates "
                        "each person's equal share and net balance.",
                   10, MUTED, wraplength=900, justify="left").pack(anchor="w", pady=(5, 12))
        self.button(top, "+ Add shared expense", self._add_shared_expense,
                    bg=PURPLE, fg=WHITE).pack(anchor="w")

        summary = self.card(self.body)
        summary.pack(fill="both", expand=True)
        self.label(summary, "Who owes whom?  •  Net balances", 14, TEXT, True).pack(anchor="w", pady=(0, 10))
        balances = self._shared_balances()
        if not balances:
            self.label(summary, "No shared expenses yet. Add your first shared bill to get started.",
                       10, MUTED).pack(anchor="w")
        else:
            for person, balance in sorted(balances.items(), key=lambda x: x[0].lower()):
                row = tk.Frame(summary, bg=WHITE)
                row.pack(fill="x", pady=5)
                self.label(row, person, 11, TEXT, True).pack(side="left")
                if balance > 0.009:
                    label = f"gets back {self.money(balance)}"
                    colour = GREEN
                elif balance < -0.009:
                    label = f"owes {self.money(abs(balance))}"
                    colour = RED
                else:
                    label, colour = "settled", MUTED
                self.label(row, label, 10, colour, True).pack(side="right")
        tk.Frame(summary, bg=BORDER, height=1).pack(fill="x", pady=12)
        self.label(summary, "Recent shared expenses", 12, TEXT, True).pack(anchor="w", pady=(0, 7))
        with self._connect_db() as con:
            rows = con.execute(
                "SELECT expense_date, title, amount, paid_by, participants FROM shared_expenses ORDER BY id DESC"
            ).fetchall()
        if not rows:
            self.label(summary, "No shared bills recorded.", 10, MUTED).pack(anchor="w")
        for tx_date, title, amount, paid_by, participants in rows[:10]:
            self.label(summary,
                f"{tx_date}  •  {title}  •  {self.money(amount)}  •  paid by {paid_by}  •  split: {participants}",
                9, MUTED, wraplength=900, justify="left").pack(anchor="w", pady=3)

    def _shared_balances(self):
        balances = defaultdict(float)
        with self._connect_db() as con:
            rows = con.execute("SELECT amount, paid_by, participants FROM shared_expenses").fetchall()
        for amount, paid_by, participants_text in rows:
            people = [p.strip() for p in participants_text.split(",") if p.strip()]
            people = list(dict.fromkeys(people))
            if not people:
                continue
            share = float(amount) / len(people)
            for person in people:
                balances[person] -= share
            balances[paid_by] += float(amount)
        return dict(balances)

    def _add_shared_expense(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add shared expense")
        dialog.configure(bg=WHITE)
        dialog.transient(self)
        dialog.grab_set()
        frame = tk.Frame(dialog, bg=WHITE, padx=22, pady=20)
        frame.pack()
        self.label(frame, "New shared expense", 16, TEXT, True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        fields = {}
        specs = [
            ("Description", "e.g. Groceries"),
            ("Amount (₹)", "e.g. 1200"),
            ("Paid by", "Your name"),
            ("Participants", "Names separated by commas"),
        ]
        for i, (name, hint) in enumerate(specs, start=1):
            self.label(frame, name, 10, MUTED).grid(row=i, column=0, sticky="w", padx=(0, 14), pady=7)
            entry = tk.Entry(frame, width=32, bg="#F6F8FB", fg=TEXT, relief="flat",
                             font=("Segoe UI", 10))
            entry.insert(0, hint)
            entry.grid(row=i, column=1, ipady=7, pady=7)
            entry.bind("<FocusIn>", lambda e, w=entry, h=hint: w.delete(0, "end") if w.get() == h else None)
            fields[name] = entry

        def save():
            title = fields["Description"].get().strip()
            payer = fields["Paid by"].get().strip()
            people = [p.strip() for p in fields["Participants"].get().split(",") if p.strip()]
            try:
                amount = float(fields["Amount (₹)"].get())
                if amount <= 0 or not title or not payer or not people:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Check details", "Enter a description, positive amount, payer and participants.", parent=dialog)
                return
            if payer not in people:
                people.append(payer)
            people = list(dict.fromkeys(people))
            with self._connect_db() as con:
                con.execute(
                    "INSERT INTO shared_expenses(expense_date, title, amount, paid_by, participants) VALUES (?, ?, ?, ?, ?)",
                    (date.today().isoformat(), title, amount, payer, ", ".join(people))
                )
            dialog.destroy()
            self.show_page("Roommate Splitter")

        self.button(frame, "Save shared expense", save, bg=PURPLE, fg=WHITE).grid(
            row=5, column=0, columnspan=2, sticky="e", pady=(14, 0))

    # ------------------------- FEATURE 3: BUDGET ALERTS -------------------------
    # Budget alerts are triggered after a new expense crosses 70%, 90% or 100%.
    # The Budget Planner also labels categories as On track / Almost at limit / Over budget.

    # ------------------------- FEATURE 4: SPENDING BEHAVIOUR INSIGHTS -------------------------
    def _spending_insights_page(self):
        today = date.today()
        start_this_week = today - timedelta(days=today.weekday())
        start_last_week = start_this_week - timedelta(days=7)
        this_week = sum(t["amount"] for t in self.transactions
                        if t["kind"] == "Expense" and start_this_week <= t["date"] <= today)
        last_week = sum(t["amount"] for t in self.transactions
                        if t["kind"] == "Expense" and start_last_week <= t["date"] < start_this_week)
        totals = self.category_total()
        total_spent = sum(totals.values())
        top_category = max(totals, key=totals.get) if totals else "Not enough data"
        top_amount = totals.get(top_category, 0)
        difference = this_week - last_week
        if last_week > 0:
            change = (difference / last_week) * 100
            trend = f"{abs(change):.1f}% {'higher' if change > 0 else 'lower'} than last week"
            trend_colour = RED if change > 0 else GREEN
        else:
            trend, trend_colour = "No previous-week baseline yet", MUTED

        stats = tk.Frame(self.body, bg=BG)
        stats.pack(fill="x")
        for i, item in enumerate([
            ("This week", self.money(this_week), "Expenses since Monday", BLUE),
            ("Last week", self.money(last_week), "Previous Monday–Sunday", PURPLE),
            ("Top category", top_category, self.money(top_amount) + " spent", CATEGORY_COLORS.get(top_category, MUTED)),
        ]):
            stats.grid_columnconfigure(i, weight=1)
            self.stat_card(stats, *item).grid(row=0, column=i, sticky="nsew",
                padx=(0 if i == 0 else 8, 8 if i < 2 else 0))

        trend_card = self.card(self.body)
        trend_card.pack(fill="x", pady=(14, 0))
        self.label(trend_card, "Weekly spending trend", 14, TEXT, True).pack(anchor="w")
        self.label(trend_card, trend, 12, trend_colour, True).pack(anchor="w", pady=(8, 0))

        tips = self.card(self.body)
        tips.pack(fill="both", expand=True, pady=(14, 0))
        self.label(tips, "Your spending observations", 14, TEXT, True).pack(anchor="w", pady=(0, 8))
        observations = []
        if totals:
            observations.append(f"• Your highest expense category is {top_category} at {self.money(top_amount)} "
                                f"({top_amount / total_spent * 100:.1f}% of recorded expenses).")
            over = [cat for cat, amount in totals.items() if amount > self.budgets.get(cat, float("inf"))]
            if over:
                observations.append("• Budget exceeded in: " + ", ".join(over) + ". Review these categories.")
            else:
                observations.append("• No category is currently above its set monthly budget.")
            high = [cat for cat, amount in totals.items()
                    if amount >= 0.9 * self.budgets.get(cat, float("inf"))]
            if high:
                observations.append("• Close to budget limit: " + ", ".join(high) + ".")
        else:
            observations.append("• Add expenses to generate spending observations.")
        observations.append("• Compare this week with last week to notice changes in your habits.")
        observations.append("• These are simple summaries of recorded entries, not automated financial advice.")
        for line in observations:
            self.label(tips, line, 10, TEXT, wraplength=900, justify="left").pack(anchor="w", pady=5)

    # ------------------------- FEATURE 5: SAVINGS CHALLENGES -------------------------
    def _add_savings_challenge(self):
        dialog = tk.Toplevel(self)
        dialog.title("Create savings challenge")
        dialog.configure(bg=WHITE)
        dialog.transient(self)
        dialog.grab_set()
        frame = tk.Frame(dialog, bg=WHITE, padx=22, pady=20)
        frame.pack()
        self.label(frame, "Create a savings challenge", 16, TEXT, True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self.label(frame, "Goal name", 10, MUTED).grid(row=1, column=0, sticky="w", pady=7, padx=(0, 14))
        name = tk.Entry(frame, width=28, bg="#F6F8FB", fg=TEXT, relief="flat")
        name.grid(row=1, column=1, ipady=7, pady=7)
        self.label(frame, "Target amount (₹)", 10, MUTED).grid(row=2, column=0, sticky="w", pady=7, padx=(0, 14))
        target = tk.Entry(frame, width=28, bg="#F6F8FB", fg=TEXT, relief="flat")
        target.grid(row=2, column=1, ipady=7, pady=7)

        def save():
            try:
                amount = float(target.get())
                if amount <= 0 or not name.get().strip():
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Invalid goal", "Enter a goal name and positive target amount.", parent=dialog)
                return
            self.goals.append({"name": name.get().strip(), "saved": 0.0, "target": amount})
            self._save_goals()
            dialog.destroy()
            self.show_page("Savings Challenges")

        self.button(frame, "Create challenge", save, bg=PURPLE, fg=WHITE).grid(
            row=3, column=0, columnspan=2, sticky="e", pady=(14, 0))

    def _add_savings_contribution(self, goal):
        amount = simpledialog.askfloat("Add savings", f"How much did you save towards {goal['name']}?",
                                          minvalue=0.01, parent=self)
        if amount is None:
            return
        goal["saved"] += amount
        self._save_goals()
        self.show_page("Savings Challenges")
        if goal["saved"] >= goal["target"]:
            messagebox.showinfo("Challenge completed!", f"You reached your {goal['name']} savings target!")

    def edit_selected(self):
        selected=self.tx_tree.selection()
        if not selected:
            messagebox.showinfo("Select a transaction","Choose a transaction row first.",parent=self); return
        values=self.tx_tree.item(selected[0],"values")
        record=next((t for t in self.transactions if t["title"]==values[1] and t["date"].strftime("%d %b")==values[0]),None)
        if record: self.open_transaction_dialog(record)

    def delete_selected(self):
        selected=self.tx_tree.selection()
        if not selected:
            messagebox.showinfo("Select a transaction","Choose a transaction row first.",parent=self); return
        values=self.tx_tree.item(selected[0],"values")
        record=next((t for t in self.transactions if t["title"]==values[1] and t["date"].strftime("%d %b")==values[0]),None)
        if record and messagebox.askyesno("Delete transaction",f"Delete '{record['title']}'?",parent=self):
            self.transactions.remove(record)
            self._save_transactions()
            self.show_page("Transactions")


if __name__ == "__main__":
    app = SpendSenseApp()
    app.mainloop()
