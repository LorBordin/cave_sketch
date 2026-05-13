from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial import Delaunay

# === CONFIG ===
DXF_PATH = "/Users/bordil/projects/cave_survey/un_altro_buco_nell_acqua/un_altro_buco_nell_acqua.dxf"
OUT_OBJ = "./cave_mesh.obj"
alpha_multiplier = 1.2  # puoi modificare questo valore per chiudere/aprire la superficie

# === 1. Parse DXF (LINE entities) ===
def parse_dxf_lines_simple(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.readlines()
    segments = []
    current = {}
    for i, line in enumerate(content):
        line = line.strip()
        if line == "LINE":
            if all(k in current for k in ["10","20","30","11","21","31"]):
                seg = (
                    (current["10"], current["20"], current["30"]),
                    (current["11"], current["21"], current["31"])
                )
                segments.append(seg)
            current = {}
        elif line in ["10","20","30","11","21","31"]:
            try:
                value = float(content[i+1].strip())
                current[line] = value
            except Exception:
                pass
    if all(k in current for k in ["10","20","30","11","21","31"]):
        seg = (
            (current["10"], current["20"], current["30"]),
            (current["11"], current["21"], current["31"])
        )
        segments.append(seg)
    return segments

segments = parse_dxf_lines_simple(DXF_PATH)
print(f"Parsed {len(segments)} LINE segments from DXF")

# === 2. Extract unique 3D points ===
pts = []
for a, b in segments:
    pts.append(tuple(a))
    pts.append(tuple(b))

def uniq_points(points, tol=1e-8):
    arr = np.array(points, dtype=float)
    rounded = np.round(arr, 8)
    uniq, idx = np.unique(rounded, axis=0, return_index=True)
    return arr[np.sort(idx)]

pts_arr = uniq_points(pts)
print(f"Extracted {len(pts_arr)} unique points")

# === 3. Delaunay tetrahedrization ===
print("Computing Delaunay tetrahedrization...")
delaunay = Delaunay(pts_arr)
simplices = delaunay.simplices
print(f"Generated {len(simplices)} tetrahedra")

# === 4. Compute circumsphere radii ===
def tetra_circumcenter_radius(p0, p1, p2, p3):
    A = np.vstack([2*(p1-p0), 2*(p2-p0), 2*(p3-p0)])
    b = np.array([np.dot(p1,p1)-np.dot(p0,p0),
                  np.dot(p2,p2)-np.dot(p0,p0),
                  np.dot(p3,p3)-np.dot(p0,p0)])
    try:
        c = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None, None
    R = np.linalg.norm(c - p0)
    return c, R

radii = []
for tet in simplices:
    p0, p1, p2, p3 = pts_arr[tet[0]], pts_arr[tet[1]], pts_arr[tet[2]], pts_arr[tet[3]]
    _, R = tetra_circumcenter_radius(p0,p1,p2,p3)
    radii.append(R if R is not None else np.inf)
radii = np.array(radii)

finite = radii[np.isfinite(radii)]
median_R = np.median(finite)
alpha = median_R * alpha_multiplier
print(f"Median circumsphere radius = {median_R:.4f} | alpha = {alpha:.4f}")

keep_mask = (radii < alpha) & np.isfinite(radii)
kept_indices = np.nonzero(keep_mask)[0]
print(f"Keeping {len(kept_indices)} / {len(simplices)} tetrahedra")

# === 5. Extract boundary faces ===
face_count = Counter()
for i in kept_indices:
    tet = simplices[i]
    faces = [
        tuple(sorted([tet[0], tet[1], tet[2]])),
        tuple(sorted([tet[0], tet[1], tet[3]])),
        tuple(sorted([tet[0], tet[2], tet[3]])),
        tuple(sorted([tet[1], tet[2], tet[3]]))
    ]
    for f in faces:
        face_count[f] += 1

boundary_faces = [f for f, c in face_count.items() if c == 1]
print(f"Extracted {len(boundary_faces)} boundary triangular faces")

# === 6. Save OBJ ===
def save_obj(vertices, faces, path):
    with open(path, "w") as f:
        f.write("# OBJ exported by cave mesh script\n")
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
    print(f"Saved OBJ to {path}")

save_obj(pts_arr, boundary_faces, OUT_OBJ)

# === 7. Visualize ===
fig = plt.figure(figsize=(10,8))
ax = fig.add_subplot(111, projection="3d")

# plot original lines in gray
for a, b in segments:
    ax.plot([a[0],b[0]], [a[1],b[1]], [a[2],b[2]], color='lightgray', linewidth=0.5)

# plot mesh faces
tri_verts = pts_arr[np.array(boundary_faces)]
mesh = Poly3DCollection(tri_verts, alpha=0.9, linewidths=0.05)
mesh.set_edgecolor('k')
ax.add_collection3d(mesh)

xyz = pts_arr
max_range = (xyz.max(axis=0) - xyz.min(axis=0)).max() / 2.0
mid = (xyz.max(axis=0) + xyz.min(axis=0)) / 2.0
ax.set_xlim(mid[0]-max_range, mid[0]+max_range)
ax.set_ylim(mid[1]-max_range, mid[1]+max_range)
ax.set_zlim(mid[2]-max_range, mid[2]+max_range)

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("Reconstructed 3D Surface of the Cave")

plt.tight_layout()
plt.show()
