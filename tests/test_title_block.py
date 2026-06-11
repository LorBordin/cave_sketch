import matplotlib.pyplot as plt

from cave_sketch.survey.graphics.title_block import draw_title_block


def test_draw_title_block_all_fields():
    fig = plt.figure(figsize=(8.27, 11.69))
    draw_title_block(
        fig=fig,
        cave_name="Grotta del Vento",
        surveyor_name="John Doe",
        total_length=154.3,
        total_depth=45.2,
    )

    # Verify that an Axes was added for the title block
    # It should be the last or one of the axes in the figure.
    title_ax = None
    for ax in fig.axes:
        # Check if this axes is in the top margin area (e.g., y >= 0.8)
        bbox = ax.get_position()
        if bbox.y0 >= 0.8:
            title_ax = ax
            break

    assert title_ax is not None, "Title block axes not found at the top of the figure"

    # Verify texts
    texts = [t.get_text() for t in title_ax.texts] + [t.get_text() for t in fig.texts]
    joined_text = " ".join(texts)

    assert "Grotta del Vento" in joined_text
    assert "John Doe" in joined_text
    assert "154.3 m" in joined_text
    assert "45.2 m" in joined_text
    assert "Data" in joined_text or "Date" in joined_text


def test_draw_title_block_omits_depth_when_none():
    fig = plt.figure(figsize=(8.27, 11.69))
    draw_title_block(
        fig=fig,
        cave_name="Grotta del Vento",
        surveyor_name="John Doe",
        total_length=154.3,
        total_depth=None,
    )

    title_ax = None
    for ax in fig.axes:
        bbox = ax.get_position()
        if bbox.y0 >= 0.8:
            title_ax = ax
            break

    assert title_ax is not None

    texts = [t.get_text() for t in title_ax.texts] + [t.get_text() for t in fig.texts]
    joined_text = " ".join(texts)

    assert "154.3 m" in joined_text
    assert "Dislivello" not in joined_text
    assert "Depth" not in joined_text


def test_draw_title_block_empty_surveyor():
    fig = plt.figure(figsize=(8.27, 11.69))
    draw_title_block(
        fig=fig,
        cave_name="Grotta Senza Nome",
        surveyor_name="",
        total_length=50.0,
        total_depth=10.0,
    )

    title_ax = None
    for ax in fig.axes:
        bbox = ax.get_position()
        if bbox.y0 >= 0.8:
            title_ax = ax
            break

    assert title_ax is not None

    texts = [t.get_text() for t in title_ax.texts] + [t.get_text() for t in fig.texts]
    joined_text = " ".join(texts)

    assert "Grotta Senza Nome" in joined_text
    assert "50.0 m" in joined_text
    assert "10.0 m" in joined_text


def test_wrap_text_logic():
    from cave_sketch.survey.graphics.title_block import wrap_text
    # Under limit
    assert wrap_text("Short Name", max_chars=20) == "Short Name"
    # Over limit
    long_name = "This is a very long name that exceeds the character limit"
    wrapped = wrap_text(long_name, max_chars=20)
    assert wrapped == "This is a very long\nname that exceeds..."


def test_draw_title_block_long_cave_name_wrapping():
    fig = plt.figure(figsize=(8.27, 11.69))
    draw_title_block(
        fig=fig,
        cave_name="Abisso di Frasassi con Sviluppo Eccezionale e Molto Lungo",
        surveyor_name="Explorer",
        total_length=120.0,
        total_depth=30.0,
    )
    texts = [t.get_text() for t in fig.texts]
    joined_fig_text = " ".join(texts)
    # Checks that it was split into lines
    assert "Abisso di Frasassi con Sviluppo\nEccezionale e Molto Lungo" in joined_fig_text
