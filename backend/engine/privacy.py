import hashlib
import numpy as np

def apply_privacy(value, action: str, rng: np.random.Generator = None):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None

    action = str(action).lower()

    if action == 'mask':
        s = str(value)
        return s[:2] + '****' + s[-2:] if len(s) > 4 else '****'

    if action == 'hash':
        return 'hash:' + hashlib.sha256(str(value).encode('utf-8')).hexdigest()[:12]

    if action == 'noise':
        try:
            val = float(value)
            local_rng = rng if rng is not None else np.random.default_rng()
            scale = abs(val) * 0.01 if abs(val) > 0 else 0.01
            noised = val + float(local_rng.normal(0, scale))
            return int(round(noised)) if isinstance(value, int) else round(noised, 2)
        except (ValueError, TypeError):
            return value

    return value