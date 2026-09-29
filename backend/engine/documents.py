import numpy as np
import random
import string
from typing import List, Dict, Any
from datetime import date, timedelta
from backend.engine.distribution import FIRST_NAMES, LAST_NAMES, COMPANIES, PRODUCTS, CITIES


def _rand_date(rng: np.random.Generator, start_year=2024, end_year=2025) -> str:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=int(rng.integers(0, delta)))).isoformat()


def _rand_invoice_number(rng: np.random.Generator) -> str:
    letters = "".join(rng.choice(list(string.ascii_uppercase), 2))
    digits = f"{rng.integers(10000, 99999)}"
    return f"INV-{letters}{digits}"


def generate_invoice(rng: np.random.Generator, seed_offset: int = 0) -> Dict[str, Any]:
    seller = rng.choice(COMPANIES)
    buyer_first = rng.choice(FIRST_NAMES)
    buyer_last = rng.choice(LAST_NAMES)
    buyer = f"{buyer_first} {buyer_last}"
    city = rng.choice(CITIES)

    n_items = int(rng.integers(2, 8))
    items = []
    subtotal = 0.0
    for _ in range(n_items):
        product = rng.choice(PRODUCTS)
        qty = int(rng.integers(1, 10))
        unit_price = round(float(rng.uniform(9.99, 499.99)), 2)
        line_total = round(qty * unit_price, 2)
        subtotal += line_total
        items.append({
            "description": product,
            "quantity": qty,
            "unit_price": unit_price,
            "line_total": line_total,
        })

    subtotal = round(subtotal, 2)
    tax_rate = round(float(rng.choice([0.05, 0.08, 0.10, 0.12, 0.15, 0.20])), 2)
    tax_amount = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax_amount, 2)
    issue_date = _rand_date(rng)

    return {
        "invoice_number": _rand_invoice_number(rng),
        "issue_date": issue_date,
        "due_date": (date.fromisoformat(issue_date) + timedelta(days=30)).isoformat(),
        "seller": seller,
        "buyer": buyer,
        "billing_address": f"{rng.integers(1, 9999)} Main St, {city}",
        "line_items": items,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "total": total,
        "currency": "USD",
        "status": rng.choice(["paid", "unpaid", "overdue", "draft"]),
        "payment_method": rng.choice(["credit_card", "bank_transfer", "paypal", "check"]),
    }


def generate_bank_statement(rng: np.random.Generator, seed_offset: int = 0) -> Dict[str, Any]:
    account_holder = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    account_num = f"****{rng.integers(1000, 9999)}"
    opening_balance = round(float(rng.uniform(500, 20000)), 2)

    n_txns = int(rng.integers(10, 30))
    transactions = []
    running_balance = opening_balance

    start = date(2025, 1, 1)
    for i in range(n_txns):
        txn_date = (start + timedelta(days=int(rng.integers(0, 365)))).isoformat()
        is_credit = rng.random() > 0.5
        amount = round(float(rng.uniform(5, 2500)), 2)
        if is_credit:
            running_balance += amount
            desc = rng.choice(["Salary Deposit", "Transfer In", "Refund", "Interest", "Freelance Payment"])
        else:
            running_balance -= amount
            desc = rng.choice([
                "Grocery Store", "Netflix", "Amazon", "Utility Bill", "Restaurant",
                "Gas Station", "Online Shopping", "Gym Membership", "Insurance Premium"
            ])
        running_balance = round(running_balance, 2)
        transactions.append({
            "date": txn_date,
            "description": desc,
            "type": "credit" if is_credit else "debit",
            "amount": amount,
            "balance": running_balance,
        })

    # Sort by date
    transactions.sort(key=lambda x: x["date"])

    return {
        "account_holder": account_holder,
        "account_number": account_num,
        "bank_name": rng.choice(COMPANIES),
        "statement_period": "Jan 2025 – Dec 2025",
        "opening_balance": opening_balance,
        "closing_balance": round(running_balance, 2),
        "total_credits": round(sum(t["amount"] for t in transactions if t["type"] == "credit"), 2),
        "total_debits": round(sum(t["amount"] for t in transactions if t["type"] == "debit"), 2),
        "transactions": transactions,
        "currency": "USD",
    }


def generate_receipt(rng: np.random.Generator, seed_offset: int = 0) -> Dict[str, Any]:
    store = rng.choice(COMPANIES)
    n_items = int(rng.integers(1, 6))
    items = []
    subtotal = 0.0
    for _ in range(n_items):
        product = rng.choice(PRODUCTS)
        qty = int(rng.integers(1, 4))
        price = round(float(rng.uniform(4.99, 99.99)), 2)
        items.append({"item": product, "qty": qty, "price": price, "total": round(qty * price, 2)})
        subtotal += round(qty * price, 2)

    subtotal = round(subtotal, 2)
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + tax, 2)

    return {
        "receipt_number": f"RCP-{rng.integers(100000, 999999)}",
        "store": store,
        "cashier": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
        "date": _rand_date(rng),
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "payment_method": rng.choice(["cash", "credit_card", "debit_card", "mobile_pay"]),
        "currency": "USD",
    }


def generate_documents(doc_type: str, count: int, seed: int) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed)
    generators = {
        "invoice": generate_invoice,
        "bank_statement": generate_bank_statement,
        "receipt": generate_receipt,
    }
    gen_fn = generators.get(doc_type, generate_invoice)
    return [gen_fn(rng, i) for i in range(count)]
