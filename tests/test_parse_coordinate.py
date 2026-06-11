from cave_sketch.geo.coordinates import parse_coordinate


def test_parse_coordinate_dot():
    assert parse_coordinate("45.678901") == 45.678901


def test_parse_coordinate_comma():
    assert parse_coordinate("45,678901") == 45.678901


def test_parse_coordinate_negative_dot():
    assert parse_coordinate("-7.654321") == -7.654321


def test_parse_coordinate_negative_comma():
    assert parse_coordinate("-7,654321") == -7.654321


def test_parse_coordinate_integer():
    assert parse_coordinate("45") == 45.0


def test_parse_coordinate_whitespace():
    assert parse_coordinate("  45.678901  ") == 45.678901


def test_parse_coordinate_empty():
    assert parse_coordinate("") is None


def test_parse_coordinate_whitespace_only():
    assert parse_coordinate("   ") is None


def test_parse_coordinate_letters():
    assert parse_coordinate("abc") is None


def test_parse_coordinate_multiple_dots():
    assert parse_coordinate("45.67.89") is None


def test_parse_coordinate_multiple_commas():
    assert parse_coordinate("45,67,89") is None
