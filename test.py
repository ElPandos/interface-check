# #!/usr/bin/env python3
# import time
# from multiprocessing import Manager, Queue

# from nicegui import run, ui


# def heavy_computation(q: Queue) -> str:
#
#     n = 50
#     for i in range(n):
#         # Perform some heavy computation
#         time.sleep(0.1)

#         # Update the progress bar through the queue
#         q.put_nowait(i / n)
#     return 'Done!'


# @ui.page('/')
# def main_page():
#     async def start_computation():
#         progressbar.visible = True
#         result = await run.cpu_bound(heavy_computation, queue)
#         ui.notify(result)
#         progressbar.visible = False

#     # Create a queue to communicate with the heavy computation process
#     queue = Manager().Queue()
#     # Update the progress bar on the main process
#     ui.timer(0.1, callback=lambda: progressbar.set_value(queue.get() if not queue.empty() else progressbar.value))

#     # Create the UI
#     ui.button('compute', on_click=start_computation)
#     progressbar = ui.linear_progress(value=0).props('instant-feedback')
#     progressbar.visible = False


# ui.run()

# #!/usr/bin/env python3
# import platform
# from pathlib import Path
# from typing import Optional

# from nicegui import events, ui


# async def pick_file() -> None:
#     result = await local_file_picker('~', multiple=True)
#     ui.notify(f'You chose {result}')


# @ui.page('/')
# def index():
#     ui.button('Choose file', on_click=pick_file, icon='folder')


# ui.run()

# class local_file_picker(ui.dialog):

#     def __init__(self, directory: str, *,
#                  upper_limit: Optional[str] = ..., multiple: bool = False, show_hidden_files: bool = False) -> None:
#         #         super().__init__()

#         self.path = Path(directory).expanduser()
#         if upper_limit is None:
#             self.upper_limit = None
#         else:
#             self.upper_limit = Path(directory if upper_limit == ... else upper_limit).expanduser()
#         self.show_hidden_files = show_hidden_files

#         with self, ui.card():
#             self.add_drives_toggle()
#             self.grid = ui.aggrid({
#                 'columnDefs': [{'field': 'name', 'headerName': 'File'}],
#                 'rowSelection': 'multiple' if multiple else 'single',
#             }, html_columns=[0]).classes('w-96').on('cellDoubleClicked', self.handle_double_click)
#             with ui.row().classes('w-full justify-end'):
#                 ui.button('Cancel', on_click=self.close).props('outline')
#                 ui.button('Ok', on_click=self._handle_ok)
#         self.update_grid()

#     def add_drives_toggle(self):
#         if platform.system() == 'Windows':
#             import win32api
#             drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
#             self.drives_toggle = ui.toggle(drives, value=drives[0], on_change=self.update_drive)

#     def update_drive(self):
#         self.path = Path(self.drives_toggle.value).expanduser()
#         self.update_grid()

#     def update_grid(self) -> None:
#         paths = list(self.path.glob('*'))
#         if not self.show_hidden_files:
#             paths = [p for p in paths if not p.name.startswith('.')]
#         paths.sort(key=lambda p: p.name.lower())
#         paths.sort(key=lambda p: not p.is_dir())

#         self.grid.options['rowData'] = [
#             {
#                 'name': f'📁 <strong>{p.name}</strong>' if p.is_dir() else p.name,
#                 'path': str(p),
#             }
#             for p in paths
#         ]
#         if (self.upper_limit is None and self.path != self.path.parent) or \
#                 (self.upper_limit is not None and self.path != self.upper_limit):
#             self.grid.options['rowData'].insert(0, {
#                 'name': '📁 <strong>..</strong>',
#                 'path': str(self.path.parent),
#             })
#         self.grid.update()

#     def handle_double_click(self, e: events.GenericEventArguments) -> None:
#         self.path = Path(e.args['data']['path'])
#         if self.path.is_dir():
#             self.update_grid()
#         else:
#             self.submit([str(self.path)])

#     async def _handle_ok(self):
#         rows = await self.grid.get_selected_rows()
#         self.submit([r['path'] for r in rows])

# #!/usr/bin/env python3
# from nicegui import ui

# tree = ui.tree([
#     {'id': 'numbers', 'icon': 'tag', 'children': [{'id': '1'}, {'id': '2'}]},
#     {'id': 'letters', 'icon': 'text_fields', 'children': [{'id': 'A'}, {'id': 'B'}]},
# ], label_key='id', on_select=lambda e: ui.notify(e.value))

