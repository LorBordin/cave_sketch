import pytest

from cave_sketch.style_icons import ICON_SHAPES, icon_strokes


@pytest.mark.parametrize("name", list(ICON_SHAPES))
def test_unit_shape_is_centered_with_largest_side_one(name):
    xs = [u for stroke in ICON_SHAPES[name] for u, _ in stroke]
    ys = [v for stroke in ICON_SHAPES[name] for _, v in stroke]
    assert max(max(xs) - min(xs), max(ys) - min(ys)) == pytest.approx(1.0, abs=1e-3)
    assert (max(xs) + min(xs)) / 2 == pytest.approx(0.0, abs=1e-3)
    assert (max(ys) + min(ys)) / 2 == pytest.approx(0.0, abs=1e-3)


@pytest.mark.parametrize("name", list(ICON_SHAPES))
def test_every_stroke_is_a_polyline(name):
    assert all(len(stroke) >= 2 for stroke in ICON_SHAPES[name])


def test_expected_icons_exist():
    assert set(ICON_SHAPES) == {
        "blocks", "entrance", "continuation", "water_flow", "water_flow_chevron"
    }


def test_icon_strokes_scales_and_translates():
    strokes = icon_strokes("entrance", 10.0, 20.0, size_m=2.0)
    apex = strokes[0][0]  # unit (0.0, 0.5)
    assert apex == pytest.approx((10.0, 21.0))


def test_icon_strokes_rotates_counter_clockwise():
    # Rotating 90 deg CCW turns "up" (+Y) into "west" (-X).
    apex = icon_strokes("entrance", 0.0, 0.0, size_m=1.0, rotation_deg=90.0)[0][0]
    assert apex == pytest.approx((-0.5, 0.0), abs=1e-9)


def test_water_flow_arrow_tip_points_up_at_rotation_zero():
    points = [p for stroke in icon_strokes("water_flow", 0.0, 0.0, 1.0) for p in stroke]
    tip = max(points, key=lambda p: p[1])
    assert tip == pytest.approx((0.0, 0.5))


def test_continuation_is_question_mark_with_dot():
    hook, dot = ICON_SHAPES["continuation"]
    assert len(hook) > len(dot) == 2
    assert max(v for _, v in dot) < min(v for _, v in hook)  # dot sits below the hook


def test_unknown_icon_raises_key_error():
    with pytest.raises(KeyError):
        icon_strokes("no_such_icon", 0.0, 0.0, 1.0)
