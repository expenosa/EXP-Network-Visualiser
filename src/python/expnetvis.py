__author__ = "Expenosa"
__copyright__ = "Copyright (C) 2023 Expenosa"
__license__ = "MIT License"
__version__ = "0.2"

import os
from typing import List, Dict
from argparse import ArgumentParser
from nicegui import app, ui
import nicegui.globals as niceglobals
from nicegui.events import KeyEventArguments
import expnetgraph


COLOURS = expnetgraph.COLOURS
SHAPES = expnetgraph.SHAPES

DEFAULT_FIELD_STYLE = 'width: 500px;'

save_file = None

netgraph = expnetgraph.NetworkGraph()
netgraph.add_node(expnetgraph.Node("First Node")) # A hack to force autocompletion to work. Never works if node_names is empty.

node_names = []
node_names.extend(netgraph.get_all_node_names())

history = expnetgraph.UndoHistory()


def clear_comp_values(*args):
    ''' Return nicegui components to default blank values '''
    for comp in args:
        comp.value = ""


def netgraph_modification(func):
    ''' Decorator function that catches exceptions, saves and redraws the network graph.
        NetGraphException messages are displayed to the user.
    '''
    def inner(*args, **kwargs):
        try:
            history.add_undo(netgraph)
            func(*args, **kwargs)
            history.clear_redos()
            save_netgraph()
            redraw_graph()
        except expnetgraph.NetGraphException as e:
            ui.notify(e.msg, type='negative')
            raise e
    return inner


def undo():
    other = history.undo(netgraph)
    if other:
        netgraph.set_nodes(other)
        save_netgraph()
        redraw_graph()


def redo():
    other = history.redo(netgraph)
    if other:
        netgraph.set_nodes(other)
        save_netgraph()
        redraw_graph()


def save_netgraph():
    global save_file
    if save_file:
        expnetgraph.save_network_graph(save_file, netgraph)


def load_netgraph():
    global netgraph
    global save_file
    if save_file:
        netgraph = expnetgraph.load_network_graph(save_file)
    else:
        netgraph = expnetgraph.NetworkGraph()
    redraw_graph()


def update_elements():
    ''' Update UI elements so they reflect current changes such as autocomplete values '''
    node_names.clear()
    node_names.extend(netgraph.get_all_node_names())
    ui.update()


def redraw_graph():
    ''' Rerender and graph HTML and force the client to refresh the page '''
    niceglobals.get_client().body_html = "" # Remove existing HTML
    html = expnetgraph.generate(netgraph)
    ui.add_body_html(html)
    update_elements()
    ui.open('/')


@netgraph_modification
def add_node(name, colour, shape, linked_from: str="", link_msg: str=""):
    print(f"Adding new node: '{name}' with colour {colour} and shape {shape}")
    # Check link from node exists
    if linked_from and not netgraph.contains_node(linked_from):
        raise expnetgraph.NetGraphException(f"Linked from node does not exist: {linked_from}")

    netgraph.add_node(expnetgraph.Node(name, colour=colour, shape=shape))
    if linked_from:
        netgraph.add_link(linked_from, name, link_msg)


@netgraph_modification
def rename_node(old_name, new_name):
    print(f"Renaming node '{old_name}' to '{new_name}")
    netgraph.rename_node(old_name, new_name)


@netgraph_modification
def edit_node(name, colour, shape, notes):
    print(f"Editing node: '{name}' to colour {colour} and shape {shape} with notes: {notes}")
    node = netgraph.get_node(name)
    node.colour = colour
    node.shape = shape
    node.notes = notes


@netgraph_modification
def create_link(nodeA: str, nodeB: str, msg: str=""):
    print(f"Connecting '{nodeA}' to '{nodeB}' with message: '{msg}'")
    netgraph.add_link(nodeA, nodeB, msg)


@netgraph_modification
def edit_link(nodeA: str, nodeB: str, msg: str):
    print(f"Editing link bettwen '{nodeA}' and '{nodeB}' with message: '{msg}'")
    netgraph.edit_link(nodeA, nodeB, msg)


@netgraph_modification
def remove_node(name: str):
    print(f"Deleting node '{name}'")
    netgraph.delete_node(name)


@netgraph_modification
def remove_link(nodeA: str, nodeB: str):
    print(f"Deleting link between {nodeA} and {nodeB}")
    netgraph.remove_link(nodeA, nodeB)


def create_input(*args, **kwargs):
    return ui.input(*args, **kwargs).style(DEFAULT_FIELD_STYLE)

