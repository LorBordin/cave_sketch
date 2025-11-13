import numpy as np
import pyvista as pv
from scipy.spatial import Delaunay

def parse_dxf_lines(file_path):
    """
    Read a DXF file and return a list of 3D segments (LINE entities only).
    Each segment is ((x1, y1, z1), (x2, y2, z2))
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    segments = []
    current = {}
    for i, line in enumerate(lines):
        line = line.strip()
        if line == "LINE":
            if all(k in current for k in ["10", "20", "30", "11", "21", "31"]):
                seg = (
                    (current["10"], current["20"], current["30"]),
                    (current["11"], current["21"], current["31"])
                )
                segments.append(seg)
            current = {}
        elif line in ["10", "20", "30", "11", "21", "31"]:
            try:
                value = float(lines[i + 1].strip())
                current[line] = value
            except:
                pass

    if all(k in current for k in ["10", "20", "30", "11", "21", "31"]):
        seg = (
            (current["10"], current["20"], current["30"]),
            (current["11"], current["21"], current["31"])
        )
        segments.append(seg)

    return segments


def segments_to_points(segments):
    """Extract unique 3D points from the list of segments."""
    pts = []
    for (x1, y1, z1), (x2, y2, z2) in segments:
        pts.append((x1, y1, z1))
        pts.append((x2, y2, z2))
    pts = np.unique(np.array(pts), axis=0)
    return pts


def compute_alpha_shape(points, alpha):
    """
    Compute a concave hull (alpha shape) of a set of 3D points projected on XY.
    Returns a set of triangles (simplices) that form the alpha shape boundary.
    """
    from shapely.geometry import MultiPoint
    from shapely.ops import triangulate

    # Project to XY for 2D alpha shape
    xy = points[:, :2]
    coords = [tuple(p) for p in xy]
    mp = MultiPoint(coords)

    # Create many triangles (Delaunay-like)
    triangles = triangulate(mp)

    # Keep only triangles whose circumradius < alpha
    def tri_circumradius(tri):
        a, b, c = np.array(tri.exterior.coords)[:3]
        ab = np.linalg.norm(a - b)
        bc = np.linalg.norm(b - c)
        ca = np.linalg.norm(c - a)
        s = (ab + bc + ca) / 2
        area = np.sqrt(max(s * (s - ab) * (s - bc) * (s - ca), 1e-12))
        return (ab * bc * ca) / (4 * area)

    valid_triangles = [tri for tri in triangles if tri_circumradius(tri) < alpha]

    # Convert back to indices of points
    simplices = []
    for tri in valid_triangles:
        coords_tri = np.array(tri.exterior.coords)[:3]
        indices = []
        for p in coords_tri:
            idx = np.where((xy == p).all(axis=1))[0]
            if len(idx) > 0:
                indices.append(idx[0])
        if len(indices) == 3:
            simplices.append(indices)

    return np.array(simplices)


def filter_far_points(points, max_dist=20):
    """
    Remove isolated points that are too far from others.
    Useful to discard distant splays.
    """
    from sklearn.neighbors import NearestNeighbors
    nbrs = NearestNeighbors(n_neighbors=3).fit(points)
    distances, _ = nbrs.kneighbors(points)
    mean_dist = distances[:, 1]  # distance to 2nd nearest neighbor
    return points[mean_dist < max_dist]


def plot_with_pyvista(points, simplices):
    """
    Plot the 3D triangulated surface using PyVista (interactive viewer).
    """
    # Properly build the faces array
    n_faces = len(simplices)
    faces = np.hstack([np.full((n_faces, 1), 3), simplices]).astype(np.int32)
    faces = faces.flatten()

    # Create the PolyData mesh
    # After creating your PyVista mesh
    mesh = pv.PolyData(points, faces)
    
    # Clean and smooth the surface
    mesh = mesh.clean()
    smooth_mesh = mesh.smooth(n_iter=50, relaxation_factor=0.1)
    
    # Compute volume
    volume = smooth_mesh.volume
    print(f"Estimated enclosed volume: {volume:.2f} m³")
    
    # Plot and save a screenshot
    plotter = pv.Plotter()
    plotter.add_mesh(smooth_mesh, color="tan", show_edges=False, smooth_shading=True)
    plotter.show(screenshot="cave_view.png")


if __name__ == "__main__":
    dxf_path = "/Users/bordil/projects/cave_survey/un_altro_buco_nell_acqua/un_altro_buco_nell_acqua.dxf"
    segments = parse_dxf_lines(dxf_path)
    print(f"Read {len(segments)} 3D segments")

    points = segments_to_points(segments)
    print(f"Extracted {len(points)} unique points")

    # 1️⃣ Filter far points
    #points = filter_far_points(points, max_dist=100)
    print(f"Remaining {len(points)} after distance filtering")

    # 2️⃣ Compute alpha shape (concave hull)
    simplices = compute_alpha_shape(points, alpha=20.0)
    print(f"Generated {len(simplices)} triangles in alpha shape")

    # 3️⃣ Plot interactive mesh
    plot_with_pyvista(points, simplices)
