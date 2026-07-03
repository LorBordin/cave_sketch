package com.cavesketch.app.util

import org.junit.Assert.assertTrue
import org.junit.Test

class GuideRendererTest {

    @Test
    fun testRenderMarkdown_headers() {
        val markdown = "# Hello World\n## Section 1\n### Subsection"
        val html = GuideRenderer.renderMarkdown(markdown)
        assertTrue(html.contains("<h1>Hello World</h1>"))
        assertTrue(html.contains("<h2>Section 1</h2>"))
        assertTrue(html.contains("<h3>Subsection</h3>"))
    }

    @Test
    fun testRenderMarkdown_boldAndLinks() {
        val markdown = "This is **bold** text and [a link](https://github.com)."
        val html = GuideRenderer.renderMarkdown(markdown)
        assertTrue(html.contains("<strong>bold</strong>"))
        assertTrue(html.contains("<a href=\"https://github.com\">a link</a>"))
    }

    @Test
    fun testRenderMarkdown_images() {
        val markdown = "Here is an image: ![alt text](screenshots/img.jpg)"
        val html = GuideRenderer.renderMarkdown(markdown)
        assertTrue(html.contains("<img src=\"screenshots/img.jpg\" alt=\"alt text\" />"))
    }

    @Test
    fun testRenderMarkdown_blockquotesAndCallouts() {
        val markdownNote = "> [!NOTE]\n> This is a note with **bold** info."
        val htmlNote = GuideRenderer.renderMarkdown(markdownNote)
        assertTrue(htmlNote.contains("<blockquote class=\"note\">"))
        assertTrue(htmlNote.contains("This is a note with <strong>bold</strong> info."))

        val markdownTip = "> [!TIP]\n> Just a tip."
        val htmlTip = GuideRenderer.renderMarkdown(markdownTip)
        assertTrue(htmlTip.contains("<blockquote class=\"tip\">"))
        assertTrue(htmlTip.contains("Just a tip."))
    }

    @Test
    fun testRenderMarkdown_lists() {
        val markdown = "- Item 1\n- Item 2\n- Item 3"
        val html = GuideRenderer.renderMarkdown(markdown)
        assertTrue(html.contains("<ul>"))
        assertTrue(html.contains("<li>Item 1</li>"))
        assertTrue(html.contains("<li>Item 2</li>"))
        assertTrue(html.contains("<li>Item 3</li>"))
        assertTrue(html.contains("</ul>"))
    }

    @Test
    fun testRenderMarkdown_tables() {
        val markdown = """
            | Header 1 | Header 2 |
            |---|---|
            | Value 1 | Value 2 |
        """.trimIndent()
        val html = GuideRenderer.renderMarkdown(markdown)
        assertTrue(html.contains("<table>"))
        assertTrue(html.contains("<thead>"))
        assertTrue(html.contains("<th>Header 1</th>"))
        assertTrue(html.contains("<th>Header 2</th>"))
        assertTrue(html.contains("<tbody>"))
        assertTrue(html.contains("<td>Value 1</td>"))
        assertTrue(html.contains("<td>Value 2</td>"))
        assertTrue(html.contains("</table>"))
    }
}
