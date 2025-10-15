from datetime import datetime
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
        self.scroll_area: ui.scroll_area | None = None
        self._buttons: dict[str, ui.button] = {}

        # Response templates for better performance
        self._response_templates = {
            "hello": "Hello! I'm here to help you with network diagnostics, system administration, and technical questions.",
            "help": "I can assist you with:\n• Network troubleshooting\n• System diagnostics\n• Code explanation\n• Script generation\n• SSH and remote management",
            "network": "For network issues, I can help you analyze interface configurations, troubleshoot connectivity, and interpret diagnostic outputs.",
        }

        # Quick action templates
        self._quick_actions = {
            "explain_code": "Please paste the code you'd like me to explain.",
            "debug": "Describe the issue you're experiencing and I'll help you debug it.",
            "network": "What network problem are you facing? I can help with connectivity, configuration, or diagnostics.",
            "script": "What kind of script would you like me to generate? Please describe the requirements.",
        }

    def build(self, screen_num: int) -> None:
        """Build ChatGPT-like interface for the screen."""
        with ui.column().classes("w-full h-full gap-4"):
            # Model selector and controls
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                ui.select(
                    ["GPT-4", "GPT-3.5", "Claude", "Local AI"],
                    value=self._current_model,
                    on_change=self._update_model,
                ).classes("w-32")
                self._buttons["clear"] = ui.button("Clear Chat", icon="clear_all", on_click=self._clear_chat).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800"
                )
                self._buttons["export"] = ui.button("Export Chat", icon="download", on_click=self._export_chat).classes(
                    "bg-blue-300 hover:bg-blue-400 text-blue-900"
                )
                self._buttons["context"] = ui.button(
                    "System Context", icon="settings", on_click=self._add_system_context
                ).classes("bg-green-300 hover:bg-green-400 text-green-900")

            # Chat messages area
            self.scroll_area = ui.scroll_area().classes("w-full h-96 border border-gray-300 rounded p-4 bg-gray-50")
            with self.scroll_area:
                self.chat_container = ui.column().classes("w-full gap-2")
                self._restore_chat_history()

            # Input area
            with ui.row().classes("w-full gap-2"):
                self.message_input = (
                    ui.textarea(placeholder="Type your message here... (Ctrl+Enter to send)", value="")
                    .classes("flex-1")
                    .props("outlined autogrow")
                    .on("keydown.ctrl.enter", self._send_message)
                )

                self._buttons["send"] = (
                    ui.button("Send", icon="send", on_click=self._send_message)
                    .classes("bg-blue-500 hover:bg-blue-600 text-white self-stretch")
                    .tooltip("Send message (Ctrl+Enter)")
                )

            # Quick actions
            with (
                ui.expansion("Quick Actions", icon="flash_on").classes("w-full mt-4"),
                ui.row().classes("w-full gap-2 flex-wrap"),
            ):
                self._buttons["explain"] = ui.button(
                    "Explain Code", on_click=lambda: self._quick_action("explain_code")
                ).classes("bg-orange-300 hover:bg-orange-400 text-orange-900")
                self._buttons["debug"] = ui.button("Debug Issue", on_click=lambda: self._quick_action("debug")).classes(
                    "bg-red-300 hover:bg-red-400 text-red-900"
                )
                self._buttons["network_help"] = ui.button(
                    "Network Help", on_click=lambda: self._quick_action("network")
                ).classes("bg-teal-300 hover:bg-teal-400 text-teal-900")
                self._buttons["script"] = ui.button(
                    "Generate Script", on_click=lambda: self._quick_action("script")
                ).classes("bg-green-300 hover:bg-green-400 text-green-900")

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
                ui.row().classes("w-full justify-end mb-2 mr-8"),
                ui.card()
                .classes("max-w-md bg-blue-500 text-white p-3 rounded-lg")
                .style("word-break: break-word; overflow-wrap: break-word;")
                .tooltip(timestamp),
            ):
                ui.label(content).classes("text-sm whitespace-pre-wrap")
        else:
            with (
                ui.row().classes("w-full justify-start mb-2"),
                ui.card().classes("max-w-md bg-white border p-3 rounded-lg").tooltip(timestamp),
            ):
                ui.label(content).classes("text-sm")

    def _update_model(self, e: Any) -> None:
        """Update current model selection."""
        self._current_model = e.value

    def _send_message(self) -> None:
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

        timestamp = datetime.now().strftime("%H:%M")  # noqa: DTZ005
        message = {"role": role, "content": content, "timestamp": timestamp}
        self._chat_history.append(message)

        with self.chat_container:
            self._render_message(role, content, timestamp)

        # Auto-scroll to bottom
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        """Scroll chat to bottom."""
        if self.scroll_area:
            ui.timer(0.1, lambda: self.scroll_area.scroll_to(percent=1), once=True)

    def _simulate_ai_response(self, user_message: str) -> None:
        """Simulate AI response (replace with actual AI API)."""
        # Simple keyword matching using cached templates
        response = f"I understand you're asking about: '{user_message[:50]}...'\n\nI'm a simulated AI assistant. In a real implementation, I would connect to an AI service like OpenAI's API to provide intelligent responses."

        for key, value in self._response_templates.items():
            if key in user_message.lower():
                response = value
                break

        # Add AI response after a short delay
        ui.timer(1.0, lambda: self._add_message("assistant", response), once=True)

    def _clear_chat(self) -> None:
        """Clear chat history."""
        if not self.chat_container:
            return

        self._chat_history.clear()
        self.chat_container.clear()
        with self.chat_container:
            ui.label("👋 Chat cleared. How can I help you?").classes("text-gray-600 italic")
        ui.notify("Chat cleared", color="info")

    def _export_chat(self) -> None:
        """Export chat history."""
        if not self._chat_history:
            ui.notify("No chat history to export", color="warning")
            return

        chat_data = {
            "model": self._current_model,
            "timestamp": datetime.now().isoformat(),  # noqa: DTZ005
            "messages": self._chat_history,
        }

        Json.export_download(chat_data, "ai_chat", success_message="Chat history exported successfully")

    def _add_system_context(self) -> None:
        """Add system context to chat."""
        connections = 0
        if self._host_handler and hasattr(self._host_handler, "_connect_route"):
            connections = len(getattr(self._host_handler, "_connect_route", []))
        context = f"System Context:\n\n• Current host connections: {connections}\n\n• Model: {self._current_model}\n\n• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"  # noqa: DTZ005
        self._add_message("system", context)

    def _quick_action(self, action_type: str) -> None:
        """Handle quick action buttons."""
        prompt = self._quick_actions.get(action_type, "How can I help you?")
        if self.message_input:
            self.message_input.value = prompt
        ui.notify(f"Quick action: {action_type.replace('_', ' ').title()}", color="info")
