import os
from argparse import ArgumentParser
from nicegui import app, ui
import nicegui.globals as niceglobals
import network

VERSION=0.1

COLOURS = network.COLOURS
SHAPES = network.SHAPES

DEFAULT_FIELD_STYLE = 'width: 500px;'

save_file = None

netgraph = network.NetworkGraph()

node_names = ['']
node_names.extend(netgraph.get_all_node_names())


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
            func(*args, **kwargs)
            save_netgraph()
            redraw_graph()
        except network.NetGraphException as e:
            ui.notify(e.msg, type='negative')
            raise e
    return inner


def save_netgraph():
    global save_file
    if save_file:
        network.save_network_graph(save_file, netgraph)


def load_netgraph():
    global netgraph
    global save_file
    if save_file:
        netgraph = network.load_network_graph(save_file)
    else:
        netgraph = network.NetworkGraph()
    redraw_graph()


def update_elements():
    node_names.clear()
    node_names.extend(netgraph.get_all_node_names())
    ui.update()


def redraw_graph():
    niceglobals.get_client().body_html = "" # Remove existing HTML
    html = network.generate(netgraph)
    ui.add_body_html(html)
    update_elements()
    ui.open('/')


@netgraph_modification
def add_node(name, colour, shape):
    print(f"Adding new node: '{name}' with colour {colour} and shape {shape}")
    netgraph.add_node(network.Node(name, colour=colour, shape=shape))


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



