from cave_sketch.utils.filename import sanitize_filename


def test_sanitize_filename_normal():
    assert sanitize_filename("My Cave") == "my_cave"

def test_sanitize_filename_special_chars():
    assert sanitize_filename("Test!@#Survey") == "test_survey"

def test_sanitize_filename_whitespace():
    assert sanitize_filename("  My Cave  ") == "my_cave"

def test_sanitize_filename_consecutive_special():
    assert sanitize_filename("My   Cave!#$Survey") == "my_cave_survey"

def test_sanitize_filename_empty():
    assert sanitize_filename("") == "my_survey"

def test_sanitize_filename_whitespace_only():
    assert sanitize_filename("    ") == "my_survey"

def test_sanitize_filename_preserve_hyphens_underscores():
    assert sanitize_filename("my-cave_survey") == "my-cave_survey"
    assert sanitize_filename("my-_-cave---survey") == "my-_-cave---survey"

def test_sanitize_filename_trailing_special():
    assert sanitize_filename("My Cave Survey!") == "my_cave_survey"
    assert sanitize_filename("!My Cave Survey!") == "my_cave_survey"
