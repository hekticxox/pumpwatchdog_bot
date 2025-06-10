import numpy as np
import pandas as pd

def json_safe(val):
    if isinstance(val, (np.integer,)):
        return int(val)
    elif isinstance(val, (np.floating,)):
        return float(val)
    elif isinstance(val, (pd.Timestamp,)):
        return val.isoformat()
    elif hasattr(val, "item"):  # For np scalars
        return val.item()
    else:
        return val
