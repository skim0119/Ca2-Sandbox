import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import os


def cluster_rois_by_similarity(
    roi_data, normalizer, fps, n_frames, n_clusters=3, workspace="results"
):
    """
    Cluster ROIs by similarity using the normalized intensity traces.

    Parameters:
    -----------
    roi_data : dict
        ROI data containing 'rois' list
    normalizer : function
        Function to normalize intensity traces
    fps : float
        Frames per second
    n_frames : int
        Number of frames
    n_clusters : int
        Number of clusters for k-means (default: 3)
    workspace : str
        Directory to save plots (default: "results")

    Returns:
    --------
    dict
        Updated roi_data with cluster assignments
    """
    if not roi_data["rois"]:
        print("No ROIs to cluster")
        return roi_data

    # Generate time points
    time_points = np.arange(n_frames) / fps

    # Collect all normalized intensity traces
    normalized_traces = []
    for roi in roi_data["rois"]:
        norm_avg_intensity = normalizer(time_points, np.array(roi["avg_intensity"]))
        normalized_traces.append(norm_avg_intensity)
        roi["norm_avg_intensity"] = norm_avg_intensity.tolist()

    # Convert to numpy array for clustering
    normalized_traces = np.array(normalized_traces)

    # Apply k-means clustering
    # Standardize the data for better clustering
    scaler = StandardScaler()
    normalized_traces_scaled = scaler.fit_transform(normalized_traces)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(normalized_traces_scaled)

    # Add cluster labels to ROI data
    for i, roi in enumerate(roi_data["rois"]):
        roi["cluster"] = int(cluster_labels[i])

    # Plot cluster results
    _plot_cluster_traces(
        normalized_traces, cluster_labels, time_points, n_clusters, workspace
    )

    # Plot t-SNE visualization
    _plot_tsne_clusters(normalized_traces_scaled, cluster_labels, n_clusters, workspace)

    # Add clustering info to roi_data
    roi_data["clustering"] = {
        "n_clusters": n_clusters,
        "cluster_centers": kmeans.cluster_centers_.tolist(),
        "cluster_labels": cluster_labels.tolist(),
    }

    # Print cluster summary
    _print_cluster_summary(cluster_labels, n_clusters)

    print(f"Clustered {len(roi_data['rois'])} ROIs into {n_clusters} clusters")

    return roi_data


def plot_clustered_rois(roi_data, workspace, n_clusters):
    """
    Create comprehensive cluster visualization plots and save them in clustering directory.

    Parameters:
    -----------
    roi_data : dict
        ROI data with cluster assignments
    workspace : str
        Base workspace directory
    n_clusters : int
        Number of clusters
    """
    if not roi_data.get("rois") or not roi_data.get("clustering"):
        print("No clustered ROI data available for plotting")
        return

    # Create clustering subdirectory
    clustering_dir = os.path.join(workspace, "clustering")
    os.makedirs(clustering_dir, exist_ok=True)

    # Extract data
    cluster_labels = np.array(roi_data["clustering"]["cluster_labels"])
    rois = roi_data["rois"]

    # Get first frame if available for spatial visualization
    first_frame = None
    if "first_frame" in roi_data:
        first_frame = roi_data["first_frame"]

    # Plot 1: ROIs colored by cluster on spatial map
    _plot_spatial_clusters(
        rois, cluster_labels, n_clusters, clustering_dir, first_frame
    )

    # Plot 2: Cluster-averaged intensity traces with std bands
    _plot_cluster_averaged_traces(rois, cluster_labels, n_clusters, clustering_dir)

    # Plot 3: Individual cluster details
    _plot_individual_clusters(rois, cluster_labels, n_clusters, clustering_dir)

    print(f"Cluster visualization plots saved to {clustering_dir}/")


