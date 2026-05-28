import numpy as np

def compute_data_bbox(x, y):
    if len(x) == 0:
        return 0, 0, 0, 0
    return float(np.min(x)), float(np.max(x)), float(np.min(y)), float(np.max(y))

def score_corners(x, y, zone_fraction=0.20, padding_fraction=0.0, padding_x_units=None, padding_y_units=None):
    x_min, x_max, y_min, y_max = compute_data_bbox(x, y)
    width = x_max - x_min
    height = y_max - y_min
    
    # Avoid division by zero or tiny zones if data is point-like
    if width == 0: width = 1.0
    if height == 0: height = 1.0
    
    zone_w = width * zone_fraction
    zone_h = height * zone_fraction
    
    if padding_x_units is not None:
        padding_x = padding_x_units
    else:
        padding_x = width * padding_fraction
        
    if padding_y_units is not None:
        padding_y = padding_y_units
    else:
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
        if padding_fraction > 0 or padding_x_units is not None or padding_y_units is not None:
            px0, px1, py0, py1 = padded_zones[name]
            padded_count = np.sum((x >= px0) & (x <= px1) & (y >= py0) & (y <= py1))
            if padded_count > 0:
                count += 1000000 # Large penalty
                
        scores[name] = float(count)
    
    return scores

def find_best_corner(x, y):
    return find_best_corner_with_padding(x, y, padding_fraction=0.03)

def find_best_corner_with_padding(x, y, padding_fraction=0.03, padding_x_units=None, padding_y_units=None):
    scores = score_corners(
        x, y, 
        padding_fraction=padding_fraction, 
        padding_x_units=padding_x_units, 
        padding_y_units=padding_y_units
    )
    
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
    inset_fraction=0.02, vertical_gap=2.0,
    ref_scale=None
):
    """
    Compute coordinates for both North arrow and scale rule.
    Arrow is stacked vertically ABOVE the rule and centered on its width.
    """
    width = x_max - x_min
    height = y_max - y_min
    inset_x = width * inset_fraction
    inset_y = height * inset_fraction
    
    # Scale dependent values
    if ref_scale is not None:
        rule_height = ref_scale * 0.01
        gap = ref_scale * 0.02
    else:
        rule_height = 2.0 # Default fallback
        gap = vertical_gap
    
    if corner == "bottom-left":
        rule_pos = (x_min + inset_x, y_min + inset_y)
    elif corner == "bottom-right":
        rule_pos = (x_max - inset_x - rule_width, y_min + inset_y)
    elif corner == "top-left":
        rule_pos = (x_min + inset_x, y_max - inset_y - rule_height - gap - arrow_height)
    elif corner == "top-right":
        rule_pos = (x_max - inset_x - rule_width, y_max - inset_y - rule_height - gap - arrow_height)
    else:
        rule_pos = (x_min + inset_x, y_min + inset_y)
        
    # Arrow is centered on rule
    arrow_x = rule_pos[0] + rule_width / 2
    # Arrow is above rule
    arrow_y = rule_pos[1] + rule_height + gap + arrow_height / 2
    
    arrow_pos = (arrow_x, arrow_y)
    
    return arrow_pos, rule_pos

def compute_dual_layout(x, y, rule_length, arrow_len, ref_scale):
    """
    High-level placement function that handles scaling, footprint calculation,
    corner selection, and fallback expansion.
    """
    x_min, x_max, y_min, y_max = compute_data_bbox(x, y)
    x_span = x_max - x_min
    y_span = y_max - y_min
    
    # 1. Compute scaled gaps and heights
    vertical_gap = ref_scale * 0.02
    rule_height = ref_scale * 0.01
    
    # 2. Compute element footprint
    # Total width is max of rule and arrow
    elem_w = max(rule_length, arrow_len)
    # Total height is arrow + gap + rule
    elem_h = arrow_len + vertical_gap + rule_height
    
    # 3. Add 3% margin of axes range as padding
    margin_x = x_span * 0.03 if x_span > 0 else ref_scale * 0.03
    margin_y = y_span * 0.03 if y_span > 0 else ref_scale * 0.03
    
    padding_x_units = elem_w + margin_x
    padding_y_units = elem_h + margin_y
    
    # 4. Find best corner
    scores = score_corners(x, y, padding_x_units=padding_x_units, padding_y_units=padding_y_units)
    
    # Check if all corners are penalized
    if all(count >= 1000000 for count in scores.values()):
        # Fallback needed
        if x_span >= y_span:
            # Wide cave: expand bottom
            extra_space = elem_h + margin_y
            new_y_min = y_min - extra_space
            # Place at bottom-left of expanded strip
            arrow_pos, rule_pos = get_dual_placement(
                "bottom-left", x_min, x_max, new_y_min, y_max,
                rule_width=rule_length, arrow_height=arrow_len,
                ref_scale=ref_scale
            )
            return arrow_pos, rule_pos, {"y_min": new_y_min}
        else:
            # Tall cave: expand left
            extra_space = elem_w + margin_x
            new_x_min = x_min - extra_space
            # Place at bottom-left of expanded strip
            arrow_pos, rule_pos = get_dual_placement(
                "bottom-left", new_x_min, x_max, y_min, y_max,
                rule_width=rule_length, arrow_height=arrow_len,
                ref_scale=ref_scale
            )
            return arrow_pos, rule_pos, {"x_min": new_x_min}
    
    # No fallback needed
    priority = ["bottom-left", "bottom-right", "top-left", "top-right"]
    best_corner = priority[0]
    min_score = scores[best_corner]
    for corner in priority[1:]:
        if scores[corner] < min_score:
            min_score = scores[corner]
            best_corner = corner
            
    arrow_pos, rule_pos = get_dual_placement(
        best_corner, x_min, x_max, y_min, y_max,
        rule_width=rule_length, arrow_height=arrow_len,
        ref_scale=ref_scale
    )
    
    return arrow_pos, rule_pos, None
