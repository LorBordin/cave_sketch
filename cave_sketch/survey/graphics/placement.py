import numpy as np

def compute_data_bbox(x, y):
    if len(x) == 0:
        return 0, 0, 0, 0
    return float(np.min(x)), float(np.max(x)), float(np.min(y)), float(np.max(y))

def score_corners(x, y, zone_fraction=0.20):
    x_min, x_max, y_min, y_max = compute_data_bbox(x, y)
    width = x_max - x_min
    height = y_max - y_min
    
    # Avoid division by zero or tiny zones if data is point-like
    if width == 0: width = 1.0
    if height == 0: height = 1.0
    
    zone_w = width * zone_fraction
    zone_h = height * zone_fraction
    
    zones = {
        "bottom-left": (x_min, x_min + zone_w, y_min, y_min + zone_h),
        "bottom-right": (x_max - zone_w, x_max, y_min, y_min + zone_h),
        "top-left": (x_min, x_min + zone_w, y_max - zone_h, y_max),
        "top-right": (x_max - zone_w, x_max, y_max - zone_h, y_max),
    }
    
    scores = {}
    for name, (x0, x1, y0, y1) in zones.items():
        # Count points in zone
        count = np.sum((x >= x0) & (x <= x1) & (y >= y0) & (y <= y1))
        scores[name] = float(count)
    
    return scores

def find_best_corner(x, y):
    scores = score_corners(x, y)
    
    # Priority: bottom-left > bottom-right > top-left > top-right
    priority = ["bottom-left", "bottom-right", "top-left", "top-right"]
    
    best_corner = priority[0]
    min_count = scores[best_corner]
    
    for corner in priority[1:]:
        if scores[corner] < min_count:
            min_count = scores[corner]
            best_corner = corner
            
    return best_corner

def is_fallback_needed(x, y):
    scores = score_corners(x, y)
    counts = list(scores.values())
    max_count = np.max(counts)
    if max_count == 0:
        return False
        
    threshold = 0.5 * max_count
    return all(count > threshold for count in counts)

def corner_anchor(corner, x_min, x_max, y_min, y_max, inset_fraction=0.02):
    width = x_max - x_min
    height = y_max - y_min
    inset_x = width * inset_fraction
    inset_y = height * inset_fraction
    
    if corner == "bottom-left":
        return x_min + inset_x, y_min + inset_y
    elif corner == "bottom-right":
        return x_max - inset_x, y_min + inset_y
    elif corner == "top-left":
        return x_min + inset_x, y_max - inset_y
    elif corner == "top-right":
        return x_max - inset_x, y_max - inset_y
    return x_min + inset_x, y_min + inset_y
