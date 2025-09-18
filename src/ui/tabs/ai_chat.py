# src/ui/tabs/ai_chat.py
#!/usr/bin/env python3
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from nicegui import ui

from src.ui.tabs.base_tab import BaseTab


class AiChat(BaseTab):
    def __init__(self) -> None:
        super().__init__()
        self.user_id = str(uuid4())
        self.avatar = f"https://robohash.org/{self.user_id}?bgset=bg2"
        self.messages: List[Tuple[str, str, str, str]] = []  # per-instance history
        self.text_input = (
            ui.input(placeholder="Start typing...").props("outlined dense").on("keydown.enter", lambda: self.send())
        )

    def build(self, title: str) -> None:
        super()._title(title)

        with ui.column().classes("w-full lp-10"):
            with ui.card().classes("w-full items-left"):
                ui.chat_message("Hello NiceGUI!", name="Robot", stamp="now", avatar="https://robohash.org/ui")

            with ui.card().classes("w-full items-left"):
                with ui.row().classes("w-full lp-10"):
                    self.text_input
                    ui.button("Send", on_click=self.send)

            ui.button("Connect")  # add your own handler if needed

        # show current messages
        self.chat_messages()

    @ui.refreshable
    def chat_messages(self) -> None:
        """Render the chat history."""
        if self.messages:
            for uid, avatar, text, stamp in self.messages:
                ui.chat_message(text=text, stamp=stamp, avatar=avatar, sent=self.user_id == uid)
        else:
            ui.label("No messages yet").classes("mx-auto my-36")
        ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")

    def send(self) -> None:
        """Append a new message and refresh the view."""
        stamp = datetime.now().strftime("%X")
        self.messages.append((self.user_id, self.avatar, self.text_input.value, stamp))
        self.text_input.value = ""
        self.chat_messages.refresh()
