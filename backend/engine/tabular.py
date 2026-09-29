import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from backend.models.schemas import GenerationConfig
from backend.engine.distribution import sample_distribution
from backend.engine.privacy import apply_privacy

def inject_nulls(df: pd.DataFrame, null_rate: float, rng: np.random.Generator, pk_cols: List[str]) -> pd.DataFrame:
    if null_rate <= 0:
        return df
    df_res = df.copy()
    n_rows = len(df_res)
    for col in df_res.columns:
        if col in pk_cols:
            continue
        mask = rng.random(n_rows) < null_rate
        df_res[col] = df_res[col].astype(object)
        df_res.loc[mask, col] = None
    return df_res

def inject_outliers(df: pd.DataFrame, outlier_rate: float, rng: np.random.Generator, distributions: Dict[str, Any], pk_cols: List[str]) -> pd.DataFrame:
    if outlier_rate <= 0:
        return df
    df_res = df.copy()
    n_rows = len(df_res)
    for col in df_res.columns:
        if col in pk_cols:
            continue
        dist = distributions.get(col, {})
        if dist.get("type") in ("integer", "float"):
            mean = float(dist.get("mean", 50.0))
            std = float(dist.get("std", 10.0)) or 5.0
            mask = rng.random(n_rows) < outlier_rate
            outlier_count = int(mask.sum())
            if outlier_count > 0:
                direction = rng.choice([-1, 1], size=outlier_count)
                sigmas = rng.uniform(3.0, 5.0, size=outlier_count)
                outliers = mean + direction * (sigmas * std)
                df_res.loc[mask, col] = np.round(outliers, 2)
    return df_res

def generate_table(schema, distributions, n_rows, seed, config, text_pools=None):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame()
    pk_cols = [col["name"] for col in schema if col.get("is_primary_key")]

    for col_info in schema:
        col_name = col_info["name"]
        dist = distributions.get(col_name, {})
        pool = text_pools.get(col_name) if text_pools else None
        df[col_name] = sample_distribution(dist, n_rows, rng, pool)

    if config.null_rate > 0:
        df = inject_nulls(df, config.null_rate, rng, pk_cols)

    if config.outlier_rate > 0:
        df = inject_outliers(df, config.outlier_rate, rng, distributions, pk_cols)

    for rule in config.privacy_rules:
        if rule.column in df.columns and rule.action.value != "none":
            df[rule.column] = df[rule.column].apply(lambda x: apply_privacy(x, rule.action.value, rng))

    return df