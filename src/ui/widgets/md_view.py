# src/ui/widgets/md_view.py

import markdown
from typing import List, Dict
from PySide6.QtCore import Slot, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView

class MarkdownView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._should_scroll_on_load = True
        # ▼▼▼ 変更点 1/3: スクロール復元用の変数を追加 ▼▼▼
        self._restore_y_pos = -1

        self.loadFinished.connect(self._on_load_finished)

        # (HTMLテンプレートは変更なし)
        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Chat</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" crossorigin="anonymous">
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" integrity="sha384-XjKyOOlGwcjNTAIQHIpgOno0Hl1YQqzUOEleOLALmuqehneUG+vnGctmUb0ZY0l8" crossorigin="anonymous"></script>
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" integrity="sha384-+VBxd3r6XgURycqtZ117nYw44OOcIax56Z4dCRWbxyPt0Koah1uHoK0o4+/RRE05" crossorigin="anonymous"></script>
            <style>
                :root {{
                    --user-bg-color: #4a4a66;
                    --ai-bg-color: #363642;
                    --text-color: #D3D3D3;
                    --background-color: #2B2B2B;
                    --code-bg-color: #424242;
                    --pre-bg-color: #333333;
                }}
                body {{
                    font-family: 'Segoe UI', 'Meiryo', sans-serif;
                    background-color: var(--background-color);
                    color: var(--text-color);
                    padding: 1em;
                    line-height: 1.7;
                    font-size: 16px;
                }}
                .message-container {{
                    display: flex;
                    align-items: flex-start;
                    margin-bottom: 1.5em;
                    max-width: 95%;
                }}
                .message-container.user {{
                    justify-content: flex-end;
                    margin-left: auto;
                }}
                .message-container.ai {{
                    justify-content: flex-start;
                    margin-right: auto;
                }}
                .avatar {{
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background-color: #555;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    flex-shrink: 0;
                }}
                 .message-container.user .avatar {{
                    margin-left: 10px;
                    background-color: #6A5ACD; /* SlateBlue */
                }}
                .message-container.ai .avatar {{
                    margin-right: 10px;
                    background-color: #1E90FF; /* DodgerBlue */
                }}
                .message-bubble {{
                    padding: 0.8em 1.2em;
                    border-radius: 18px;
                    max-width: calc(100% - 60px);
                }}
                .message-container.user .message-bubble {{
                    background-color: var(--user-bg-color);
                    border-bottom-right-radius: 4px;
                }}
                .message-container.ai .message-bubble {{
                    background-color: var(--ai-bg-color);
                    border-bottom-left-radius: 4px;
                }}
                .message-bubble p {{ margin: 0.5em 0; }}
                .message-bubble p:first-child {{ margin-top: 0; }}
                .message-bubble p:last-child {{ margin-bottom: 0; }}
                .message-bubble hr {{ border-color: #555; }}
                
                code {{
                    background-color: var(--code-bg-color);
                    padding: 0.2em 0.4em;
                    margin: 0;
                    font-size: 85%;
                    border-radius: 6px;
                    font-family: Consolas, 'Courier New', monospace;
                }}
                pre {{
                    background-color: var(--pre-bg-color);
                    padding: 1em;
                    border-radius: 8px;
                    overflow-x: auto;
                    border: 1px solid #444;
                }}
                pre > code {{
                    padding: 0;
                    background-color: transparent;
                    border-radius: 0;
                    border: none;
                }}
                .katex-display {{
                    overflow-x: auto;
                    overflow-y: hidden;
                    padding: 0.5em 0;
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
                        throwOnError: false
                    }});
                }});
            </script>
        </body>
        </html>
        """

    # ▼▼▼ 変更点 2/3: _on_load_finished のロジックを強化 ▼▼▼
    @Slot()
    def _on_load_finished(self):
        """ページ読み込み完了時に呼ばれ、スクロール位置を復元または最下部へ移動"""
        if self._restore_y_pos != -1:
            # 保存された位置があれば、そこへ移動
            self.page().runJavaScript(f"window.scrollTo(0, {self._restore_y_pos});")
            self._restore_y_pos = -1 # 一度使ったらリセット
        elif self._should_scroll_on_load:
            # 最下部へスクロールするべき場合
            self.page().runJavaScript("window.scrollTo(0, document.body.scrollHeight);")

    # ▼▼▼ 変更点 3/3: set_messages のロジックを強化 ▼▼▼
    def set_messages(self, messages: List[Dict[str, str]], scroll_to_bottom: bool):
        """
        メッセージのリストを受け取り、HTMLに変換して表示する。
        スクロールしない場合は、現在のスクロール位置を保存してから更新する。
        """
        self._should_scroll_on_load = scroll_to_bottom
        
        # まずHTMLコンテンツを生成
        html_content = ""
        for msg in messages:
            role = msg.get("role", "ai")
            content = msg.get("content", "")
            md_html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
            avatar_char = "U" if role == "user" else "A"
            container_order = ('<div class="message-bubble">' + md_html + '</div>'
                               '<div class="avatar">' + avatar_char + '</div>')
            if role == 'ai':
                 container_order = ('<div class="avatar">' + avatar_char + '</div>'
                                    '<div class="message-bubble">' + md_html + '</div>')
            
            html_content += f'<div class="message-container {role}">{container_order}</div>'

        full_html = self.html_template.format(content=html_content)

        if not scroll_to_bottom:
            # スクロールを維持したい場合
            # 1. 現在位置を取得するJSを実行し、結果を _load_html_with_saved_pos に渡す
            def _load_html_with_saved_pos(pos):
                self._restore_y_pos = pos if pos is not None else 0
                self.setHtml(full_html)

            self.page().runJavaScript("window.scrollY;", _load_html_with_saved_pos)
        else:
            # 最下部にスクロールしたい場合
            self._restore_y_pos = -1 # 復元は不要
            self.setHtml(full_html)