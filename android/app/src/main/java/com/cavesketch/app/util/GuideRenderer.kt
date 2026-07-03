package com.cavesketch.app.util

import android.content.Context
import java.io.BufferedReader
import java.io.InputStreamReader

object GuideRenderer {

    fun renderFromAssets(context: Context, assetPath: String): String {
        val markdown = context.assets.open(assetPath).use { inputStream ->
            BufferedReader(InputStreamReader(inputStream)).use { reader ->
                reader.readText()
            }
        }
        val bodyHtml = renderMarkdown(markdown)
        return wrapWithHtmlStructure(bodyHtml)
    }

    fun wrapWithHtmlStructure(bodyHtml: String): String {
        return """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" href="guide.css">
            </head>
            <body>
                $bodyHtml
            </body>
            </html>
        """.trimIndent()
    }

    fun renderMarkdown(markdown: String): String {
        val lines = markdown.split(Regex("\\r?\\n"))
        val htmlBuilder = StringBuilder()
        
        var currentBlockType = BlockType.NONE
        val accumulatedLines = mutableListOf<String>()

        fun closeCurrentBlock() {
            if (accumulatedLines.isEmpty()) return
            when (currentBlockType) {
                BlockType.PARAGRAPH -> {
                    val content = accumulatedLines.joinToString(" ")
                    htmlBuilder.append("<p>").append(applyInlineStyles(content)).append("</p>\n")
                }
                BlockType.BLOCKQUOTE -> {
                    var isNote = false
                    var isTip = false
                    val cleanLines = mutableListOf<String>()
                    for (line in accumulatedLines) {
                        val trimmedLine = line.removePrefix(">").trim()
                        if (trimmedLine.startsWith("[!NOTE]")) {
                            isNote = true
                        } else if (trimmedLine.startsWith("[!TIP]")) {
                            isTip = true
                        } else {
                            cleanLines.add(trimmedLine)
                        }
                    }
                    val cssClass = when {
                        isNote -> " class=\"note\""
                        isTip -> " class=\"tip\""
                        else -> ""
                    }
                    val content = cleanLines.joinToString(" ")
                    htmlBuilder.append("<blockquote$cssClass><p>").append(applyInlineStyles(content)).append("</p></blockquote>\n")
                }
                BlockType.LIST -> {
                    htmlBuilder.append("<ul>\n")
                    for (line in accumulatedLines) {
                        val content = line.removePrefix("-").trim()
                        htmlBuilder.append("  <li>").append(applyInlineStyles(content)).append("</li>\n")
                    }
                    htmlBuilder.append("</ul>\n")
                }
                BlockType.TABLE -> {
                    htmlBuilder.append("<table>\n")
                    var isHeader = true
                    for (line in accumulatedLines) {
                        val parts = line.split("|").map { it.trim() }.filterIndexed { index, _ -> 
                            index > 0 && index < line.split("|").size - 1 
                        }
                        if (parts.isEmpty()) continue
                        if (parts.all { it.startsWith("-") && it.endsWith("-") || it == "-" }) {
                            continue
                        }
                        if (isHeader) {
                            htmlBuilder.append("<thead>\n  <tr>\n")
                            for (part in parts) {
                                htmlBuilder.append("    <th>").append(applyInlineStyles(part)).append("</th>\n")
                            }
                            htmlBuilder.append("  </tr>\n</thead>\n<tbody>\n")
                            isHeader = false
                        } else {
                            htmlBuilder.append("  <tr>\n")
                            for (part in parts) {
                                htmlBuilder.append("    <td>").append(applyInlineStyles(part)).append("</td>\n")
                            }
                            htmlBuilder.append("  </tr>\n")
                        }
                    }
                    if (!isHeader) {
                        htmlBuilder.append("</tbody>\n")
                    }
                    htmlBuilder.append("</table>\n")
                }
                else -> {}
            }
            accumulatedLines.clear()
            currentBlockType = BlockType.NONE
        }

        for (line in lines) {
            val trimmed = line.trim()
            if (trimmed.isEmpty()) {
                closeCurrentBlock()
                continue
            }

            // Headers
            if (trimmed.startsWith("#")) {
                closeCurrentBlock()
                val headerLevel = trimmed.takeWhile { it == '#' }.length
                val content = trimmed.substring(headerLevel).trim()
                htmlBuilder.append("<h$headerLevel>").append(applyInlineStyles(content)).append("</h$headerLevel>\n")
                continue
            }

            // Horizontal rule
            if (trimmed == "---") {
                closeCurrentBlock()
                htmlBuilder.append("<hr />\n")
                continue
            }

            // Blockquote
            if (trimmed.startsWith(">")) {
                if (currentBlockType != BlockType.BLOCKQUOTE) {
                    closeCurrentBlock()
                    currentBlockType = BlockType.BLOCKQUOTE
                }
                accumulatedLines.add(trimmed)
                continue
            }

            // List item
            if (trimmed.startsWith("- ")) {
                if (currentBlockType != BlockType.LIST) {
                    closeCurrentBlock()
                    currentBlockType = BlockType.LIST
                }
                accumulatedLines.add(trimmed)
                continue
            }

            // Table row
            if (trimmed.startsWith("|")) {
                if (currentBlockType != BlockType.TABLE) {
                    closeCurrentBlock()
                    currentBlockType = BlockType.TABLE
                }
                accumulatedLines.add(trimmed)
                continue
            }

            // Regular paragraph line
            if (currentBlockType != BlockType.PARAGRAPH) {
                closeCurrentBlock()
                currentBlockType = BlockType.PARAGRAPH
            }
            accumulatedLines.add(trimmed)
        }

        closeCurrentBlock()
        return htmlBuilder.toString().trim()
    }

    private fun applyInlineStyles(text: String): String {
        var result = text
        result = result.replace(Regex("\\*\\*(.*?)\\*\\*"), "<strong>$1</strong>")
        result = result.replace(Regex("!\\[(.*?)\\]\\((.*?)\\)"), "<img src=\"$2\" alt=\"$1\" />")
        result = result.replace(Regex("\\[(.*?)\\]\\((.*?)\\)"), "<a href=\"$2\">$1</a>")
        return result
    }

    private enum class BlockType {
        NONE, PARAGRAPH, BLOCKQUOTE, LIST, TABLE
    }
}
