import math
from collections import Counter


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def perform_dbscan_clustering(coords: list[dict], eps_km: float = 15.0, min_samples: int = 2) -> list[dict]:
    """
    Standard DBSCAN clustering algorithm implemented in pure Python.
    
    Parameters
    ----------
    coords : list[dict]
        List of dicts with 'latitude', 'longitude', 'crime_type', 'gravity', 'district' keys.
    eps_km : float
        Radius in kilometers.
    min_samples : int
        Minimum number of samples in radius to form a core point.
        
    Returns
    -------
    list[dict]
        List of cluster summary statistics.
    """
    n = len(coords)
    if n == 0:
        return []

    labels = [-1] * n  # -1 means unvisited
    # -2 means noise

    def get_neighbors(idx):
        neighbors = []
        p1 = coords[idx]
        for i in range(n):
            p2 = coords[i]
            dist = haversine(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
            if dist <= eps_km:
                neighbors.append(i)
        return neighbors

    cluster_id = 0
    for i in range(n):
        if labels[i] != -1:
            continue

        neighbors = get_neighbors(i)
        if len(neighbors) < min_samples:
            labels[i] = -2  # Noise
        else:
            labels[i] = cluster_id
            # Seed queue
            queue = [idx for idx in neighbors if idx != i]
            
            queue_idx = 0
            while queue_idx < len(queue):
                curr = queue[queue_idx]
                if labels[curr] == -2:
                    labels[curr] = cluster_id
                elif labels[curr] == -1:
                    labels[curr] = cluster_id
                    curr_neighbors = get_neighbors(curr)
                    if len(curr_neighbors) >= min_samples:
                        for neighbor in curr_neighbors:
                            if neighbor not in queue and labels[neighbor] == -1:
                                queue.append(neighbor)
                queue_idx += 1
            cluster_id += 1

    # Group points by cluster labels
    clusters_data = {}
    for idx, label in enumerate(labels):
        if label < 0:
            continue  # Ignore noise and unvisited (if any)
        if label not in clusters_data:
            clusters_data[label] = []
        clusters_data[label].append(coords[idx])

    results = []
    for label, points in clusters_data.items():
        count = len(points)
        avg_lat = sum(p["latitude"] for p in points) / count
        avg_lng = sum(p["longitude"] for p in points) / count
        avg_gravity = sum(p["gravity"] for p in points) / count
        
        crime_types = [p["crime_type"] for p in points]
        dominant_crime = Counter(crime_types).most_common(1)[0][0]
        
        districts = [p["district"] for p in points if p.get("district")]
        dominant_district = Counter(districts).most_common(1)[0][0] if districts else "Unknown"

        results.append({
            "cluster_id": label,
            "center": {"latitude": avg_lat, "longitude": avg_lng},
            "cases": count,
            "severity": round(avg_gravity, 2),
            "dominant": dominant_crime,
            "district": dominant_district
        })

    return sorted(results, key=lambda x: x["cases"], reverse=True)


def calculate_forecast(history_counts: list[int]) -> dict:
    """
    Generate basic crime forecasts using linear regression and moving average.
    
    Parameters
    ----------
    history_counts : list[int]
        Chronological list of historical crime counts.
        
    Returns
    -------
    dict
        Dictionary containing prediction and confidence.
    """
    n = len(history_counts)
    if n == 0:
        return {"prediction": 0, "confidence": 0.5, "method": "none"}
        
    # Moving average
    ma_val = sum(history_counts[-3:]) / min(n, 3)
    
    if n < 3:
        return {
            "prediction": round(ma_val, 2),
            "confidence": 0.70,
            "method": "moving_average"
        }
        
    # Fit y = mx + c (Linear Regression)
    x = list(range(n))
    y = history_counts
    
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(val * val for val in x)
    sum_xy = sum(x[i] * y[i] for i in range(n))
    
    denom = (n * sum_xx) - (sum_x * sum_x)
    if denom == 0:
        return {
            "prediction": round(ma_val, 2),
            "confidence": 0.60,
            "method": "moving_average"
        }
        
    m = ((n * sum_xy) - (sum_x * sum_y)) / denom
    c = (sum_y - (m * sum_x)) / n
    
    # Predict next month (x_next = n)
    pred = (m * n) + c
    pred = max(0.0, pred)  # Cannot be negative
    
    # Compute R-squared for confidence
    y_mean = sum_y / n
    ss_tot = sum((val - y_mean) ** 2 for val in y)
    ss_res = sum((y[i] - (m * x[i] + c)) ** 2 for i in range(n))
    
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    
    # Bound confidence
    confidence = max(0.50, min(0.95, r_squared))
    
    return {
        "prediction": round(pred, 2),
        "confidence": round(confidence, 2),
        "method": "linear_regression"
    }


def detect_anomalies(history_counts: list[int], dates: list[str]) -> list[dict]:
    """
    Identify spikes using Z-scores over a historical window.
    
    Parameters
    ----------
    history_counts : list[int]
        Chronological counts.
    dates : list[str]
        Matching time labels (e.g. 'Jan 2026', '2026-07-14').
        
    Returns
    -------
    list[dict]
        List of identified anomalies.
    """
    n = len(history_counts)
    if n < 3:
        return []

    mean = sum(history_counts) / n
    variance = sum((x - mean) ** 2 for x in history_counts) / n
    std_dev = math.sqrt(variance)
    
    anomalies = []
    if std_dev == 0:
        return anomalies
        
    for i in range(n):
        val = history_counts[i]
        z_score = (val - mean) / std_dev
        
        # Flag if Z-score is greater than 2.0 (standard anomaly threshold)
        if z_score > 2.0:
            confidence = min(0.99, max(0.60, 1.0 - math.exp(-z_score)))
            anomalies.append({
                "time_period": dates[i],
                "count": val,
                "z_score": round(z_score, 2),
                "confidence": round(confidence, 2),
                "reason": f"Significant spike in case registration volume. Count of {val} is {z_score:.2f} standard deviations above the mean ({mean:.2f})."
            })
            
    return anomalies