# tree.add_slot('default-header', r
#     def __init__(self) -> None:
#         with ui.dialog().props('maximized').classes('bg-black') as self.dialog:
#             ui.keyboard(self._handle_key)
#             self.large_image = ui.image().props('no-spinner fit=scale-down')
#         self.image_list: List[str] = []

#     def add_image(self, thumb_url: str, orig_url: str) -> ui.image:
#
#         self.image_list.append(orig_url)
#         with ui.button(on_click=lambda: self._open(orig_url)).props('flat dense square'):
#             return ui.image(thumb_url)

#     def _handle_key(self, event_args: events.KeyEventArguments) -> None:
#         if not event_args.action.keydown:
#             return
#         if event_args.key.escape:
#             self.dialog.close()
#         image_index = self.image_list.index(self.large_image.source)
#         if event_args.key.arrow_left and image_index > 0:
#             self._open(self.image_list[image_index - 1])
#         if event_args.key.arrow_right and image_index < len(self.image_list) - 1:
#             self._open(self.image_list[image_index + 1])

#     def _open(self, url: str) -> None:
#         self.large_image.set_source(url)
#         self.dialog.open()


# @ui.page('/')
# async def page():
#     lightbox = Lightbox()
#     async with httpx.AsyncClient() as client:  # using async httpx instead of sync requests to avoid blocking the event loop
#         images = await client.get('https://picsum.photos/v2/list?page=4&limit=30')
#     with ui.row().classes('w-full'):
#         for image in images.json():  # picsum returns a list of images as json data
#             # we can use the image ID to construct the image URLs
#             image_base_url = f'https://picsum.photos/id/{image["id"]}'
#             # the lightbox allows us to add images which can be opened in a full screen dialog
#             lightbox.add_image(
#                 thumb_url=f'{image_base_url}/300/200',
#                 orig_url=f'{image_base_url}/{image["width"]}/{image["height"]}',
#             ).classes('w-[300px] h-[200px]')

# ui.run()

# #!/usr/bin/env python3
# from nicegui import events, ui

# columns = [
#     {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left'},
#     {'name': 'age', 'label': 'Age', 'field': 'age'},
# ]
# rows = [
#     {'id': 0, 'name': 'Alice', 'age': 18},
#     {'id': 1, 'name': 'Bob', 'age': 21},
#     {'id': 2, 'name': 'Carol', 'age': 20},
# ]


# def add_row() -> None:
#     new_id = max((dx['id'] for dx in rows), default=-1) + 1
#     rows.append({'id': new_id, 'name': 'New guy', 'age': 21})
#     ui.notify(f'Added new row with ID {new_id}')
#     table.update()


# def rename(e: events.GenericEventArguments) -> None:
#     for row in rows:
#         if row['id'] == e.args['id']:
#             row.update(e.args)
#     ui.notify(f'Updated rows to: {table.rows}')
#     table.update()


# def delete(e: events.GenericEventArguments) -> None:
#     rows[:] = [row for row in rows if row['id'] != e.args['id']]
#     ui.notify(f'Deleted row with ID {e.args["id"]}')
#     table.update()


# table = ui.table(columns=columns, rows=rows, row_key='name').classes('w-60')
# table.add_slot('header', r#     <q-tr :props="props">
#         <q-td auto-width >
#             <q-btn size="sm" color="warning" round dense icon="delete"
#                 @click="() => $parent.$emit('delete', props.row)"
#             />
#         </q-td>
#         <q-td key="name" :props="props">
#             {{ props.row.name }}
#             <q-popup-edit v-model="props.row.name" v-slot="scope"
#                 @update:model-value="() => $parent.$emit('rename', props.row)"
#             >
#                 <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" />
#             </q-popup-edit>
#         </q-td>
#         <q-td key="age" :props="props">
#             {{ props.row.age }}
#             <q-popup-edit v-model="props.row.age" v-slot="scope"
#                 @update:model-value="() => $parent.$emit('rename', props.row)"
#             >
#                 <q-input v-model.number="scope.value" type="number" dense autofocus counter @keyup.enter="scope.set" />
#             </q-popup-edit>
#         </q-td>
#     </q-tr>
# ''')
# with table.add_slot('bottom-row'):
#     with table.cell().props('colspan=3'):
#         ui.button('Add row', icon='add', color='accent', on_click=add_row).classes('w-full')
# table.on('rename', rename)
# table.on('delete', delete)

# ui.run()