def create_buttons_row():
    with ui.footer():
        # Create Node Button
        with ui.dialog() as new_node_dialog, ui.card():
            ui.markdown("New Node")
            node_name_field = ui.input(label="Node name").style(DEFAULT_FIELD_STYLE)

            ui.label("Colour")
            create_node_colour_select = ui.select(COLOURS, value=COLOURS[0]).style(DEFAULT_FIELD_STYLE)

            ui.label("Shape")
            create_node_shape_select = ui.select(SHAPES, value=SHAPES[0]).style(DEFAULT_FIELD_STYLE)
            link_from_field = ui.input(label="Linked from (optional)", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)
            link_msg_field = ui.input(label="Link Message (optional)").style(DEFAULT_FIELD_STYLE)

            with ui.row():
                def create_node_clicked():
                    if not node_name_field.value:
                        return
                    new_node_dialog.close()
                    add_node(node_name_field.value, create_node_colour_select.value, create_node_shape_select.value)
                    if (link_from_field.value):
                        create_link(node_name_field.value, link_from_field.value, link_msg_field.value)
                    clear_comp_values(node_name_field, link_from_field, link_msg_field)
                ui.button('Create', on_click=create_node_clicked)
                ui.button('Close', on_click=new_node_dialog.close)

        ui.button('Create Node', on_click=new_node_dialog.open)
        
        # Rename Node Button
        with ui.dialog() as rename_node_dialog, ui.card():
            ui.markdown("Rename Node")
            old_name_input = ui.input(label="Current Name", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)
            new_name_input = ui.input(label="New Name").style(DEFAULT_FIELD_STYLE)

            with ui.row():
                def rename_node_clicked():
                    if not old_name_input.value or not new_name_input.value:
                        return
                    rename_node_dialog.close()
                    rename_node(old_name_input.value, new_name_input.value)
                    clear_comp_values(old_name_input, new_name_input)
                ui.button('Rename', on_click=rename_node_clicked)
                ui.button('Close', on_click=rename_node_dialog.close)

        ui.button('Rename Node', on_click=rename_node_dialog.open)


        # Edit Node Button
        with ui.dialog() as edit_node_dialog, ui.card():
            ui.markdown("Edit Node")
            #node_select = ui.select(node_names, with_input=True).style(DEFAULT_FIELD_STYLE)
            edit_node_select = ui.input(label="Node Name", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)

            with ui.column() as column:
                ui.label("Colour")
                edit_node_colour_select = ui.select(COLOURS, value=COLOURS[0]).style(DEFAULT_FIELD_STYLE)

                ui.label("Shape")
                edit_node_shape_select = ui.select(SHAPES, value=SHAPES[0]).style(DEFAULT_FIELD_STYLE)
                edit_node_notes_ta = ui.textarea("Notes").style(DEFAULT_FIELD_STYLE)
                def column_visible(value) -> bool:
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

        ui.button('Edit Node', on_click=edit_node_dialog.open)


        # Delete Node Button
        with ui.dialog() as delete_node_dialog, ui.card():
            ui.markdown("Delete Node")
            #node_select = ui.select(node_names, with_input=True).style(DEFAULT_FIELD_STYLE)
            delete_node_select = ui.input(label="Node Name", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)

            with ui.row():
                def delete_node_clicked():
                    if not delete_node_select.value:
                        return
                    delete_node_dialog.close()
                    remove_node(delete_node_select.value)
                    clear_comp_values(delete_node_select)
                ui.button('Delete', on_click=delete_node_clicked)
                ui.button('Close', on_click=delete_node_dialog.close)

        ui.button('Delete Node', on_click=delete_node_dialog.open)
    

        ## Add spacer
        ui.label("| |")


        # Create Link Button 
        with ui.dialog() as new_link_dialog, ui.card():
            ui.markdown("New Link")
            # nodeA_select = ui.select(node_names, with_input=True).style(DEFAULT_FIELD_STYLE)
            nodeA_select = ui.input(label="From Node", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)
            # nodeB_select = ui.select(node_names, with_input=True).style(DEFAULT_FIELD_STYLE)
            nodeB_select = ui.input(label="To Node", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)
            msg_text = ui.textarea('Link Message').style(DEFAULT_FIELD_STYLE)
            

            with ui.row():
                def create_link_clicked():
                    if not nodeA_select.value or not nodeB_select.value:
                        return
                    new_link_dialog.close()
                    create_link(nodeA_select.value, nodeB_select.value, msg_text.value)
                    clear_comp_values(nodeA_select, nodeB_select, msg_text)
                ui.button('Create', on_click=create_link_clicked)
                ui.button('Close', on_click=new_link_dialog.close)

        ui.button('Add Link', on_click=new_link_dialog.open)


        # Edit Link Button
        with ui.dialog() as edit_link_dialog, ui.card():
            ui.markdown("Edit Link")
            edit_nodeA_input = ui.input(label="From Node", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)
            edit_nodeB_input = ui.input(label="To Node", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)
            edit_msg_text = ui.textarea('Link Message').style(DEFAULT_FIELD_STYLE)
            
            def edit_msg_visibility(value) -> bool:
                a_exists = edit_nodeA_input.value in node_names
                b_exists = edit_nodeB_input.value in node_names
                if a_exists and b_exists:
                    try:
                        link = netgraph.get_link(edit_nodeA_input.value, edit_nodeB_input.value)
                        edit_msg_text.value = link.msg
                        return True
                    except network.NetGraphException:
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

        ui.button('Edit Link', on_click=edit_link_dialog.open)



        # Remove Link Button
        with ui.dialog() as remove_link_dialog, ui.card():
            ui.markdown("Remove Link")
            remove_nodeA_select = ui.input(label="First Node", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)
            remove_nodeB_select = ui.input(label="Second Node", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)

            with ui.row():
                def remove_link_clicked():
                    if not remove_nodeA_select.value or not remove_nodeB_select.value:
                        return
                    remove_link_dialog.close()
                    remove_link(remove_nodeA_select.value, remove_nodeB_select.value)
                    clear_comp_values(remove_nodeA_select, remove_nodeB_select)
                ui.button('Remove', on_click=remove_link_clicked)
                ui.button('Close', on_click=remove_link_dialog.close)
        
        ui.button('Remove Link', on_click=remove_link_dialog.open)



def load_from_file(abspath):
    global save_file
    save_file = os.path.abspath(abspath)
    print(f"Loading from file: {save_file}")
    if os.path.exists(save_file):
        load_netgraph()
    else:
        redraw_graph()
    


def file_selection_dialog() -> str:
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
    
    dialog.props('persistent')
    dialog.open()



def main():
    parser = ArgumentParser(f"Expenosa's Network Visualiser {VERSION}")
    parser.add_argument('-f', '--file', type=str, default=None, help="Network json file location. Created if does not exist.")
    parser.add_argument('--web', default=False, action='store_true', help="Use web browser instead of native app window.")
    args = parser.parse_args()
    global save_file
    save_file = args.file
    native = not args.web

    ## Allow javscript resources for pyvis to be served
    app.add_static_files('/lib', 'lib')

    #redraw_graph()
    create_buttons_row()

    # load graph from file if it exists
    if save_file:
        load_from_file(save_file)
    else:
        file_selection_dialog()

    # Only reload on src changes in dev environment
    reload = os.path.isdir('env')
    window = (1280,800) if native else None
    ui.run(reload=reload, title="Network Visualiser", dark=True, window_size=window) #TODO favicon


if __name__ in {"__main__", "__mp_main__"}:
    import multiprocessing
    multiprocessing.freeze_support() ## Required for PyInstaller
    main()