from nicegui import ui
import asyncio

# Simulated host connection state
host_connected = False


async def toggle_connection():
    global host_connected
    host_connected = not host_connected
    # Update tab state
    settings_tab.classes(remove="disabled" if host_connected else "disabled")
    connect_button.label = "Disconnect" if host_connected else "Connect"
    ui.notify(f"Host connection: {'Connected' if host_connected else 'Disconnected'}")


# UI setup
ui.label("Host Connection Example").classes("text-2xl mb-4")

# Tab panel
with ui.tabs() as tabs:
    home_tab = ui.tab("Home")
    settings_tab = ui.tab("Settings").classes("disabled")

# Tab content
with ui.tab_panels(tabs, value=home_tab):
    with ui.tab_panel(home_tab):
        ui.label("Welcome to the Home tab!")
    with ui.tab_panel(settings_tab):
        ui.label("Settings tab (only accessible when host is connected)")

# Button to toggle connection state
connect_button = ui.button("Connect", on_click=toggle_connection)

# Run the app
ui.run()
