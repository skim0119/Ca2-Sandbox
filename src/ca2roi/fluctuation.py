import numpy as np
from skimage import exposure
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sklearn.cluster import DBSCAN
from scipy.ndimage import label
import json
import os


def compute_fluctuation_map(frames, mean_intensity):
    n_frames = frames.shape[0]
    bleaching_trend = np.polyval(
        np.polyfit(np.arange(n_frames), mean_intensity, 2), np.arange(n_frames)
    )
    corrected = frames - bleaching_trend[:, None, None]
    fluctuation_map = np.std(corrected, axis=0)
    return fluctuation_map


def save_fluctuation_overlay(fluctuation_map, out_path):
    plt.figure(figsize=(8, 6))
    im = plt.imshow(fluctuation_map, cmap="jet")
    plt.colorbar(im, label="Fluctuation")
    plt.title("Fluctuation map")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight", pad_inches=0.1)
    plt.close("all")

    plt.figure(figsize=(8, 6))
    plt.hist(fluctuation_map.flatten(), bins=100)
    plt.yscale("log")
    plt.title("Histogram of Fluctuation Map")
    plt.xlabel("Fluctuation")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(
        out_path.replace(".pdf", "_histogram.pdf"), bbox_inches="tight", pad_inches=0.1
    )
    plt.close("all")


def auto_select_rois_from_fluctuation(
    fluctuation_map, frames, threshold, min_distance, workspace
) -> dict:
    """
    Automatically select ROIs based on fluctuation map thresholding and clustering.

    Parameters:
    -----------
    fluctuation_map : numpy.ndarray
        2D array representing fluctuation values
    frames : numpy.ndarray
        3D array of video frames (time, height, width)
    threshold : float
        Threshold value for fluctuation map
    min_distance : int
        Minimum distance in pixels for clustering
    workspace : str
        Directory to save outputs

    Returns:
    --------
    dict
        Dictionary containing ROI information and statistics
    """
    # Create binary mask of target pixels that pass threshold
    target_mask = fluctuation_map >= threshold

    if not np.any(target_mask):
        print(f"No pixels found above threshold {threshold}")
        return {
            "rois": [],
            "stats": {"n_rois": 0, "total_pixels": 0, "coverage_percent": 0.0},
        }

    # Save thresholded image
    if workspace:
        target_img_path = os.path.join(workspace, "fluctuation_targets.png")
        target_img = (target_mask * 255).astype(np.uint8)
        cv2.imwrite(target_img_path, target_img)
        print(f"Saved target pixels image to {target_img_path}")

    # Get coordinates of target pixels
    target_coords = np.column_stack(np.where(target_mask))

    # Cluster nearby target pixels using DBSCAN
    clustering = DBSCAN(eps=min_distance, min_samples=1).fit(target_coords)
    labels = clustering.labels_

    # Get unique cluster labels (excluding noise points if any)
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels[unique_labels >= 0])

    rois = []
    total_target_pixels = 0

    # Process each cluster
    for cluster_id in unique_labels:
        if cluster_id < 0:  # Skip noise points
            continue

        # Get pixels belonging to this cluster
        cluster_mask = labels == cluster_id
        cluster_coords = target_coords[cluster_mask]

        # Calculate bounding rectangle
        min_row, min_col = cluster_coords.min(axis=0)
        max_row, max_col = cluster_coords.max(axis=0)

        # Create ROI mask for this cluster
        roi_mask = np.zeros_like(fluctuation_map, dtype=bool)
        roi_mask[cluster_coords[:, 0], cluster_coords[:, 1]] = True

        # Calculate average intensity over time for this ROI
        n_frames = frames.shape[0]
        avg_intensity = np.zeros(n_frames)
        for frame_idx in range(n_frames):
            avg_intensity[frame_idx] = frames[frame_idx][roi_mask].mean()

        # Store ROI information
        roi_info = {
            "id": cluster_id,
            "coords": [
                int(min_col),
                int(min_row),
                int(max_col + 1),
                int(max_row + 1),
            ],  # [x0, y0, x1, y1]
            "n_pixels": len(cluster_coords),
            "avg_intensity": avg_intensity.tolist(),
            "center": [
                float(cluster_coords[:, 1].mean()),
                float(cluster_coords[:, 0].mean()),
            ],  # [x, y]
            "fluctuation_strength": float(fluctuation_map[roi_mask].mean()),
        }

        rois.append(roi_info)
        total_target_pixels += len(cluster_coords)

    # Calculate statistics
    total_pixels = fluctuation_map.size
    coverage_percent = (total_target_pixels / total_pixels) * 100

    stats = {
        "n_rois": n_clusters,
        "total_pixels": total_target_pixels,
        "coverage_percent": coverage_percent,
        "threshold_used": threshold,
        "min_distance_used": min_distance,
    }

    print(f"Found {n_clusters} ROIs")
    print(f"Total target pixels: {total_target_pixels}")
    print(f"Coverage: {coverage_percent:.2f}% of image")

    result = {"rois": rois, "stats": stats}

    return result


