import matplotlib.pyplot as plt
import pytest

from cave_sketch.survey.graphics.title_block import draw_cave_name, draw_title_block

ROWS = ["Rilevatore: John Doe", "Data: 01/01/2026", "Sviluppo: 154.3 m", "Dislivello: 45.2 m"]


def _page():
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.subplots_adjust(top=0.86)
    ax = fig.add_subplot(1, 1, 1)
    return fig, ax


def test_draw_title_block_draws_rows_in_header():
    fig, ax = _page()
    name_text = draw_cave_name(fig, "Grotta del Vento")
    placement = draw_title_block(fig, name_text, ROWS, [ax])

    assert placement.strategy == "header"
    title_ax = fig.axes[-1]
    assert tuple(title_ax.get_position().bounds) == pytest.approx(placement.rect)
    assert [t.get_text() for t in title_ax.texts] == ROWS
    assert "Grotta del Vento" in [t.get_text() for t in fig.texts]
    plt.close(fig)


def test_rows_are_evenly_spaced_top_to_bottom():
    fig, ax = _page()
    draw_title_block(fig, draw_cave_name(fig, "G"), ROWS, [ax])
    ys = [t.get_position()[1] for t in fig.axes[-1].texts]
    steps = [a - b for a, b in zip(ys, ys[1:])]
    assert all(s > 0 for s in steps)
    assert max(steps) - min(steps) < 1e-9
    plt.close(fig)


def test_draw_cave_name_wraps_long_names():
    fig, _ = _page()
    text = draw_cave_name(fig, "Abisso di Frasassi con Sviluppo Eccezionale e Molto Lungo")
    assert text.get_text() == "Abisso di Frasassi con Sviluppo\nEccezionale e Molto Lungo"
    plt.close(fig)


def test_wrap_text_logic():
    from cave_sketch.survey.graphics.title_block import wrap_text
    # Under limit
    assert wrap_text("Short Name", max_chars=20) == "Short Name"
    # Over limit
    long_name = "This is a very long name that exceeds the character limit"
    wrapped = wrap_text(long_name, max_chars=20)
    assert wrapped == "This is a very long\nname that exceeds..."
