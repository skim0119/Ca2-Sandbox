import numpy as np
from typing import Union, Optional


def exponential_moving_average(
    data: Union[np.ndarray, list], alpha: float, debias: bool = True
) -> np.ndarray:
    """
    Apply exponential moving average (EMA) to a 1D array with optional debiasing.

    Parameters:
    -----------
    data : array-like
        Input data to smooth
    alpha : float
        Smoothing factor (0 < alpha <= 1). Higher values = more smoothing.
        - alpha = 0: no smoothing (returns original data)
        - alpha = 1: maximum smoothing
    debias : bool, default=True
        Whether to apply debiasing correction for the initial bias in EMA

    Returns:
    --------
    np.ndarray
        Smoothed data with same shape as input

    Notes:
    ------
    The EMA is calculated as:
        s_t = alpha * x_t + (1 - alpha) * s_{t-1}

    With debiasing correction:
        s_t_corrected = s_t / (1 - (1 - alpha)^t)

    This correction removes the bias that occurs at the beginning of the series
    when the EMA hasn't "warmed up" yet.
    """
    if alpha < 0 or alpha > 1:
        raise ValueError("Alpha must be between 0 and 1 (inclusive)")

    if alpha == 0:
        return np.array(data)

    data = np.asarray(data, dtype=float)

    if data.ndim != 1:
        raise ValueError("Input data must be 1-dimensional")

    n = len(data)
    if n == 0:
        return data

    # Initialize smoothed array
    smoothed = np.zeros_like(data)
    smoothed[0] = data[0]  # First value is unchanged

    # Apply EMA
    for i in range(1, n):
        smoothed[i] = alpha * data[i] + (1 - alpha) * smoothed[i - 1]

    # Apply debiasing correction if requested
    if debias:
        # Calculate bias correction factor for each time point
        # The bias correction is: 1 / (1 - (1 - alpha)^t)
        bias_correction = 1 - (1 - alpha) ** np.arange(1, n + 1)
        # Avoid division by zero for alpha = 1
        bias_correction = np.where(bias_correction == 0, 1, bias_correction)
        smoothed = smoothed / bias_correction

    return smoothed


def smooth_intensity_trace(
    intensity_trace: Union[np.ndarray, list], smoothing_factor: float
) -> np.ndarray:
    """
    Apply smoothing to an intensity trace.

    Parameters:
    -----------
    intensity_trace : array-like
        Intensity values over time
    smoothing_factor : float
        Smoothing factor (0 <= smoothing_factor <= 1)
        - 0: no smoothing
        - > 0: apply exponential moving average

    Returns:
    --------
    np.ndarray
        Smoothed intensity trace
    """
    if smoothing_factor <= 0:
        return np.array(intensity_trace)

    return exponential_moving_average(intensity_trace, smoothing_factor, debias=True)


def smooth_multiple_traces(traces: list, smoothing_factor: float) -> list:
    """
    Apply smoothing to multiple intensity traces.

    Parameters:
    -----------
    traces : list of array-like
        List of intensity traces to smooth
    smoothing_factor : float
        Smoothing factor (0 <= smoothing_factor <= 1)

    Returns:
    --------
    list
        List of smoothed intensity traces
    """
    if smoothing_factor <= 0:
        return [np.array(trace) for trace in traces]

    return [smooth_intensity_trace(trace, smoothing_factor) for trace in traces]
