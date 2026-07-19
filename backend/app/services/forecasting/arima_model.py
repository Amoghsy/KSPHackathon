import logging

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from statsmodels.tsa.arima.model import ARIMA
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

def forecast_arima_or_fallback(history: list[int], periods: int = 3) -> dict:
    """
    Forecasting utility that uses ARIMA(1,1,1) if statsmodels is available
    and history length is >= 8. Otherwise, falls back to a Weighted Moving Average (WMA).
    """
    if not history:
        return {
            "forecast": [],
            "method": "fallback_empty",
            "confidence": 0.0,
            "error": "No historical data provided"
        }

    # Clean history: map elements to floats/ints
    clean_history = [float(x) for x in history]

    # Try ARIMA(1,1,1) if statsmodels is installed and we have at least 8 data points
    if HAS_STATSMODELS and len(clean_history) >= 8:
        try:
            # Fit an ARIMA(1, 1, 1) model
            model = ARIMA(clean_history, order=(1, 1, 1))
            fit_model = model.fit()
            
            # Forecast next steps
            forecast_values = fit_model.forecast(steps=periods)
            forecast_list = [max(0.0, round(float(val), 2)) for val in forecast_values]
            
            # Estimate confidence based on residuals variance vs historical variance
            residuals = fit_model.resid
            mse = float(np.mean(residuals**2))
            var_hist = float(np.var(clean_history))
            r_squared = 1.0 - (mse / var_hist) if var_hist > 0 else 1.0
            
            confidence = max(0.50, min(0.95, r_squared))
            
            return {
                "forecast": forecast_list,
                "method": "arima_1_1_1",
                "confidence": round(confidence, 2)
            }
        except Exception as exc:
            logger.warning("ARIMA fit failed (non-fatal), falling back to WMA: %s", exc)

    # Fallback: Weighted Moving Average (WMA)
    forecast_list = []
    temp_history = list(clean_history)
    
    for _ in range(periods):
        n = len(temp_history)
        if n == 0:
            pred_val = 0.0
        elif n == 1:
            pred_val = temp_history[0]
        elif n == 2:
            pred_val = sum(temp_history) / 2.0
        else:
            # WMA: 3*t + 2*(t-1) + 1*(t-2) / 6
            pred_val = (3.0 * temp_history[-1] + 2.0 * temp_history[-2] + 1.0 * temp_history[-3]) / 6.0
        
        pred_val = max(0.0, pred_val)
        forecast_list.append(round(pred_val, 2))
        temp_history.append(pred_val)

    # WMA confidence estimation
    confidence = 0.65 if len(history) >= 3 else 0.50

    return {
        "forecast": forecast_list,
        "method": "weighted_moving_average",
        "confidence": confidence
    }
