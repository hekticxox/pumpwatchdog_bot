import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def load_indicator_history(path="indicator_history.csv"):
    """
    Load historical indicator data (with future return labels) for pattern recognition.
    Returns a DataFrame or an empty DataFrame if the file does not exist.
    """
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def find_similar_patterns(current_vec, history_df, threshold=0.9, pump_threshold=0.1, min_support=0.7):
    """
    Look for similar indicator patterns in history.
    - current_vec: np.array of current indicators.
    - history_df: DataFrame with past indicators + 'future_return' column.
    Returns True if similar patterns resulted in pumps in > min_support fraction of cases.
    """
    if history_df.empty or "future_return" not in history_df.columns:
        return False

    past_vecs = history_df.drop(columns=["future_return"]).values
    similarities = cosine_similarity([current_vec], past_vecs)[0]
    matches = similarities >= threshold
    matched_returns = history_df["future_return"][matches]

    if len(matched_returns) > 0 and (matched_returns > pump_threshold).mean() > min_support:
        return True
    return False