def create_dropdown(*args, **kwargs):
    return ui.select(*args, **kwargs).style(DEFAULT_FIELD_STYLE)

def create_textarea(*args, **kwargs):
    return ui.textarea(*args, **kwargs).style(DEFAULT_FIELD_STYLE)


# Javascript integrated functions

async def get_selected_node() -> str:
    ''' Returns the name of the selected node in the gui, otherwise empty string '''
    selected = await ui.run_javascript('network.getSelectedNodes()', timeout=3)
    if selected:
        return selected[0]
    return ""


async def get_selected_link() -> List[str]:
    ''' Returns an array containing names of the nodes connected to the selected link, otherwise empty array '''
    selected = await ui.run_javascript('''
        var selectedEdges = network.getSelectedEdges();
        if (selectedEdges && selectedEdges.length == 1) {
            var selectedEdge = selectedEdges[0];
            network.getConnectedNodes(selectedEdge);
        } else {
            Array();
        }
        ''', timeout=3)

    if selected and len(selected) == 2:
        return selected
    return ["", ""]


async def clear_selection():
    ''' Perform the same operation as the Reset Selection button in pyvis '''
    await ui.run_javascript('neighbourhoodHighlight({ nodes: [] });', respond=False)


async def get_node_positions() -> Dict:
    ''' NOT USED. Fetch a map of x, y coordinates for every node '''
    node_names = [ f'"{x}"' for x in netgraph.get_all_node_names() ]
    positions = await ui.run_javascript('network.getPositions(Array(' + ','.join(node_names) + '))', timeout=10)
    print(positions)



