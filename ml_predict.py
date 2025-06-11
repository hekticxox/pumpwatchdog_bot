import numpy as np
import pickle
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

def train_ml_model(indicator_df, model_path="ml_model.pkl"):
    """
    Train an XGBoost regression model to predict future returns from indicators.
    Saves the model to the given path.
    """
    X = indicator_df.drop(columns=["future_return"])
    y = indicator_df["future_return"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
    model = XGBRegressor()
    model.fit(X_train, y_train)
    pickle.dump(model, open(model_path, "wb"))
    return model

def load_ml_model(model_path="ml_model.pkl"):
    """
    Load an XGBoost regression model from the given file path.
    Returns the model object, or None if it cannot be loaded.
    """
    try:
        return pickle.load(open(model_path, "rb"))
    except Exception:
        return None

def predict_return(model, indicator_vec):
    """
    Given a trained model and a vector of indicator values, predict the future return.
    """
    indicator_vec = np.array(indicator_vec, dtype=float).reshape(1, -1)
    return float(model.predict(indicator_vec)[0])
