import numpy as np

def compute_data_bbox(x, y):
    if len(x) == 0:
        return 0, 0, 0, 0
    return float(np.min(x)), float(np.max(x)), float(np.min(y)), float(np.max(y))

def score_corners(x, y, zone_fraction=0.20, padding_fraction=0.0):
    x_min, x_max, y_min, y_max = compute_data_bbox(x, y)
    width = x_max - x_min
    height = y_max - y_min
    
    # Avoid division by zero or tiny zones if data is point-like
    if width == 0: width = 1.0
    if height == 0: height = 1.0
    
    zone_w = width * zone_fraction
    zone_h = height * zone_fraction
    
    padding_x = width * padding_fraction
    padding_y = height * padding_fraction
    
    zones = {
        "bottom-left": (x_min, x_min + zone_w, y_min, y_min + zone_h),
        "bottom-right": (x_max - zone_w, x_max, y_min, y_min + zone_h),
        "top-left": (x_min, x_min + zone_w, y_max - zone_h, y_max),
        "top-right": (x_max - zone_w, x_max, y_max - zone_h, y_max),
    }
    
    # Padded regions to avoid
    padded_zones = {
        "bottom-left": (x_min, x_min + padding_x, y_min, y_min + padding_y),
        "bottom-right": (x_max - padding_x, x_max, y_min, y_min + padding_y),
        "top-left": (x_min, x_min + padding_x, y_max - padding_y, y_max),
        "top-right": (x_max - padding_x, x_max, y_max - padding_y, y_max),
    }
    
    scores = {}
    for name, (x0, x1, y0, y1) in zones.items():
        # Count points in zone
        count = np.sum((x >= x0) & (x <= x1) & (y >= y0) & (y <= y1))
        
        # If padding is requested, significantly penalize if any point is within padding
        if padding_fraction > 0:
            px0, px1, py0, py1 = padded_zones[name]
            padded_count = np.sum((x >= px0) & (x <= px1) & (y >= py0) & (y <= py1))
            if padded_count > 0:
                count += 1000000 # Large penalty
                
        scores[name] = float(count)
    
    return scores

def find_best_corner(x, y):
    return find_best_corner_with_padding(x, y, padding_fraction=0.0)

def find_best_corner_with_padding(x, y, padding_fraction=0.03):
    scores = score_corners(x, y, padding_fraction=padding_fraction)
    
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
    # Use default 3% padding for fallback check
    scores = score_corners(x, y, padding_fraction=0.03)
    counts = list(scores.values())
    max_count = np.max(counts)
    if max_count == 0:
        return False
        
    # If all corners are penalized (>= 1,000,000), fallback is needed
    if all(count >= 1000000 for count in counts):
        return True
        
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

def get_dual_placement(
    corner, x_min, x_max, y_min, y_max, 
    rule_width, arrow_height, 
    inset_fraction=0.02, vertical_gap=2.0
):
    """
    Compute coordinates for both North arrow and scale rule.
    Arrow is stacked vertically ABOVE the rule and centered on its width.
    """
    width = x_max - x_min
    height = y_max - y_min
    inset_x = width * inset_fraction
    inset_y = height * inset_fraction
    
    # Rule height is small, assume ~2 units for center calculation if needed
    rule_height_est = 2.0 
    
    if corner == "bottom-left":
        rule_pos = (x_min + inset_x, y_min + inset_y)
    elif corner == "bottom-right":
        rule_pos = (x_max - inset_x - rule_width, y_min + inset_y)
    elif corner == "top-left":
        rule_pos = (x_min + inset_x, y_max - inset_y - rule_height_est - vertical_gap - arrow_height)
    elif corner == "top-right":
        rule_pos = (x_max - inset_x - rule_width, y_max - inset_y - rule_height_est - vertical_gap - arrow_height)
    else:
        rule_pos = (x_min + inset_x, y_min + inset_y)
        
    # Arrow is centered on rule
    arrow_x = rule_pos[0] + rule_width / 2
    # Arrow is above rule
    arrow_y = rule_pos[1] + rule_height_est + vertical_gap + arrow_height / 2
    
    arrow_pos = (arrow_x, arrow_y)
    
    return arrow_pos, rule_pos