def create_buttons_row():
    with ui.footer():
        # Create Node Button
        with ui.dialog() as new_node_dialog, ui.card():
            ui.markdown("New Node")
            node_name_field = create_input(label="Node name")

            ui.label("Colour")
            create_node_colour_select = create_dropdown(COLOURS, value=COLOURS[0])

            ui.label("Shape")
            create_node_shape_select = create_dropdown(SHAPES, value=SHAPES[0])
            link_from_field = create_input(label="Linked from (optional)", autocomplete=node_names)
            link_msg_field = create_input(label="Link Message (optional)")

            with ui.row():
                def create_node_clicked():
                    if not node_name_field.value:
                        return
                    new_node_dialog.close()
                    add_node(node_name_field.value, create_node_colour_select.value, create_node_shape_select.value, 
                             linked_from=link_from_field.value, link_msg=link_msg_field.value)
                    clear_comp_values(node_name_field, link_from_field, link_msg_field)
                ui.button('Create', on_click=create_node_clicked)
                ui.button('Close', on_click=new_node_dialog.close)

        async def show_new_node_dialog():
            link_from_field.value = await get_selected_node()
            new_node_dialog.open()
        ui.button('Create Node', on_click=show_new_node_dialog)
        

        # Rename Node Button
        with ui.dialog() as rename_node_dialog, ui.card():
            ui.markdown("Rename Node")
            old_name_input = create_input(label="Current Name", autocomplete=node_names)
            new_name_input = create_input(label="New Name")

            with ui.row():
                def rename_node_clicked():
                    if not old_name_input.value or not new_name_input.value:
                        return
                    rename_node_dialog.close()
                    rename_node(old_name_input.value, new_name_input.value)
                    clear_comp_values(old_name_input, new_name_input)
                ui.button('Rename', on_click=rename_node_clicked)
                ui.button('Close', on_click=rename_node_dialog.close)

        async def show_rename_node_dialog():
            old_name_input.value = await get_selected_node()
            rename_node_dialog.open()
        ui.button('Rename Node', on_click=show_rename_node_dialog)


        # Edit Node Button
        with ui.dialog() as edit_node_dialog, ui.card():
            ui.markdown("Edit Node")
            #node_select = create_dropdown(node_names, with_input=True)
            edit_node_select = create_input(label="Node Name", autocomplete=node_names)

            with ui.column() as column:
                ui.label("Colour")
                edit_node_colour_select = create_dropdown(COLOURS, value=COLOURS[0])

                ui.label("Shape")
                edit_node_shape_select = create_dropdown(SHAPES, value=SHAPES[0])
                edit_node_notes_ta = create_textarea("Notes")

                def column_visible(value) -> bool:
                    ''' Function to reflect existing values for selected node '''
                    exists = value and value in node_names
                    if exists:
                        node = netgraph.get_node(value)
                        edit_node_colour_select.value = node.colour
                        edit_node_shape_select.value = node.shape
                        edit_node_notes_ta.value = node.notes
                    return exists

                column.bind_visibility_from(edit_node_select, 'value', column_visible)

            with ui.row():
                def edit_node_clicked():
                    edit_node_dialog.close()
                    edit_node(edit_node_select.value, edit_node_colour_select.value, 
                              edit_node_shape_select.value, edit_node_notes_ta.value)
                    clear_comp_values(edit_node_select)
                apply_btn = ui.button('Apply', on_click=edit_node_clicked)
                apply_btn.bind_visibility_from(column)
                ui.button('Close', on_click=edit_node_dialog.close)

        async def show_edit_node_dialog():
            edit_node_select.value = await get_selected_node()
            edit_node_dialog.open()
        ui.button('Edit Node', on_click=show_edit_node_dialog)


        # Delete Node Button
        with ui.dialog() as delete_node_dialog, ui.card():
            ui.markdown("Delete Node")
            #node_select = create_dropdown(node_names, with_input=True)
            delete_node_select = create_input(label="Node Name", autocomplete=node_names)

            with ui.row():
                def delete_node_clicked():
                    if not delete_node_select.value:
                        return
                    delete_node_dialog.close()
                    remove_node(delete_node_select.value)
                    clear_comp_values(delete_node_select)
                ui.button('Delete', on_click=delete_node_clicked)
                ui.button('Close', on_click=delete_node_dialog.close)

        async def show_delete_node_dialog():
            delete_node_select.value = await get_selected_node()
            delete_node_dialog.open()
        ui.button('Delete Node', on_click=show_delete_node_dialog)


        ## Add spacer
        ui.label("| |")


        # Create Link Button 
        with ui.dialog() as new_link_dialog, ui.card():
            ui.markdown("New Link")
            # nodeA_select = create_dropdown(node_names, with_input=True)
            nodeA_select = create_input(label="From Node", autocomplete=node_names)
            # nodeB_select = create_dropdown(node_names, with_input=True)
            nodeB_select = create_input(label="To Node", autocomplete=node_names)
            msg_text = create_textarea('Link Message')
            

            with ui.row():
                def create_link_clicked():
                    if not nodeA_select.value or not nodeB_select.value:
                        return
                    new_link_dialog.close()
                    create_link(nodeA_select.value, nodeB_select.value, msg_text.value)
                    clear_comp_values(nodeA_select, nodeB_select, msg_text)
                ui.button('Create', on_click=create_link_clicked)
                ui.button('Close', on_click=new_link_dialog.close)
        
        async def show_new_link_dialog():
            nodeA_select.value = await get_selected_node()
            new_link_dialog.open()
        ui.button('Add Link', on_click=show_new_link_dialog)


        # Edit Link Button
        with ui.dialog() as edit_link_dialog, ui.card():
            ui.markdown("Edit Link")
            edit_nodeA_input = create_input(label="From Node", autocomplete=node_names)
            edit_nodeB_input = create_input(label="To Node", autocomplete=node_names)
            edit_msg_text = create_textarea('Link Message')
            
            def edit_msg_visibility(value) -> bool:
                ''' Function to load the existing values for the selected link '''
                a_exists = edit_nodeA_input.value in node_names
                b_exists = edit_nodeB_input.value in node_names
                if a_exists and b_exists:
                    try:
                        link = netgraph.get_link(edit_nodeA_input.value, edit_nodeB_input.value)
                        edit_msg_text.value = link.msg
                        return True
                    except expnetgraph.NetGraphException:
                        pass # Ignore and return false
                return False

            edit_msg_text.bind_visibility_from(edit_nodeB_input, 'value', edit_msg_visibility)

            with(ui.row()):
                def edit_link_clicked():
                    if not edit_nodeA_input.value or not edit_nodeB_input.value:
                        return
                    edit_link_dialog.close()
                    edit_link(edit_nodeA_input.value, edit_nodeB_input.value, edit_msg_text.value)
                    clear_comp_values(edit_nodeA_input, edit_nodeB_input, edit_msg_text)
                ui.button('Apply', on_click=edit_link_clicked).bind_visibility_from(edit_msg_text)
                ui.button('Close', on_click=edit_link_dialog.close)

        async def show_edit_link_dialog():
            nodes = await get_selected_link()
            if nodes:
                edit_nodeA_input.value = nodes[0]
                edit_nodeB_input.value = nodes[1]
            edit_link_dialog.open()
        ui.button('Edit Link', on_click=show_edit_link_dialog)



        # Remove Link Button
        with ui.dialog() as remove_link_dialog, ui.card():
            ui.markdown("Remove Link")
            remove_nodeA_select = create_input(label="First Node", autocomplete=node_names)
            remove_nodeB_select = create_input(label="Second Node", autocomplete=node_names)

            with ui.row():
                def remove_link_clicked():
                    if not remove_nodeA_select.value or not remove_nodeB_select.value:
                        return
                    remove_link_dialog.close()
                    remove_link(remove_nodeA_select.value, remove_nodeB_select.value)
                    clear_comp_values(remove_nodeA_select, remove_nodeB_select)
                ui.button('Remove', on_click=remove_link_clicked)
                ui.button('Close', on_click=remove_link_dialog.close)
        
        async def show_remove_link_dialog():
            nodes = await get_selected_link()
            if nodes:
                remove_nodeA_select.value = nodes[0]
                remove_nodeB_select.value = nodes[1]
            remove_link_dialog.open()
        ui.button('Remove Link', on_click=show_remove_link_dialog)


        ## Add spacer
        ui.label("| |")

        ui.button('Reset Selection', on_click=clear_selection)

