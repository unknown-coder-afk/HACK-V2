import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from backend.models.schemas import GenerationConfig, ColumnSchema
from backend.engine.distribution import sample_distribution
from backend.engine.privacy import apply_privacy


def _col_to_dist(col: ColumnSchema) -> Dict[str, Any]:
    """Convert a ColumnSchema into a distribution spec dict."""
    dist: Dict[str, Any] = {"type": col.type}
    if col.categories is not None:
        dist["categories"] = col.categories
    if col.probabilities is not None:
        dist["probabilities"] = col.probabilities
    if col.min is not None:
        dist["min"] = col.min
    if col.max is not None:
        dist["max"] = col.max
    if col.mean is not None:
        dist["mean"] = col.mean
    if col.std is not None:
        dist["std"] = col.std
    if col.start is not None:
        dist["start"] = col.start
    if col.end is not None:
        dist["end"] = col.end
    return dist


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


def inject_outliers(
    df: pd.DataFrame,
    outlier_rate: float,
    rng: np.random.Generator,
    distributions: Dict[str, Any],
    pk_cols: List[str],
) -> pd.DataFrame:
    if outlier_rate <= 0:
        return df
    df_res = df.copy()
    n_rows = len(df_res)
    for col in df_res.columns:
        if col in pk_cols:
            continue
        dist = distributions.get(col, {})
        if dist.get("type") in ("integer", "float"):
            mean = float(dist.get("mean", dist.get("min", 0) + (dist.get("max", 100) - dist.get("min", 0)) / 2))
            std = float(dist.get("std", abs(dist.get("max", 100) - dist.get("min", 0)) / 6)) or 5.0
            mask = rng.random(n_rows) < outlier_rate
            outlier_count = int(mask.sum())
            if outlier_count > 0:
                direction = rng.choice([-1, 1], size=outlier_count)
                sigmas = rng.uniform(3.0, 5.0, size=outlier_count)
                outliers = mean + direction * (sigmas * std)
                df_res.loc[mask, col] = np.round(outliers, 2)
    return df_res


def generate_table(
    schema: List[ColumnSchema],
    n_rows: int,
    seed: int,
    config: GenerationConfig,
    text_pools: Optional[Dict[str, list]] = None,
    pk_override: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Generate a single synthetic table DataFrame."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame()
    pk_cols = [col.name for col in schema if col.is_primary_key]
    distributions = {col.name: _col_to_dist(col) for col in schema}

    for col_info in schema:
        col_name = col_info.name
        dist = distributions[col_name]
        pool = (text_pools or {}).get(col_name)

        if col_info.is_primary_key and col_info.type in ("integer",):
            # Unique sequential IDs
            start = int(col_info.min or 1)
            df[col_name] = np.arange(start, start + n_rows, dtype=int)
        elif pk_override and col_name in pk_override:
            # FK column filled in from parent
            parent_vals = pk_override[col_name]
            df[col_name] = rng.choice(parent_vals, size=n_rows, replace=True)
        else:
            raw = sample_distribution(dist, n_rows, rng, pool)
            # Convert numpy datetime64 to ISO strings
            if hasattr(raw, "dtype") and np.issubdtype(getattr(raw, "dtype", object), np.datetime64):
                raw = raw.astype("datetime64[D]").astype(str)
            df[col_name] = raw

    if config.null_rate > 0:
        df = inject_nulls(df, config.null_rate, rng, pk_cols)

    if config.outlier_rate > 0:
        df = inject_outliers(df, config.outlier_rate, rng, distributions, pk_cols)

    for rule in config.privacy_rules:
        if rule.column in df.columns and rule.action.value != "none":
            df[rule.column] = df[rule.column].apply(
                lambda x: apply_privacy(x, rule.action.value, rng)
            )

    return df


def df_to_serializable(df: pd.DataFrame) -> list:
    """Convert DataFrame to a JSON-serialisable list of dicts."""
    import math
    rows = df.to_dict(orient="records")
    clean = []
    for row in rows:
        new_row = {}
        for k, v in row.items():
            if v is None:
                new_row[k] = None
            elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                new_row[k] = None
            elif hasattr(v, "item"):  # numpy scalar
                new_row[k] = v.item()
            else:
                new_row[k] = v
        clean.append(new_row)
    return clean