# src/ui/widgets/md_view.pyチャット更新時にチャットの一番上に飛ばされないようにしたい。

import re
from PySide6.QtCore import Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
import markdown

class MarkdownView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # --- ここからが修正箇所 ---
        # CSSとJavaScript、両方の波括弧を {{ と }} にエスケープします。
        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Markdown</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" crossorigin="anonymous">
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" integrity="sha384-XjKyOOlGwcjNTAIQHIpgOno0Hl1YQqzUOEleOLALmuqehneUG+vnGctmUb0ZY0l8" crossorigin="anonymous"></script>
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" integrity="sha384-+VBxd3r6XgURycqtZ117nYw44OOcIax56Z4dCRWbxyPt0Koah1uHoK0o4+/RRE05" crossorigin="anonymous"></script>
            <style>
                body {{
                    font-family: sans-serif;
                    background-color: #2B2B2B;
                    color: #D3D3D3;
                    padding: 1em;
                    line-height: 1.6;
                }}
                code {{
                    background-color: #424242;
                    padding: 0.2em 0.4em;
                    margin: 0;
                    font-size: 85%;
                    border-radius: 6px;
                }}
                pre {{
                    background-color: #333333;
                    padding: 1em;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                pre > code {{
                    padding: 0;
                    background-color: transparent;
                    border-radius: 0;
                }}
                .katex {{
                    color: #FFFFFF;
                    font-size: 1.1em;
                }}
                h1, h2, h3 {{
                    border-bottom: 1px solid #555;
                    padding-bottom: 0.3em;
                }}
            </style>
        </head>
        <body>
            <div id="content">{content}</div>
            <script>
                document.addEventListener("DOMContentLoaded", function() {{
                    renderMathInElement(document.getElementById("content"), {{
                        delimiters: [
                            {{left: "$$", right: "$$", display: true}},
                            {{left: "$", right: "$", display: false}},
                            {{left: "\\\\[", right: "\\\\]", display: true}},
                            {{left: "\\\\(", right: "\\\\)", display: false}}
                        ],
                        ignoredTags: [
                            "script", "noscript", "style", "textarea", "pre", "code"
                        ]
                    }});
                }});
            </script>
        </body>
        </html>
        """
        # 接続済みのスロットを管理するためのフラグ
        self._is_scroll_slot_connected = False


    @Slot()
    def _scroll_to_bottom(self):
        """JavaScriptを実行して一番下までスクロールするスロット"""
        scroll_script = "window.scrollTo(0, document.body.scrollHeight);"
        self.page().runJavaScript(scroll_script)
        # 一度実行されたら、不要な再接続を防ぐためにスロットを切断する
        if self._is_scroll_slot_connected:
            try:
                self.loadFinished.disconnect(self._scroll_to_bottom)
                self._is_scroll_slot_connected = False
            except RuntimeError:
                # すでに切断されている場合に発生する可能性のあるエラーを無視
                pass

    def set_markdown(self, md_text: str):
        """
        MarkdownテキストをHTMLに変換して表示し、一番下にスクロールする。
        """
        html_content = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
        full_html = self.html_template.format(content=html_content)
        
        # 毎回新しいHTMLを読み込む前に、以前のスロットが接続されたままになっていないか確認
        if self._is_scroll_slot_connected:
            try:
                self.loadFinished.disconnect(self._scroll_to_bottom)
            except RuntimeError:
                pass # すでに切断されている場合は何もしない
        
        # 新しいHTMLをセットする前にスロットを接続
        self.loadFinished.connect(self._scroll_to_bottom)
        self._is_scroll_slot_connected = True
        
        self.setHtml(full_html)