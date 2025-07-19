# src/ui/widgets/md_view.py

import markdown
import json
from typing import List, Dict
from PySide6.QtCore import Slot, QObject, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

# QWebChannelとBridgeは将来の「再生成」ボタン等のために残しておきます
class Bridge(QObject):
    regenerate_requested = Signal(int)
    good_rating_requested = Signal(int)
    bad_rating_requested = Signal(int)

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
                :root { --user-bg-color: #4a4a66; --ai-bg-color: #363642; --text-color: #D3D3D3; --background-color: #2B2B2B; --code-bg-color: #1E1E1E; --pre-bg-color: #1E1E1E; --button-bg-color: #4f4f66; --button-hover-bg-color: #6a6a88; }
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
                pre { position: relative; background-color: var(--pre-bg-color); padding: 1em; padding-top: 2.5em; border-radius: 8px; overflow-x: auto; border: 1px solid #444; }
                
                /* ▼▼▼ CSSの変更箇所 ▼▼▼ */
                .copy-button {
                    position: absolute;
                    top: 8px;
                    right: 8px;
                    background: var(--button-bg-color);
                    color: var(--text-color);
                    border: none;
                    padding: 4px 10px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 12px;
                    /* JSで制御するための初期状態 */
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.2s ease-in-out;
                }
                .copy-button.visible {
                    opacity: 1;
                    pointer-events: auto;
                }
                /* ▲▲▲ CSSの変更箇所 ▲▲▲ */
                
                .copy-button:hover { background: var(--button-hover-bg-color); }
                code { font-family: Consolas, 'Courier New', monospace; font-size: 85%; }
                pre > code { padding: 0; background-color: transparent; border-radius: 0; border: none; }
                .katex-display { overflow-x: auto; overflow-y: hidden; padding: 0.5em 0; }
            </style>
        </head>
        <body>
            <div id="chat-container"></div>
            <script>
                let qtBridge;
                new QWebChannel(qt.webChannelTransport, function (channel) { qtBridge = channel.objects.bridge; });

                /* ▼▼▼ JavaScriptの変更箇所 ▼▼▼ */
                function copyCodeToClipboard(button, codeText) {
                    const textArea = document.createElement('textarea');
                    textArea.value = codeText;
                    textArea.style.position = 'fixed';
                    textArea.style.top = '-9999px';
                    textArea.style.left = '-9999px';
                    document.body.appendChild(textArea);
                    textArea.select();
                    try {
                        document.execCommand('copy');
                        button.innerText = 'コピーしました！';
                    } catch (err) {
                        console.error('コピーに失敗しました', err);
                        button.innerText = '失敗';
                    }
                    document.body.removeChild(textArea);
                    setTimeout(() => { button.innerText = 'コピー'; }, 2000);
                }

                function addCopyButtons(element) {
                    const codeBlocks = element.querySelectorAll('pre');
                    codeBlocks.forEach(block => {
                        if (block.querySelector('.copy-button')) { return; }
                        const button = document.createElement('button');
                        button.className = 'copy-button';
                        button.innerText = 'コピー';
                        const code = block.querySelector('code').innerText;
                        
                        button.addEventListener('click', () => {
                            copyCodeToClipboard(button, code);
                        });
                        
                        // JavaScriptでマウスイベントを直接制御
                        block.addEventListener('mouseenter', () => {
                            button.classList.add('visible');
                        });
                        block.addEventListener('mouseleave', () => {
                            button.classList.remove('visible');
                        });
                        
                        block.appendChild(button);
                    });
                }
                /* ▲▲▲ JavaScriptの変更箇所 ▲▲▲ */

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
                    if (msg.role === 'user') { wrapper.appendChild(contentDiv); wrapper.appendChild(avatar); }
                    else { wrapper.appendChild(avatar); wrapper.appendChild(contentDiv); }
                    return wrapper;
                }
                window.set_all_messages = function(messages) {
                    const container = document.getElementById('chat-container');
                    container.innerHTML = '';
                    messages.forEach(msg => { container.appendChild(createMessageElement(msg)); });
                    renderMathInElement(container, { delimiters: [ {left: "$$", right: "$$", display: true}, {left: "$", right: "$", display: false} ], throwOnError: false });
                    addCopyButtons(container);
                    window.scrollTo(0, document.body.scrollHeight);
                }
                window.append_message = function(msg, scroll) {
                    const container = document.getElementById('chat-container');
                    const el = createMessageElement(msg);
                    container.appendChild(el);
                    renderMathInElement(el, { delimiters: [ {left: "$$", right: "$$", display: true}, {left: "$", right: "$", display: false} ], throwOnError: false });
                    addCopyButtons(el);
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
        self._page_loaded = True
        self._process_js_queue()

    def _run_or_queue_js(self, js_code: str):
        if self._page_loaded:
            self.page().runJavaScript(js_code)
        else:
            self._js_call_queue.append(js_code)

    def _process_js_queue(self):
        if self._page_loaded:
            for code in self._js_call_queue:
                self.page().runJavaScript(code)
            self._js_call_queue.clear()
            
    def _convert_message_to_js_format(self, message: Dict) -> Dict:
        html_content = markdown.markdown(message.get("content", ""), extensions=['fenced_code', 'tables'])
        return { "id": message.get("id"), "role": message.get("role"), "content": message.get("content"), "html_content": html_content }

    @Slot(list)
    def set_messages(self, messages: List[Dict]):
        js_messages = [self._convert_message_to_js_format(m) for m in messages]
        js_code = f"window.set_all_messages({json.dumps(js_messages)});"
        self._run_or_queue_js(js_code)

    @Slot(dict, bool)
    def add_message(self, message: Dict, scroll: bool):
        js_message = self._convert_message_to_js_format(message)
        js_code = f"window.append_message({json.dumps(js_message)}, {str(scroll).lower()});"
        self._run_or_queue_js(js_code)