def _print_cluster_summary(cluster_labels, n_clusters):
    """
    Print summary information about the clustering results.
    """
    print("\nCluster Summary:")
    print("-" * 40)
    for cluster_id in range(n_clusters):
        cluster_count = np.sum(cluster_labels == cluster_id)
        percentage = (cluster_count / len(cluster_labels)) * 100
        print(f"Cluster {cluster_id + 1}: {cluster_count} ROIs ({percentage:.1f}%)")
    print("-" * 40)


def _plot_cluster_traces(
    normalized_traces, cluster_labels, time_points, n_clusters, workspace
):
    """
    Plot normalized intensity traces grouped by clusters with mean and variation.
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()

    # Colors for different clusters
    colors = plt.cm.Set1(np.linspace(0, 1, n_clusters))

    # Plot 1: All traces colored by cluster
    ax = axes[0]
    for cluster_id in range(n_clusters):
        cluster_mask = cluster_labels == cluster_id
        cluster_traces = normalized_traces[cluster_mask]

        for trace in cluster_traces:
            ax.plot(
                time_points, trace, color=colors[cluster_id], alpha=0.3, linewidth=0.8
            )

    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Normalized Intensity")
    ax.set_title("All ROI Traces Colored by Cluster")
    ax.grid(True, alpha=0.3)

    # Plot 2: Cluster means with standard deviation
    ax = axes[1]
    for cluster_id in range(n_clusters):
        cluster_mask = cluster_labels == cluster_id
        cluster_traces = normalized_traces[cluster_mask]

        if len(cluster_traces) > 0:
            mean_trace = np.mean(cluster_traces, axis=0)
            std_trace = np.std(cluster_traces, axis=0)

            ax.plot(
                time_points,
                mean_trace,
                color=colors[cluster_id],
                linewidth=2,
                label=f"Cluster {cluster_id + 1} (n={len(cluster_traces)})",
            )
            ax.fill_between(
                time_points,
                mean_trace - std_trace,
                mean_trace + std_trace,
                color=colors[cluster_id],
                alpha=0.2,
            )

    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Normalized Intensity")
    ax.set_title("Cluster Means ± Standard Deviation")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 3: Individual cluster subplots
    for cluster_id in range(min(2, n_clusters)):  # Show first 2 clusters in detail
        ax = axes[2 + cluster_id]
        cluster_mask = cluster_labels == cluster_id
        cluster_traces = normalized_traces[cluster_mask]

        if len(cluster_traces) > 0:
            # Plot individual traces
            for trace in cluster_traces:
                ax.plot(
                    time_points, trace, color=colors[cluster_id], alpha=0.5, linewidth=1
                )

            # Plot mean
            mean_trace = np.mean(cluster_traces, axis=0)
            ax.plot(time_points, mean_trace, color="black", linewidth=2, label="Mean")

            ax.set_xlabel("Time (seconds)")
            ax.set_ylabel("Normalized Intensity")
            ax.set_title(f"Cluster {cluster_id + 1} Detail (n={len(cluster_traces)})")
            ax.legend()
            ax.grid(True, alpha=0.3)

    # Hide unused subplots
    for i in range(2 + min(2, n_clusters), 4):
        axes[i].set_visible(False)

    plt.tight_layout()

    # Save plot
    output_path = os.path.join(workspace, "cluster_analysis.pdf")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved cluster analysis plot to {output_path}")


def _plot_tsne_clusters(
    normalized_traces_scaled, cluster_labels, n_clusters, workspace
):
    """
    Plot t-SNE visualization of clusters.
    """
    # Apply t-SNE
    tsne = TSNE(
        n_components=2,
        random_state=42,
        perplexity=min(30, len(normalized_traces_scaled) - 1),
    )
    tsne_coords = tsne.fit_transform(normalized_traces_scaled)

    # Create plot
    plt.figure(figsize=(10, 8))

    # Colors for different clusters
    colors = plt.cm.Set1(np.linspace(0, 1, n_clusters))

    # Plot points colored by cluster
    for cluster_id in range(n_clusters):
        cluster_mask = cluster_labels == cluster_id
        cluster_coords = tsne_coords[cluster_mask]

        if len(cluster_coords) > 0:
            plt.scatter(
                cluster_coords[:, 0],
                cluster_coords[:, 1],
                c=[colors[cluster_id]],
                s=50,
                alpha=0.7,
                label=f"Cluster {cluster_id + 1} (n={len(cluster_coords)})",
            )

    plt.xlabel("t-SNE Dimension 1")
    plt.ylabel("t-SNE Dimension 2")
    plt.title("t-SNE Visualization of ROI Clusters")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Save plot
    output_path = os.path.join(workspace, "tsne_clusters.pdf")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved t-SNE cluster plot to {output_path}")


def _plot_spatial_clusters(
    rois, cluster_labels, n_clusters, clustering_dir, first_frame=None
):
    """
    Plot ROIs colored by cluster on spatial map.
    """
    # Create a figure for spatial visualization
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Colors for clusters
    colors = plt.cm.Set1(np.linspace(0, 1, n_clusters))

    # Plot 1: ROI locations colored by cluster
    ax = axes[0]

    if first_frame is not None:
        ax.imshow(first_frame, cmap="gray", alpha=0.7)
        ax.set_title("ROI Clusters on Video Frame")
    else:
        # Create a synthetic background based on ROI positions
        max_x = max(roi["coords"][2] for roi in rois) if rois else 100
        max_y = max(roi["coords"][3] for roi in rois) if rois else 100
        ax.set_xlim(0, max_x)
        ax.set_ylim(max_y, 0)  # Flip y-axis to match image coordinates
        ax.set_title("ROI Cluster Locations")

    for i, roi in enumerate(rois):
        cluster_id = cluster_labels[i]
        x0, y0, x1, y1 = roi["coords"]

        # Draw rectangle
        from matplotlib.patches import Rectangle

        rect = Rectangle(
            (x0, y0),
            x1 - x0,
            y1 - y0,
            linewidth=2,
            edgecolor="k",
            facecolor=colors[cluster_id - 1],
            alpha=0.7,
        )
        ax.add_patch(rect)

        # Add ROI label
        ax.text(
            x0 + (x1 - x0) / 2,
            y0 + (y1 - y0) / 2,
            f"{i + 1}",
            ha="center",
            va="center",
            fontsize=8,
            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.8),
        )

    ax.set_xlabel("X (pixels)")
    ax.set_ylabel("Y (pixels)")

    # Plot 2: Cluster legend and statistics
    ax = axes[1]
    ax.axis("off")

    # Create legend
    legend_elements = []
    for cluster_id in range(n_clusters):
        cluster_count = np.sum(cluster_labels == cluster_id)
        percentage = (cluster_count / len(cluster_labels)) * 100
        legend_elements.append(
            plt.Line2D(
                [0],
                [0],
                marker="s",
                color="w",
                markerfacecolor=colors[cluster_id],
                markersize=15,
                label=f"Cluster {cluster_id + 1}: {cluster_count} ROIs ({percentage:.1f}%)",
            )
        )

    ax.legend(handles=legend_elements, loc="center", fontsize=12)
    ax.set_title("Cluster Distribution", fontsize=14, pad=20)

    plt.tight_layout()
    plt.savefig(
        os.path.join(clustering_dir, "roi_spatial_clusters.pdf"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


def _plot_cluster_averaged_traces(rois, cluster_labels, n_clusters, clustering_dir):
    """
    Plot cluster-averaged intensity traces with standard deviation bands.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Colors for clusters
    colors = plt.cm.Set1(np.linspace(0, 1, n_clusters))

    # Calculate time points (assuming uniform sampling)
    n_frames = len(rois[0]["norm_avg_intensity"]) if rois else 0
    time_points = np.arange(n_frames)  # Use frame numbers if fps not available

    # Plot 1: All individual traces colored by cluster
    for i, roi in enumerate(rois):
        cluster_id = cluster_labels[i]
        norm_intensity = np.array(roi["norm_avg_intensity"])
        ax1.plot(
            time_points,
            norm_intensity,
            color=colors[cluster_id],
            alpha=0.3,
            linewidth=0.8,
        )

    ax1.set_xlabel("Frame Number")
    ax1.set_ylabel("Normalized Intensity")
    ax1.set_title("Individual ROI Traces Colored by Cluster")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Cluster averages with standard deviation
    for cluster_id in range(n_clusters):
        cluster_mask = cluster_labels == cluster_id
        if not np.any(cluster_mask):
            continue

        # Get all traces for this cluster
        cluster_traces = []
        for i, roi in enumerate(rois):
            if cluster_mask[i]:
                cluster_traces.append(np.array(roi["norm_avg_intensity"]))

        if cluster_traces:
            cluster_traces = np.array(cluster_traces)
            mean_trace = np.mean(cluster_traces, axis=0)
            std_trace = np.std(cluster_traces, axis=0)

            # Plot mean line
            ax2.plot(
                time_points,
                mean_trace,
                color=colors[cluster_id],
                linewidth=3,
                label=f"Cluster {cluster_id + 1} (n={len(cluster_traces)})",
            )

            # Plot standard deviation band
            ax2.fill_between(
                time_points,
                mean_trace - std_trace,
                mean_trace + std_trace,
                color=colors[cluster_id],
                alpha=0.2,
            )

    ax2.set_xlabel("Frame Number")
    ax2.set_ylabel("Normalized Intensity")
    ax2.set_title("Cluster-Averaged Traces ± Standard Deviation")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(
        os.path.join(clustering_dir, "cluster_averaged_traces.pdf"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


def _plot_individual_clusters(rois, cluster_labels, n_clusters, clustering_dir):
    """
    Create detailed plots for each individual cluster.
    """
    # Calculate number of subplots needed
    n_cols = min(3, n_clusters)
    n_rows = (n_clusters + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
    if n_rows == 1 and n_cols == 1:
        axes = [axes]
    elif n_rows == 1 or n_cols == 1:
        axes = axes.flatten()
    else:
        axes = axes.flatten()

    # Colors for clusters
    colors = plt.cm.Set1(np.linspace(0, 1, n_clusters))

    time_points = np.arange(len(rois[0]["norm_avg_intensity"])) if rois else []

    for cluster_id in range(n_clusters):
        ax = axes[cluster_id] if cluster_id < len(axes) else None
        if ax is None:
            continue

        cluster_mask = cluster_labels == cluster_id
        cluster_traces = []

        # Collect traces for this cluster
        for i, roi in enumerate(rois):
            if cluster_mask[i]:
                trace = np.array(roi["norm_avg_intensity"])
                cluster_traces.append(trace)
                # Plot individual trace
                ax.plot(
                    time_points, trace, color=colors[cluster_id], alpha=0.5, linewidth=1
                )

        if cluster_traces:
            # Plot cluster mean
            cluster_traces = np.array(cluster_traces)
            mean_trace = np.mean(cluster_traces, axis=0)
            ax.plot(time_points, mean_trace, color="black", linewidth=3, label="Mean")

            ax.set_title(
                f"Cluster {cluster_id + 1} Detail\n({len(cluster_traces)} ROIs)"
            )
            ax.set_xlabel("Frame Number")
            ax.set_ylabel("Normalized Intensity")
            ax.legend()
            ax.grid(True, alpha=0.3)
        else:
            ax.text(
                0.5,
                0.5,
                "No ROIs in cluster",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=12,
            )
            ax.set_title(f"Cluster {cluster_id + 1} (Empty)")

    # Hide unused subplots
    for i in range(n_clusters, len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()
    plt.savefig(
        os.path.join(clustering_dir, "individual_cluster_details.pdf"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()
