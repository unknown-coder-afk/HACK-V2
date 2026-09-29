import numpy as np
import pandas as pd
from backend.engine.tabular import generate_table

def generate_relational(tables_config=None, row_counts=None, seed=42, config=None):
    rng = np.random.default_rng(seed)
    generated = {}

    # STEP 1: Parents first (tables with no foreign keys)
    for t_name, t_meta in tables_config.items():
        if len(t_meta.get("foreign_keys", [])) == 0:
            generated[t_name] = generate_table(
                schema=t_meta["schema"],
                distributions=t_meta["distributions"],
                n_rows=row_counts.get(t_name, 25),
                seed=seed,
                config=config
            )

    # STEP 2: Children (sample FKs from parent IDs)
    for t_name, t_meta in tables_config.items():
        if t_name not in generated:
            df_child = generate_table(
                schema=t_meta["schema"],
                distributions=t_meta["distributions"],
                n_rows=row_counts.get(t_name, 50),
                seed=seed + 1,
                config=config
            )
            for fk in t_meta.get("foreign_keys", []):
                parent_ids = generated[fk["parent_table"]]["id"].dropna().values
                df_child[fk["column"]] = rng.choice(parent_ids, len(df_child), replace=True)
            generated[t_name] = df_child

    # STEP 3: Derived values calculation & reconciliation
    if "order_items" in generated and "orders" in generated:
        oi = generated["order_items"]
        clean_qty = pd.to_numeric(oi["quantity"], errors="coerce").fillna(1)
        clean_price = pd.to_numeric(oi["unit_price"], errors="coerce").fillna(0.0)
        oi["line_total"] = np.round(clean_qty * clean_price, 2)

        order_totals = oi.groupby("order_id")["line_total"].sum().round(2)
        generated["orders"]["total_amount"] = generated["orders"]["id"].map(order_totals).fillna(0.0).round(2)

    return generated