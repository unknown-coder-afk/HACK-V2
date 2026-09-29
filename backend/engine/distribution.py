import numpy as np

def sample_distribution(dist, n_rows, rng, pool=None):
    dist_type = dist.get("type", "string")
    if pool:
        return rng.choice(pool, size=n_rows)
    
    if dist_type == "integer":
        min_val = dist.get("min", 0)
        max_val = dist.get("max", 100)
        return rng.integers(min_val, max_val + 1, size=n_rows)
    elif dist_type == "float":
        min_val = dist.get("min", 0.0)
        max_val = dist.get("max", 100.0)
        return np.round(rng.uniform(min_val, max_val, size=n_rows), 2)
    elif dist_type == "categorical":
        categories = dist.get("categories", ["A", "B", "C"])
        probs = dist.get("probabilities", None)
        return rng.choice(categories, size=n_rows, p=probs)
    elif dist_type == "boolean":
        return rng.choice([True, False], size=n_rows)
    elif dist_type == "datetime":
        start = np.datetime64(dist.get("start", "2020-01-01"))
        end = np.datetime64(dist.get("end", "2025-01-01"))
        delta = end - start
        return start + rng.integers(0, delta.astype(int), size=n_rows).astype('timedelta64[D]')
    else: # string or generic
        return np.array([f"id_{i}" for i in range(n_rows)])
