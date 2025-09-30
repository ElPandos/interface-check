from nicegui import ui


class IpTable:
    """Handles rendering and synchronization table settings."""

    def __init__(self) -> None:
        pass

    def build(self) -> None:
        columns = [{"name": "IP", "label": "ip", "field": "name"},
                   {"name": "date", "label": "Date", "field": "date"},
                   {"name": "date", "label": "Date", "field": "date"}
                   ]
        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left'},
            {'name': 'age', 'label': 'Age', 'field': 'age', 'sortable': True},
        ]
        rows = [
            {'name': 'Alice', 'age': 18},
            {'name': 'Bob', 'age': 21},
            {'name': 'Carol'},
        ]

        self.__table = ui.table(columns=columns, rows=[]).classes("h-52").props("virtual-scroll")
        ui.button("Add row", on_click=add)

    def add(self):
        self.__table.add_row({"date": datetime.now().strftime("%c")})
        self.__table.run_method("scrollTo", len(self.__table.rows) - 1)
