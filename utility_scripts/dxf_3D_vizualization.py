import matplotlib.pyplot as plt


def parse_dxf_lines(file_path):
    """
    Legge un file DXF e restituisce una lista di segmenti 3D (solo entità LINE).
    Ogni segmento è ((x1, y1, z1), (x2, y2, z2))
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

    # aggiungi l'ultimo se completo
    if all(k in current for k in ["10", "20", "30", "11", "21", "31"]):
        seg = (
            (current["10"], current["20"], current["30"]),
            (current["11"], current["21"], current["31"])
        )
        segments.append(seg)

    return segments


def plot_3d_segments(segments):
    """Visualizza le linee 3D con Matplotlib."""
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    for (x1, y1, z1), (x2, y2, z2) in segments:
        ax.plot([x1, x2], [y1, y2], [z1, z2], color='dodgerblue', linewidth=1)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Rilievo 3D - DXF")
    ax.view_init(elev=30, azim=45)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    
    dxf_path = "/Users/bordil/projects/cave_survey/un_altro_buco_nell_acqua/un_altro_buco_nell_acqua.dxf"
    segments = parse_dxf_lines(dxf_path)
    print(f"Letti {len(segments)} segmenti 3D")
    plot_3d_segments(segments)
