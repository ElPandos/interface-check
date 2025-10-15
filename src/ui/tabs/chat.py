from datetime import UTC, datetime
from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.json import Json
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "chat"
LABEL = "Chat"


class ChatTab(BaseTab):
    ICON_NAME: str = "smart_toy"  # tips_and_updates

    def __init__(self, *, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class ChatPanel(BasePanel, MultiScreen):
    def __init__(
        self,
        *,
        build: bool = False,
        config: Config | None = None,
        ssh_connection: SshConnection | None = None,
        host_handler: Any = None,
        icon: ui.icon | None = None,
    ) -> None:
        BasePanel.__init__(self, NAME, LABEL, ChatTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._config = config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._chat_screens: dict[int, Any] = {}

        if build:
            self.build()

    def build(self) -> None:
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base("AI Chat")
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str) -> None:
        with (
            ui.card().classes(classes),
            ui.expansion(f"AI Chat {screen_num}", icon="smart_toy", value=True).classes("w-full"),
        ):
            if screen_num not in self._chat_screens:
                self._chat_screens[screen_num] = ChatContent(self._host_handler)

            chat = self._chat_screens[screen_num]
            chat.build(screen_num)


class ChatContent:
    def __init__(self, host_handler: Any = None) -> None:
        self._current_model: str = "GPT-4"
        self._chat_history: list[dict[str, str]] = []
        self._host_handler = host_handler
        self.chat_container: ui.column | None = None
        self.message_input: ui.textarea | None = None

    def build(self, screen_num: int) -> None:
        """Build ChatGPT-like interface for the screen."""
        with ui.column().classes("w-full h-full gap-4"):
            # Model selector and controls
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                ui.select(
                    ["GPT-4", "GPT-3.5", "Claude", "Local AI"],
                    value=self._current_model,
                    on_change=lambda e: setattr(self, "_current_model", e.value),
                ).classes("w-32")
                ui.button("Clear Chat", icon="clear_all", on_click=lambda s=screen_num: self._clear_chat(s)).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800"
                )
                ui.button("Export Chat", icon="download", on_click=lambda s=screen_num: self._export_chat(s)).classes(
                    "bg-blue-300 hover:bg-blue-400 text-blue-900"
                )
                ui.button(
                    "System Context", icon="settings", on_click=lambda s=screen_num: self._add_system_context(s)
                ).classes("bg-green-300 hover:bg-green-400 text-green-900")

            # Chat messages area
            with ui.scroll_area().classes("w-full h-96 border border-gray-300 rounded p-4 bg-gray-50"):
                self.chat_container = ui.column().classes("w-full gap-2")
                self._restore_chat_history()

            # Input area
            with ui.row().classes("w-full gap-2"):
                self.message_input = (
                    ui.textarea(
                        placeholder="Type your message here... (Shift+Enter for new line, Enter to send)", value=""
                    )
                    .classes("flex-1")
                    .props("outlined autogrow")
                )

                with ui.column().classes("gap-1"):
                    ui.button("Send", icon="send", on_click=lambda s=screen_num: self._send_message(s)).classes(
                        "bg-blue-500 hover:bg-blue-600 text-white"
                    )
                    ui.button("Voice", icon="mic", on_click=lambda s=screen_num: self._voice_input(s)).classes(
                        "bg-purple-300 hover:bg-purple-400 text-purple-900"
                    )

            # Quick actions
            with (
                ui.expansion("Quick Actions", icon="flash_on").classes("w-full mt-4"),
                ui.row().classes("w-full gap-2 flex-wrap"),
            ):
                ui.button("Explain Code", on_click=lambda s=screen_num: self._quick_action(s, "explain_code")).classes(
                    "bg-orange-300 hover:bg-orange-400 text-orange-900"
                )
                ui.button("Debug Issue", on_click=lambda s=screen_num: self._quick_action(s, "debug")).classes(
                    "bg-red-300 hover:bg-red-400 text-red-900"
                )
                ui.button("Network Help", on_click=lambda s=screen_num: self._quick_action(s, "network")).classes(
                    "bg-teal-300 hover:bg-teal-400 text-teal-900"
                )
                ui.button("Generate Script", on_click=lambda s=screen_num: self._quick_action(s, "script")).classes(
                    "bg-green-300 hover:bg-green-400 text-green-900"
                )

    def _restore_chat_history(self) -> None:
        """Restore chat history when rebuilding UI."""
        if not self.chat_container:
            return

        with self.chat_container:
            if not self._chat_history:
                ui.label("👋 Hello! I'm your AI assistant. How can I help you today?").classes("text-gray-600 italic")
            else:
                for msg in self._chat_history:
                    self._render_message(msg["role"], msg["content"], msg["timestamp"])

    def _render_message(self, role: str, content: str, timestamp: str) -> None:
        """Render a single message in the chat."""
        if role == "user":
            with (
                ui.row().classes("w-full justify-end mb-2"),
                ui.card().classes("max-w-xs bg-blue-500 text-white p-3 rounded-lg"),
            ):
                ui.label(content).classes("text-sm")
                ui.label(timestamp).classes("text-xs opacity-70 mt-1")
        else:
            with (
                ui.row().classes("w-full justify-start mb-2"),
                ui.card().classes("max-w-xs bg-white border p-3 rounded-lg"),
            ):
                ui.label(content).classes("text-sm")
                ui.label(timestamp).classes("text-xs text-gray-500 mt-1")

    def _send_message(self, _screen_num: int) -> None:
        """Send message to AI."""
        if not self.message_input:
            return

        message = self.message_input.value.strip()
        if not message:
            return

        # Add user message
        self._add_message("user", message)
        self.message_input.value = ""

        # Simulate AI response (replace with actual AI API call)
        self._simulate_ai_response(message)

    def _add_message(self, role: str, content: str) -> None:
        """Add message to chat history and display."""
        if not self.chat_container:
            return

        timestamp = datetime.now(UTC).strftime("%H:%M")
        message = {"role": role, "content": content, "timestamp": timestamp}
        self._chat_history.append(message)

        with self.chat_container:
            self._render_message(role, content, timestamp)

    def _simulate_ai_response(self, user_message: str) -> None:
        """Simulate AI response (replace with actual AI API)."""
        # Simple response simulation
        responses = {
            "hello": "Hello! I'm here to help you with network diagnostics, system administration, and technical questions.",
            "help": "I can assist you with:\n• Network troubleshooting\n• System diagnostics\n• Code explanation\n• Script generation\n• SSH and remote management",
            "network": "For network issues, I can help you analyze interface configurations, troubleshoot connectivity, and interpret diagnostic outputs.",
            "default": f"I understand you're asking about: '{user_message[:50]}...'\n\nI'm a simulated AI assistant. In a real implementation, I would connect to an AI service like OpenAI's API to provide intelligent responses.",
        }

        # Simple keyword matching
        response = responses.get("default", "I'm here to help!")
        for key, value in responses.items():
            if key in user_message.lower():
                response = value
                break

        # Add AI response after a short delay
        ui.timer(1.0, lambda: self._add_message("assistant", response), once=True)

    def _clear_chat(self, _screen_num: int) -> None:
        """Clear chat history."""
        if not self.chat_container:
            return

        self._chat_history.clear()
        self.chat_container.clear()
        with self.chat_container:
            ui.label("👋 Chat cleared. How can I help you?").classes("text-gray-600 italic")
        ui.notify("Chat cleared", color="info")

    def _export_chat(self, _screen_num: int) -> None:
        """Export chat history."""
        if not self._chat_history:
            ui.notify("No chat history to export", color="warning")
            return

        chat_data = {
            "model": self._current_model,
            "timestamp": datetime.now(UTC).isoformat(),
            "messages": self._chat_history,
        }

        Json.export_download(chat_data, "ai_chat", success_message="Chat history exported successfully")

    def _add_system_context(self, _screen_num: int) -> None:
        """Add system context to chat."""
        connections = 0
        if self._host_handler and hasattr(self._host_handler, "_connect_route"):
            connections = len(getattr(self._host_handler, "_connect_route", []))
        context = f"System Context:\n• Current host connections: {connections}\n• Model: {self._current_model}\n• Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}"
        self._add_message("system", context)

    def _voice_input(self, _screen_num: int) -> None:
        """Voice input placeholder."""
        ui.notify("Voice input feature would be implemented here", color="info")

    def _quick_action(self, _screen_num: int, action_type: str) -> None:
        """Handle quick action buttons."""
        actions = {
            "explain_code": "Please paste the code you'd like me to explain.",
            "debug": "Describe the issue you're experiencing and I'll help you debug it.",
            "network": "What network problem are you facing? I can help with connectivity, configuration, or diagnostics.",
            "script": "What kind of script would you like me to generate? Please describe the requirements.",
        }

        prompt = actions.get(action_type, "How can I help you?")
        if self.message_input:
            self.message_input.value = prompt
        ui.notify(f"Quick action: {action_type.replace('_', ' ').title()}", color="info")