#         ## Add spacer
#         ui.label("| |")

#         ui.button(icon='menu', on_click=lambda: ui.open('/settings_page')).style('position: absolute; right: 30px;')



# @ui.page('/settings_page')
# def settings_page():
#     ui.markdown("# Settings")

#     ui.button('Back', on_click=lambda: ui.open('/'))



def init_keybinds():
    ''' Add keybinds such as refresh on F5 '''
    async def handle_key(e: KeyEventArguments):
        if not e.action.keyup and not e.action.repeat:
            return
        
        # print(e.key)
        if e.key == 'F5':
            ui.open('/')
        elif e.key == 'Escape':
            await clear_selection()
        elif e.modifiers.ctrl and e.key == 'z': # TODO undo function
            undo()
        elif e.modifiers.ctrl and e.key == 'y': # TODO redo function
            redo()

    ui.keyboard(on_key=handle_key)



def load_from_file(abspath):
    ''' Load data from file and render the netgraph '''
    global save_file
    save_file = os.path.abspath(abspath)
    print(f"Loading from file: {save_file}")
    if os.path.exists(save_file):
        load_netgraph()
    else:
        redraw_graph()
    


def file_selection_dialog():
    ''' Show the 'Create New'/'Open Existing' dialog and load the graph using that chosen file selection '''
    with ui.dialog() as dialog, ui.card():
        ui.markdown("Choose working file...")

        async def choose_file(open: bool):
            import webview
            mode = webview.OPEN_DIALOG if open else webview.SAVE_DIALOG
            file_types = ('PJson Files (*.pjson)', 'All files (*.*)')
            pwd = os.path.abspath('.')
            working_file = await app.native.main_window.create_file_dialog(mode, directory=pwd, allow_multiple=False, file_types=file_types, save_filename='untitled.pjson')

            if working_file:
                if isinstance(working_file, tuple):
                    working_file = working_file[0]
                ui.notify(f"Using File: {working_file}")
                load_from_file(working_file)
                dialog.close()
                
        async def open_file():
            await choose_file(True)
        async def new_file():
            await choose_file(False)

        ui.button('Open Existing', on_click=open_file)
        ui.button('Create New', on_click=new_file)
    
    dialog.props('persistent') # So this dialog cannot be dismissed normally
    dialog.open()



def main():
    parser = ArgumentParser(f"Expenosa's Network Visualiser {__version__}")
    parser.add_argument('-f', '--file', type=str, default=None, help="Network json file location. Created if does not exist.")
    parser.add_argument('--web', default=False, action='store_true', help="Use web browser instead of native app window.")
    args = parser.parse_args()
    global save_file
    save_file = args.file
    native = not args.web

    ## Allow javscript resources for pyvis to be served
    app.add_static_files('/lib', 'lib')

    create_buttons_row()
    init_keybinds()

    # load graph from file if it exists, otherwise show dialog
    if save_file:
        load_from_file(save_file)
    else:
        file_selection_dialog()

    # Only reload on src changes in dev environment
    reload = os.path.isdir('env')
    window = (1280,800) if native else None
    ui.run(reload=reload, title="EXP Network Visualiser", dark=True, window_size=window, favicon="lib/favicon.ico")


if __name__ in {"__main__", "__mp_main__"}:
    import multiprocessing
    multiprocessing.freeze_support() ## Required for PyInstaller
    main()