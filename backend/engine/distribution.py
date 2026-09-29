import numpy as np
import uuid
import random
import string
from typing import Any, Dict, List, Optional


FIRST_NAMES = [
    "Emily", "Liam", "Olivia", "Noah", "Sophia", "James", "Ava", "William",
    "Isabella", "Oliver", "Mia", "Elijah", "Charlotte", "Mason", "Amelia",
    "Lucas", "Harper", "Logan", "Evelyn", "Aiden", "Maria", "Ahmed", "Sofia",
    "Yuki", "Chen", "Fatima", "Carlos", "Aisha", "Diego", "Priya"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young"
]

COMPANIES = [
    "Apex Global Systems", "Nexus Dynamics", "OmniCorp International",
    "Horizon Health", "Stellar Innovations", "Quantum Ventures", "PrimeTech",
    "BlueSky Analytics", "CloudWave Solutions", "DataPlex Inc", "IronShield Security",
    "GreenLeaf Biotech", "FutureMind AI", "Velocity Commerce", "Pinnacle Group"
]

PRODUCTS = [
    "Wireless Headphones", "Mechanical Keyboard", "4K Monitor", "Ergonomic Desk Chair",
    "USB-C Hub", "Gaming Mouse", "Webcam HD", "Standing Desk", "LED Desk Lamp",
    "Noise Cancelling Earbuds", "Laptop Stand", "Smart Speaker", "External SSD",
    "Graphics Tablet", "Ring Light", "Microphone", "Blue-Ray Drive", "Smart Watch"
]

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com", "icloud.com"]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "London", "Paris", "Berlin",
    "Tokyo", "Sydney", "Toronto", "Dubai", "Singapore", "Mumbai", "Seoul"
]

STREET_NAMES = [
    "Main St", "Oak Ave", "Maple Dr", "Cedar Blvd", "Pine Rd", "Elm St",
    "Washington Blvd", "Park Ave", "Lake Dr", "River Rd", "Sunset Blvd", "Highland Ave"
]

STATUSES = ["active", "inactive", "pending", "suspended", "archived"]
ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled", "refunded"]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "crypto", "cash"]


def _make_name(rng: np.random.Generator) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def _make_email(name: str, rng: np.random.Generator) -> str:
    parts = name.lower().split()
    sep = rng.choice([".", "_", ""])
    num = rng.integers(1, 999) if rng.random() < 0.4 else ""
    domain = rng.choice(EMAIL_DOMAINS)
    return f"{parts[0]}{sep}{parts[-1]}{num}@{domain}"


def _make_address(rng: np.random.Generator) -> str:
    num = rng.integers(1, 9999)
    street = rng.choice(STREET_NAMES)
    city = rng.choice(CITIES)
    return f"{num} {street}, {city}"


def _make_phone(rng: np.random.Generator) -> str:
    area = rng.integers(200, 999)
    mid = rng.integers(100, 999)
    end = rng.integers(1000, 9999)
    return f"+1-{area}-{mid}-{end}"


def sample_distribution(dist: Dict[str, Any], n_rows: int, rng: np.random.Generator, pool: Optional[list] = None) -> np.ndarray:
    """Core sampling engine — maps a distribution spec to an array of n_rows values."""
    if pool is not None and len(pool) > 0:
        return rng.choice(pool, size=n_rows, replace=True)

    dtype = dist.get("type", "string").lower()

    if dtype == "integer":
        lo = int(dist.get("min", 0))
        hi = int(dist.get("max", 100))
        if dist.get("mean") is not None:
            mean = float(dist["mean"])
            std = float(dist.get("std", (hi - lo) / 6 or 1))
            vals = rng.normal(mean, std, n_rows).astype(int)
            return np.clip(vals, lo, hi)
        return rng.integers(lo, hi + 1, size=n_rows)

    elif dtype == "float":
        lo = float(dist.get("min", 0.0))
        hi = float(dist.get("max", 100.0))
        if dist.get("mean") is not None:
            mean = float(dist["mean"])
            std = float(dist.get("std", (hi - lo) / 6 or 1.0))
            vals = rng.normal(mean, std, n_rows)
            return np.round(np.clip(vals, lo, hi), 2)
        return np.round(rng.uniform(lo, hi, n_rows), 2)

    elif dtype == "categorical":
        cats = dist.get("categories", ["A", "B", "C"])
        probs = dist.get("probabilities", None)
        if probs is not None:
            # Normalise to ensure sum==1
            p = np.array(probs, dtype=float)
            p = p / p.sum()
        else:
            p = None
        return rng.choice(cats, size=n_rows, p=p, replace=True)

    elif dtype == "boolean":
        prob_true = float(dist.get("prob_true", 0.5))
        return rng.random(n_rows) < prob_true

    elif dtype == "datetime":
        start = np.datetime64(dist.get("start", "2020-01-01"))
        end = np.datetime64(dist.get("end", "2025-12-31"))
        delta = int((end - start) / np.timedelta64(1, "D"))
        if delta <= 0:
            delta = 1
        offsets = rng.integers(0, delta, size=n_rows).astype("timedelta64[D]")
        return start + offsets

    elif dtype == "uuid":
        return np.array([str(uuid.uuid4()) for _ in range(n_rows)])

    elif dtype == "name":
        return np.array([_make_name(rng) for _ in range(n_rows)])

    elif dtype == "email":
        names = [_make_name(rng) for _ in range(n_rows)]
        return np.array([_make_email(n, rng) for n in names])

    elif dtype == "address":
        return np.array([_make_address(rng) for _ in range(n_rows)])

    elif dtype == "phone":
        return np.array([_make_phone(rng) for _ in range(n_rows)])

    elif dtype == "company":
        return rng.choice(COMPANIES, size=n_rows, replace=True)

    elif dtype == "product":
        return rng.choice(PRODUCTS, size=n_rows, replace=True)

    elif dtype == "status":
        return rng.choice(STATUSES, size=n_rows, replace=True)

    else:
        # Generic sequential IDs for unknown types
        return np.array([f"{dtype.title()}_{i+1:04d}" for i in range(n_rows)])
