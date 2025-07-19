# src/ui/widgets/md_view.py

import markdown
import json
from typing import List, Dict
from PySide6.QtCore import Slot, QObject, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

class Bridge(QObject):
    """PythonとJavaScriptの通信を仲介するブリッジオブジェクト"""
    copy_requested = Signal(int, str) # contentも渡すように変更
    regenerate_requested = Signal(int)
    good_rating_requested = Signal(int)
    bad_rating_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
    
    @Slot(int, str)
    def on_copy_requested(self, msg_id: int, content: str): self.copy_requested.emit(msg_id, content)
    @Slot(int)
    def on_regenerate_requested(self, msg_id: int): self.regenerate_requested.emit(msg_id)
    @Slot(int)
    def on_good_rating_requested(self, msg_id: int): self.good_rating_requested.emit(msg_id)
    @Slot(int)
    def on_bad_rating_requested(self, msg_id: int): self.bad_rating_requested.emit(msg_id)


class MarkdownView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._page_loaded = False
        self._js_call_queue = []

        self.channel = QWebChannel(self.page())
        self.page().setWebChannel(self.channel)
        self.bridge = Bridge()
        self.channel.registerObject("bridge", self.bridge)

        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Chat</title>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV" crossorigin="anonymous">
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" integrity="sha384-XjKyOOlGwcjNTAIQHIpgOno0Hl1YQqzUOEleOLALmuqehneUG+vnGctmUb0ZY0l8" crossorigin="anonymous"></script>
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" integrity="sha384-+VBxd3r6XgURycqtZ117nYw44OOcIax56Z4dCRWbxyPt0Koah1uHoK0o4+/RRE05" crossorigin="anonymous"></script>
            <style>
                :root { --user-bg-color: #4a4a66; --ai-bg-color: #363642; --text-color: #D3D3D3; --background-color: #2B2B2B; --code-bg-color: #424242; --pre-bg-color: #333333; --button-bg-color: #4f4f66; --button-hover-bg-color: #6a6a88; }
                body { font-family: 'Segoe UI', 'Meiryo', sans-serif; background-color: var(--background-color); color: var(--text-color); padding: 1em; line-height: 1.7; font-size: 16px; overflow-x: hidden; }
                #chat-container { padding-bottom: 50px; }
                .message-wrapper { display: flex; align-items: flex-start; margin-bottom: 0.5em; max-width: 95%; }
                .message-wrapper.user { justify-content: flex-end; margin-left: auto; }
                .message-wrapper.ai { justify-content: flex-start; margin-right: auto; }
                .avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #555; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; margin-top: 5px; }
                .message-wrapper.user .avatar { margin-left: 10px; background-color: #6A5ACD; }
                .message-wrapper.ai .avatar { margin-right: 10px; background-color: #1E90FF; }
                .message-content { display: flex; flex-direction: column; max-width: calc(100% - 60px); }
                .message-bubble { padding: 0.8em 1.2em; border-radius: 18px; background-color: var(--ai-bg-color); }
                .message-wrapper.user .message-bubble { background-color: var(--user-bg-color); border-bottom-right-radius: 4px; }
                .message-wrapper.ai .message-bubble { border-bottom-left-radius: 4px; }
                .message-bubble p:first-child { margin-top: 0; }
                .message-bubble p:last-child { margin-bottom: 0; }
                .toolbar { display: flex; justify-content: flex-end; padding: 4px 8px 0 0; opacity: 0; transition: opacity 0.2s; height: 0; overflow: hidden; }
                .message-content:hover .toolbar { opacity: 1; height: auto; }
                .toolbar button { background: var(--button-bg-color); border: none; color: var(--text-color); padding: 4px 8px; border-radius: 4px; cursor: pointer; margin-left: 5px; font-size: 12px; }
                .toolbar button:hover { background: var(--button-hover-bg-color); }
                code { background-color: var(--code-bg-color); padding: 0.2em 0.4em; margin: 0; font-size: 85%; border-radius: 6px; font-family: Consolas, 'Courier New', monospace;}
                pre { background-color: var(--pre-bg-color); padding: 1em; border-radius: 8px; overflow-x: auto; border: 1px solid #444;}
                pre > code {padding: 0; background-color: transparent; border-radius: 0; border: none;}
                .katex-display { overflow-x: auto; overflow-y: hidden; padding: 0.5em 0; }
            </style>
        </head>
        <body>
            <div id="chat-container"></div>
            <script>
                let qtBridge;
                // ▼▼▼ 修正点 1/3: {{}} を {} に修正 ▼▼▼
                new QWebChannel(qt.webChannelTransport, function (channel) {
                    qtBridge = channel.objects.bridge;
                });

                function createMessageElement(msg) {
                    const wrapper = document.createElement('div');
                    wrapper.className = `message-wrapper ${msg.role}`;
                    wrapper.id = `message-${msg.id}`;
                    
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'message-content';

                    const bubble = document.createElement('div');
                    bubble.className = 'message-bubble';
                    bubble.innerHTML = msg.html_content;
                    
                    contentDiv.appendChild(bubble);

                    const avatar = document.createElement('div');
                    avatar.className = 'avatar';
                    avatar.textContent = (msg.role === 'user') ? 'U' : 'A';

                    if (msg.role === 'user') {
                        wrapper.appendChild(contentDiv);
                        wrapper.appendChild(avatar);
                    } else {
                        wrapper.appendChild(avatar);
                        wrapper.appendChild(contentDiv);
                    }
                    return wrapper;
                }

                window.set_all_messages = function(messages) {
                    const container = document.getElementById('chat-container');
                    container.innerHTML = '';
                    messages.forEach(msg => { container.appendChild(createMessageElement(msg)); });
                    // ▼▼▼ 修正点 2/3: {{}} を {} に修正 ▼▼▼
                    renderMathInElement(container, {
                        delimiters: [
                            {left: "$$", right: "$$", display: true},
                            {left: "$", right: "$", display: false}
                        ],
                        throwOnError: false
                    });
                    window.scrollTo(0, document.body.scrollHeight);
                }

                window.append_message = function(msg, scroll) {
                    const container = document.getElementById('chat-container');
                    const el = createMessageElement(msg);
                    container.appendChild(el);
                    // ▼▼▼ 修正点 3/3: {{}} を {} に修正 ▼▼▼
                    renderMathInElement(el, {
                        delimiters: [
                            {left: "$$", right: "$$", display: true},
                            {left: "$", right: "$", display: false}
                        ],
                        throwOnError: false
                    });
                    if (scroll) { window.scrollTo(0, document.body.scrollHeight); }
                }
            </script>
        </body>
        </html>
        """
        self.loadFinished.connect(self._on_load_finished)
        self.setHtml(self.html_template)

    @Slot()
    def _on_load_finished(self):
        """ページの読み込みが完了したら呼ばれる"""
        self._page_loaded = True
        self._process_js_queue()

    def _run_or_queue_js(self, js_code: str):
        """ページの準備ができていればJSを実行し、できていなければキューに入れる"""
        if self._page_loaded:
            self.page().runJavaScript(js_code)
        else:
            self._js_call_queue.append(js_code)

    def _process_js_queue(self):
        """キュー内のJS命令を順番に実行する"""
        if self._page_loaded:
            for code in self._js_call_queue:
                self.page().runJavaScript(code)
            self._js_call_queue.clear()
            
    def _convert_message_to_js_format(self, message: Dict) -> Dict:
        html_content = markdown.markdown(message.get("content", ""), extensions=['fenced_code', 'tables'])
        return {
            "id": message.get("id"),
            "role": message.get("role"),
            "content": message.get("content"), # 生のテキストも渡す
            "html_content": html_content
        }

    @Slot(list)
    def set_messages(self, messages: List[Dict]):
        """（初回読み込み用）チャット履歴全体をセットする命令をキューに入れる"""
        js_messages = [self._convert_message_to_js_format(m) for m in messages]
        js_code = f"window.set_all_messages({json.dumps(js_messages)});"
        self._run_or_queue_js(js_code)

    @Slot(dict, bool)
    def add_message(self, message: Dict, scroll: bool):
        """（動的追加用）新しいメッセージを1件追加する命令をキューに入れる"""
        js_message = self._convert_message_to_js_format(message)
        js_code = f"window.append_message({json.dumps(js_message)}, {str(scroll).lower()});"
        self._run_or_queue_js(js_code)