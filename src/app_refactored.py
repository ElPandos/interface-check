"""Refactored application with dependency injection and improved architecture."""

import logging
from pathlib import Path

from dotenv import load_dotenv
from nicegui import ui

from src.core.container import get_container
from src.core.event_bus import EventBus
from src.core.lifecycle import LifecycleManager
from src.implementations.json_config import JsonConfigurationFactory
from src.implementations.network_tools import NetworkToolFactory
from src.implementations.ssh_connection import SshConnectionFactory
from src.interfaces.configuration import IConfigurationFactory, IConfigurationProvider
from src.interfaces.connection import IConnection, IConnectionFactory
from src.interfaces.tool import IToolFactory
from src.interfaces.ui import IEventBus
from src.models.configurations import AppConfig
from src.ui.base.components import Tab
from src.ui.panels.ethtool_panel import EthtoolPanel

logger = logging.getLogger(__name__)


class RefactoredApp:
    """Refactored application with dependency injection."""

    def __init__(self):
        self._lifecycle_manager = LifecycleManager()
        self._container = get_container()
        self._setup_dependencies()

    def _setup_dependencies(self) -> None:
        """Setup dependency injection container."""
        load_dotenv()
        self._setup_configuration()
        self._setup_event_bus()
        self._setup_connection()

    def _setup_configuration(self) -> None:
        """Setup configuration dependencies."""
        config_factory = JsonConfigurationFactory()
        config_path = Path.home() / ".interface-check" / "ssh_config.json"
        config_provider = config_factory.create_provider(str(config_path))

        self._container.register_instance(IConfigurationFactory, config_factory)
        self._container.register_instance(IConfigurationProvider, config_provider)

    def _setup_event_bus(self) -> None:
        """Setup event bus."""
        event_bus = EventBus()
        self._container.register_instance(IEventBus, event_bus)

    def _setup_connection(self) -> None:
        """Setup connection and tools."""
        connection_factory = SshConnectionFactory()
        self._container.register_instance(IConnectionFactory, connection_factory)

        app_config = self._load_app_config()
        if app_config and app_config.hosts:
            self._create_connection(connection_factory, app_config.hosts[0])

    def _load_app_config(self) -> AppConfig | None:
        """Load application configuration."""
        try:
            config_provider = self._container.get(IConfigurationProvider)
            app_config_data = config_provider.get("", {})

            if not app_config_data:
                app_config = AppConfig()
                config_provider.set("", app_config.model_dump())
                config_provider.save()
                return app_config

            return AppConfig.model_validate(app_config_data)
        except Exception:
            logger.exception("Failed to load app config")
            return None

    def _create_connection(self, factory: SshConnectionFactory, host) -> None:
        """Create SSH connection and tools."""
        try:
            connection = factory.create_connection(host)
            self._container.register_instance(IConnection, connection)
            self._lifecycle_manager.register(connection)

            tool_factory = NetworkToolFactory(connection)
            self._container.register_instance(IToolFactory, tool_factory)
        except Exception:
            logger.exception("Failed to create connection")

    def run(self) -> None:
        """Run the application."""
        try:
            with self._lifecycle_manager.managed_lifecycle():
                self._build_ui()
                ui.run(favicon="./assets/icons/interoperability.png", reload=True)
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception:
            logger.exception("Application error")

    def _build_ui(self) -> None:
        """Build the user interface."""
        dependencies = self._get_ui_dependencies()
        self._build_header(dependencies)
        self._build_body(dependencies)
        self._add_custom_styles()

    def _get_ui_dependencies(self) -> dict:
        """Get UI dependencies from container."""
        return {
            "config": self._container.get(IConfigurationProvider),
            "connection": self._container.get(IConnection),
            "tool_factory": self._container.get(IToolFactory),
            "event_bus": self._container.get(IEventBus),
        }

    def _build_header(self, deps: dict) -> None:
        """Build header with tabs."""
        with ui.header().classes("row items-center justify-between"), ui.tabs() as tabs:
            ethtool_tab = Tab("ethtool", "Ethtool", "home_repair_service", deps["event_bus"])
            self._lifecycle_manager.register(ethtool_tab)
            self._tabs = tabs

    def _build_body(self, deps: dict) -> None:
        """Build body with panels."""
        with ui.tab_panels(self._tabs, value="ethtool").classes("w-full h-fit bg-gray-100"):
            ethtool_panel = EthtoolPanel(deps["config"], deps["connection"], deps["tool_factory"], deps["event_bus"])
            self._lifecycle_manager.register(ethtool_panel)

    def _add_custom_styles(self) -> None:
        """Add custom CSS styles."""
        ui.add_head_html("""
        <style>
        .q-tab {
            transition: all 0.3s ease;
            border-radius: 8px 8px 0 0;
            margin: 0 2px;
            background: rgba(255, 255, 255, 0.1);
        }

        .q-tab--active {
            background: rgba(255, 255, 255, 0.9) !important;
            color: #1976d2 !important;
            font-weight: 600;
            box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }

        .q-tab--active .q-icon {
            color: #1976d2 !important;
            transform: scale(1.1);
        }

        .q-tab:not(.q-tab--active):hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }
        </style>
        """)
