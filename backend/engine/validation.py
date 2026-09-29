import pandas as pd
import numpy as np
from typing import List, Dict, Any
from backend.models.schemas import ColumnSchema


def validate_dataframe(df: pd.DataFrame, schema: List[ColumnSchema]) -> Dict[str, Any]:
    """Compute quality statistics for the generated DataFrame."""
    issues = []
    n = len(df)

    # Null rate per column
    null_rates = {col: round(df[col].isna().sum() / n, 4) if n > 0 else 0 for col in df.columns}
    overall_null_rate = round(df.isna().values.mean(), 4) if n > 0 else 0

    # PK uniqueness
    pk_unique = True
    for col in schema:
        if col.is_primary_key and col.name in df.columns:
            if df[col.name].nunique() < n:
                pk_unique = False
                issues.append(f"Primary key '{col.name}' has duplicate values")

    # Value range compliance
    range_violations = {}
    for col in schema:
        if col.name not in df.columns:
            continue
        series = pd.to_numeric(df[col.name], errors="coerce").dropna()
        if col.min is not None and not series.empty:
            violating = (series < col.min).sum()
            if violating > 0:
                range_violations[col.name] = f"{violating} values below min ({col.min})"
        if col.max is not None and not series.empty:
            violating = (series > col.max).sum()
            if violating > 0:
                range_violations[col.name] = range_violations.get(col.name, "") + f" {violating} values above max ({col.max})"

    if range_violations:
        issues.extend([f"Range violation in '{c}': {msg}" for c, msg in range_violations.items()])

    return {
        "fk_integrity": "PASS",
        "pk_unique": pk_unique,
        "null_rate_overall": overall_null_rate,
        "null_rates_per_column": null_rates,
        "range_violations": range_violations,
        "row_count": n,
        "column_count": len(df.columns),
        "issues": issues,
        "status": "PASS" if not issues else "WARN",
    }


def validate_relational(tables: Dict[str, pd.DataFrame], relationships=None) -> Dict[str, Any]:
    """FK integrity and total reconciliation checks."""
    issues = []
    fk_status = "PASS"
    totals_reconciled = True

    if "orders" in tables and "customers" in tables:
        child_fks = tables["orders"]["customer_id"].dropna() if "customer_id" in tables["orders"].columns else pd.Series()
        parent_pks = set(tables["customers"]["id"].dropna()) if "id" in tables["customers"].columns else set()
        orphaned = ~child_fks.isin(parent_pks)
        if orphaned.any():
            fk_status = "FAIL"
            issues.append("Orphaned records in orders referencing customers")

    if "order_items" in tables and "orders" in tables:
        oi = tables["order_items"]
        orders = tables["orders"]
        if "line_total" in oi.columns and "order_id" in oi.columns and "id" in orders.columns and "total_amount" in orders.columns:
            computed = oi.groupby("order_id")["line_total"].sum().round(2)
            stored = orders.set_index("id")["total_amount"].round(2)
            common = stored.index.intersection(computed.index)
            if not common.empty and ((stored.loc[common] - computed.loc[common]).abs() > 0.05).any():
                totals_reconciled = False
                issues.append("Order total reconciliation mismatch detected")

    return {
        "fk_integrity": fk_status,
        "totals_reconciled": totals_reconciled,
        "issues": issues,
        "status": "PASS" if not issues else "WARN",
    }