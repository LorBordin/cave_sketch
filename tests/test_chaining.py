# ruff: noqa: E501
from cave_sketch.features.chaining import chain_segments_by_type


def test_straight_line():
    lines = [
        {"from": {"id": "1", "lat": 1.0, "lon": 1.0}, "to": {"id": "2", "lat": 2.0, "lon": 2.0}, "type": "wall"},
        {"from": {"id": "2", "lat": 2.0, "lon": 2.0}, "to": {"id": "3", "lat": 3.0, "lon": 3.0}, "type": "wall"},
        {"from": {"id": "3", "lat": 3.0, "lon": 3.0}, "to": {"id": "4", "lat": 4.0, "lon": 4.0}, "type": "wall"},
    ]
    res = chain_segments_by_type(lines)
    assert "wall" in res
    assert len(res["wall"]) == 1
    # Note: order of nodes could be 1->2->3->4 or 4->3->2->1.
    pts = res["wall"][0]
    assert len(pts) == 4
    assert pts in ([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0], [4.0, 4.0]], [[4.0, 4.0], [3.0, 3.0], [2.0, 2.0], [1.0, 1.0]])

def test_reverse_duplicate_edges():
    lines = [
        {"from": {"id": "1", "lat": 1.0, "lon": 1.0}, "to": {"id": "2", "lat": 2.0, "lon": 2.0}, "type": "wall"},
        {"from": {"id": "2", "lat": 2.0, "lon": 2.0}, "to": {"id": "1", "lat": 1.0, "lon": 1.0}, "type": "wall"},
        {"from": {"id": "2", "lat": 2.0, "lon": 2.0}, "to": {"id": "3", "lat": 3.0, "lon": 3.0}, "type": "wall"},
    ]
    res = chain_segments_by_type(lines)
    pts = res["wall"][0]
    assert len(res["wall"]) == 1
    assert len(pts) == 3
    assert pts in ([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]], [[3.0, 3.0], [2.0, 2.0], [1.0, 1.0]])

def test_y_junction():
    lines = [
        {"from": {"id": "c", "lat": 0.0, "lon": 0.0}, "to": {"id": "1", "lat": 1.0, "lon": 1.0}, "type": "wall"},
        {"from": {"id": "c", "lat": 0.0, "lon": 0.0}, "to": {"id": "2", "lat": -1.0, "lon": 1.0}, "type": "wall"},
        {"from": {"id": "c", "lat": 0.0, "lon": 0.0}, "to": {"id": "3", "lat": 0.0, "lon": -1.0}, "type": "wall"},
    ]
    res = chain_segments_by_type(lines)
    # The center node 'c' has degree 3, so it splits into 3 polylines
    assert len(res["wall"]) == 3
    for poly in res["wall"]:
        assert len(poly) == 2
        assert [0.0, 0.0] in poly

def test_closed_loop():
    lines = [
        {"from": {"id": "1", "lat": 1.0, "lon": 1.0}, "to": {"id": "2", "lat": 2.0, "lon": 1.0}, "type": "wall"},
        {"from": {"id": "2", "lat": 2.0, "lon": 1.0}, "to": {"id": "3", "lat": 2.0, "lon": 2.0}, "type": "wall"},
        {"from": {"id": "3", "lat": 2.0, "lon": 2.0}, "to": {"id": "1", "lat": 1.0, "lon": 1.0}, "type": "wall"},
    ]
    res = chain_segments_by_type(lines)
    assert len(res["wall"]) == 1
    poly = res["wall"][0]
    assert len(poly) == 4
    assert poly[0] == poly[-1] # First vertex == last vertex

def test_mixed_types():
    lines = [
        {"from": {"id": "1", "lat": 1.0, "lon": 1.0}, "to": {"id": "2", "lat": 2.0, "lon": 2.0}, "type": "wall"},
        {"from": {"id": "2", "lat": 2.0, "lon": 2.0}, "to": {"id": "3", "lat": 3.0, "lon": 3.0}, "type": "water"},
    ]
    res = chain_segments_by_type(lines)
    assert len(res.keys()) == 2
    assert len(res["wall"]) == 1
    assert len(res["water"]) == 1
    assert res["wall"][0] in ([[1.0, 1.0], [2.0, 2.0]], [[2.0, 2.0], [1.0, 1.0]])
    assert res["water"][0] in ([[2.0, 2.0], [3.0, 3.0]], [[3.0, 3.0], [2.0, 2.0]])
