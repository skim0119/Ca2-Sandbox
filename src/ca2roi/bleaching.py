import os

import numpy as np
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score


def exponential_decay(t, I0, tau):
    return I0 * np.exp(-t / tau)


def inverse_decay(t, I0, tau):
    return I0 / (1 + t / tau)


def create_bleaching_normalizer(tau):
    def normalizer(t, arr):
        return (arr * (1 + t / tau)) / arr[0]

    return normalizer


def compute_bleaching(frames):
    return frames.mean(axis=(1, 2))


def save_bleaching_trend_csv(mean_intensity, fps, csv_path):
    """Save bleaching trend as CSV file with time and intensity columns"""
    n_frames = len(mean_intensity)
    time_points = np.arange(n_frames) / fps  # Convert frame numbers to time in seconds

    df = pd.DataFrame({"time_seconds": time_points, "mean_intensity": mean_intensity})
    df.to_csv(csv_path, index=False)


def plot_bleaching_trend(
    csv_path=None,
    time_points=None,
    mean_intensity=None,
    output_path=None,
    title="Photobleaching Trend",
):
    """
    Plot bleaching trend over time with both exponential and inverse curve fitting

    Parameters:
    -----------
    csv_path : str, optional
        Path to CSV file with time_seconds and mean_intensity columns
    time_points : array-like, optional
        Time points in seconds (alternative to csv_path)
    mean_intensity : array-like, optional
        Mean intensity values (alternative to csv_path)
    output_path : str, optional
        Path to save the plot (if None, saves next to csv_path)
    title : str
        Title for the plot

    Returns:
    --------
    dict
        Dictionary containing:
        - 'fig': matplotlib figure object
        - 'fit_params': fitted parameters dict with 'exponential' and 'inverse' keys
        - 'r2_score': R² score dict with 'exponential' and 'inverse' keys
    """

    # Load data from CSV if provided
    if csv_path is not None:
        df = pd.read_csv(csv_path)
        time_points = df["time_seconds"].values
        mean_intensity = df["mean_intensity"].values
    elif time_points is None or mean_intensity is None:
        raise ValueError(
            "Either provide csv_path or both time_points and mean_intensity"
        )

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot original data
    ax.plot(time_points, mean_intensity, "b-", linewidth=2, alpha=0.8, label="Raw Data")
    ax.set_yscale("log")

    result = {"fig": fig, "fit_params": {}, "r2_score": {}}

    # Fit configurations
    fit_configs = [
        {
            "name": "exponential",
            "func": exponential_decay,
            "tau_guess_factor": 3,
            "label": "Exponential Fit",
            "equation_template": "Exp: I(t) = {:.1f} × exp(-t/{:.2f})",
            "color": "r",
            "linestyle": "--",
        },
        {
            "name": "inverse",
            "func": inverse_decay,
            "tau_guess_factor": 2,
            "label": "Inverse Fit",
            "equation_template": "Inv: I(t) = {:.1f} / (1 + t/{:.2f})",
            "color": "g",
            "linestyle": "-.",
        },
    ]

    equation_texts = []

    # Fit both exponential and inverse curves
    for config in fit_configs:
        try:
            # Initial parameter guesses
            I0_guess = mean_intensity[0]
            tau_guess = time_points[-1] / config["tau_guess_factor"]

            # Fit the curve
            popt, pcov = curve_fit(
                config["func"],
                time_points,
                mean_intensity,
                p0=[I0_guess, tau_guess],
                maxfev=10000,
            )

            I0_fit, tau_fit = popt

            # Generate smooth curve for plotting
            t_smooth = np.linspace(time_points[0], time_points[-1], 300)
            y_fit_smooth = config["func"](t_smooth, I0_fit, tau_fit)

            # Calculate R² score
            y_fit = config["func"](time_points, I0_fit, tau_fit)
            r2 = r2_score(mean_intensity, y_fit)

            # Plot fitted curve
            ax.plot(
                t_smooth,
                y_fit_smooth,
                color=config["color"],
                linestyle=config["linestyle"],
                linewidth=2,
                alpha=0.9,
                label=f"{config['label']} (τ={tau_fit:.2f}s, R²={r2:.3f})",
            )

            # Store fit results
            result["fit_params"][config["name"]] = [I0_fit, tau_fit]
            result["r2_score"][config["name"]] = r2

            # Add equation text
            equation_texts.append(config["equation_template"].format(I0_fit, tau_fit))

            print(f"{config['label']} parameters:")
            print(f"  Initial intensity (I₀): {I0_fit:.2f}")
            print(f"  Time constant (τ): {tau_fit:.2f} seconds")
            print(f"  R² score: {r2:.4f}")

        except Exception as e:
            print(f"Warning: Could not fit {config['name']} curve: {e}")
            result["fit_params"][config["name"]] = None
            result["r2_score"][config["name"]] = None

    # Add equations to plot
    if equation_texts:
        combined_equation = "\n".join(equation_texts)
        ax.text(
            0.05,
            0.95,
            combined_equation,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )

    # Add legend
    ax.legend()

    # Styling
    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel("Mean Intensity", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    # Save plot
    if output_path is None and csv_path is not None:
        output_path = os.path.join(os.path.dirname(csv_path), "bleaching_trend.pdf")

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {output_path}")

    plt.close("all")

    normalizer = create_bleaching_normalizer(result["fit_params"]["inverse"][1])

    return result, normalizer


def save_bleaching(mean_intensity, info, out_path):
    bleaching_info = dict(mean_intensity=mean_intensity, **info)
    with open(out_path, "wb") as f:
        pickle.dump(bleaching_info, f)
