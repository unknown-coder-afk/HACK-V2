import numpy as np
import pandas as pd
from typing import Dict, List
from backend.models.schemas import RelationalRequest, GenerationConfig, TableConfig
from backend.engine.tabular import generate_table, df_to_serializable


def _topo_sort(tables: List[TableConfig]) -> List[TableConfig]:
    """Return tables ordered parents-before-children (simple topological sort)."""
    name_map = {t.name: t for t in tables}
    result = []
    visited = set()

    def visit(t: TableConfig):
        if t.name in visited:
            return
        visited.add(t.name)
        for col in t.schema_cols:
            if col.is_foreign_key and col.references:
                parent_table = col.references.split(".")[0]
                if parent_table in name_map:
                    visit(name_map[parent_table])
        result.append(t)

    for table in tables:
        visit(table)
    return result


def generate_relational(request: RelationalRequest) -> Dict[str, list]:
    """Generate a set of related tables honouring FK relationships."""
    config = request.config
    ordered = _topo_sort(request.tables)
    generated_dfs: Dict[str, pd.DataFrame] = {}

    for idx, table_cfg in enumerate(ordered):
        seed = config.seed + idx * 100

        # Identify FK overrides
        pk_override: Dict[str, list] = {}
        for col in table_cfg.schema_cols:
            if col.is_foreign_key and col.references:
                parts = col.references.split(".")
                parent_tbl, parent_col = parts[0], parts[1]
                if parent_tbl in generated_dfs:
                    parent_vals = generated_dfs[parent_tbl][parent_col].dropna().tolist()
                    if parent_vals:
                        pk_override[col.name] = parent_vals

        df = generate_table(
            schema=table_cfg.schema_cols,
            n_rows=table_cfg.row_count,
            seed=seed,
            config=config,
            pk_override=pk_override,
        )
        generated_dfs[table_cfg.name] = df

    # Reconcile line totals if order_items + orders exist
    if "order_items" in generated_dfs and "orders" in generated_dfs:
        oi = generated_dfs["order_items"]
        if "quantity" in oi.columns and "unit_price" in oi.columns and "order_id" in oi.columns:
            clean_qty = pd.to_numeric(oi["quantity"], errors="coerce").fillna(1)
            clean_price = pd.to_numeric(oi["unit_price"], errors="coerce").fillna(0.0)
            oi["line_total"] = np.round(clean_qty * clean_price, 2)

            orders_df = generated_dfs["orders"]
            if "id" in orders_df.columns:
                order_totals = oi.groupby("order_id")["line_total"].sum().round(2)
                generated_dfs["orders"]["total_amount"] = (
                    orders_df["id"].map(order_totals).fillna(0.0).round(2)
                )

    return {name: df_to_serializable(df) for name, df in generated_dfs.items()}