def save_auto_rois_plot(fluctuation_map, roi_data, first_frame, output_path):
    """
    Save a plot showing the automatically detected ROIs on the fluctuation map.

    Parameters:
    -----------
    fluctuation_map : numpy.ndarray
        2D fluctuation map
    roi_data : dict
        ROI data from auto_select_rois_from_fluctuation
    first_frame : numpy.ndarray
        First frame for background
    output_path : str
        Path to save the plot
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot 1: Fluctuation map with ROI overlay
    im1 = ax1.imshow(fluctuation_map, cmap="viridis", aspect="equal")
    ax1.set_title(f"Fluctuation Map with {roi_data['stats']['n_rois']} Auto ROIs")
    plt.colorbar(im1, ax=ax1, label="Fluctuation Intensity")

    # Plot 2: First frame with ROI overlay
    ax2.imshow(first_frame, cmap="gray", aspect="equal")
    ax2.set_title("First Frame with ROI Locations")

    # Add ROI rectangles and labels to both plots
    for roi in roi_data["rois"]:
        x0, y0, x1, y1 = roi["coords"]
        width = x1 - x0
        height = y1 - y0

        # Add rectangle to fluctuation map
        rect1 = patches.Rectangle(
            (x0, y0), width, height, linewidth=2, edgecolor="red", facecolor="none"
        )
        ax1.add_patch(rect1)
        ax1.text(
            x0,
            y0 - 2,
            f"ROI{roi['id'] + 1}",
            color="red",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8),
        )

        # Add rectangle to first frame
        rect2 = patches.Rectangle(
            (x0, y0), width, height, linewidth=2, edgecolor="yellow", facecolor="none"
        )
        ax2.add_patch(rect2)
        ax2.text(
            x0,
            y0 - 2,
            f"ROI{roi['id'] + 1}",
            color="yellow",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.1", facecolor="black", alpha=0.8),
        )

    ax1.set_xlabel("X (pixels)")
    ax1.set_ylabel("Y (pixels)")
    ax2.set_xlabel("X (pixels)")
    ax2.set_ylabel("Y (pixels)")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved ROI plot to {output_path}")


def plot_roi_intensity_traces(roi_data, fps, normalizer, output_path):
    """
    Plot average intensity traces for each ROI, overlaid in a single figure.

    Parameters:
    -----------
    roi_data : dict
        ROI data from auto_select_rois_from_fluctuation
    fps : float
        Frames per second for time axis
    normalizer : function
        Function to normalize intensity traces
    output_path : str
        Path to save the plot
    """
    if not roi_data["rois"]:
        print("No ROIs to plot")
        return

    n_rois = len(roi_data["rois"])
    n_frames = len(roi_data["rois"][0]["avg_intensity"])
    time_points = np.arange(n_frames) / fps

    plt.figure(figsize=(12, 6))
    for roi in roi_data["rois"]:
        avg_intensity = np.array(roi["avg_intensity"])
        plt.plot(
            time_points,
            avg_intensity,
            label=f"ROI {roi['id'] + 1} ({roi['n_pixels']} px, Fluct: {roi['fluctuation_strength']:.2f})",
            linewidth=1.5,
        )

    plt.xlabel("Time (seconds)")
    plt.ylabel("Average Intensity")
    plt.title(f"Intensity Traces for {n_rois} Auto-detected ROIs")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=9, loc="best", framealpha=0.8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved ROI intensity traces plot to {output_path}")


def filter_rois_by_size(roi_data, min_percentile=10, max_percentile=90):
    """
    Filter ROIs by size using percentile thresholds.

    Parameters:
    -----------
    roi_data : dict
        ROI data from auto_select_rois_from_fluctuation
    min_percentile : float
        Minimum percentile threshold for ROI size (default: 10)
    max_percentile : float
        Maximum percentile threshold for ROI size (default: 90)

    Returns:
    --------
    dict
        Filtered ROI data with updated statistics
    """
    # Extract ROI sizes
    roi_sizes = [roi["n_pixels"] for roi in roi_data["rois"]]
    print(roi_sizes)

    if len(roi_sizes) < 2:
        print("Not enough ROIs to perform percentile filtering")
        return roi_data

    # Calculate percentile thresholds
    min_size = np.percentile(roi_sizes, min_percentile)
    max_size = np.percentile(roi_sizes, max_percentile)

    print(
        f"Size filtering: {min_percentile}th percentile = {min_size:.1f} pixels, "
        f"{max_percentile}th percentile = {max_size:.1f} pixels"
    )

    # Filter ROIs
    filtered_rois = []
    total_filtered_pixels = 0

    for roi in roi_data["rois"]:
        if min_size <= roi["n_pixels"] <= max_size:
            filtered_rois.append(roi)
            total_filtered_pixels += roi["n_pixels"]

    # Update statistics
    original_count = len(roi_data["rois"])
    filtered_count = len(filtered_rois)

    # Calculate coverage based on original image size if available
    if "stats" in roi_data and "coverage_percent" in roi_data["stats"]:
        original_total_pixels = roi_data["stats"]["total_pixels"]
        # Estimate total image pixels from coverage percentage
        if roi_data["stats"]["coverage_percent"] > 0:
            total_image_pixels = original_total_pixels / (
                roi_data["stats"]["coverage_percent"] / 100
            )
            filtered_coverage_percent = (
                total_filtered_pixels / total_image_pixels
            ) * 100
        else:
            filtered_coverage_percent = 0.0
    else:
        filtered_coverage_percent = 0.0

    filtered_stats = {
        "n_rois": filtered_count,
        "total_pixels": total_filtered_pixels,
        "coverage_percent": filtered_coverage_percent,
        "threshold_used": (
            roi_data["stats"]["threshold_used"] if "stats" in roi_data else None
        ),
        "min_distance_used": (
            roi_data["stats"]["min_distance_used"] if "stats" in roi_data else None
        ),
        "size_filter_applied": True,
        "size_filter_range": [min_size, max_size],
        "original_roi_count": original_count,
        "filtered_roi_count": filtered_count,
    }

    print(
        f"Size filtering: {original_count} → {filtered_count} ROIs "
        f"(removed {original_count - filtered_count} ROIs)"
    )

    return {"rois": filtered_rois, "stats": filtered_stats}
