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
# netgraph.add_node(network.Node("Chapel Of Anticipation", colour='gold', shape='triangle'))
# netgraph.add_node(network.Node("Example Node"))
# netgraph.add_link("Chapel Of Anticipation", "Example Node")

node_names = ['']
node_names.extend(netgraph.get_all_node_names())


def notify_on_netgraph_error(func):
    def inner(*args, **kwargs):
        try:
            func(*args, **kwargs)
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
    redraw_graph(save=False)


def update_elements():
    node_names.clear()
    node_names.extend(netgraph.get_all_node_names())
    ui.update()


def redraw_graph(save=True):
    niceglobals.get_client().body_html = "" # Remove existing HTML
    html = network.generate(netgraph)
    save_netgraph()
    ui.add_body_html(html)
    update_elements()
    ui.open('/')


@notify_on_netgraph_error
def add_node(name, colour, shape):
    print(f"Adding new node: '{name}' with colour {colour} and shape {shape}")
    netgraph.add_node(network.Node(name, colour=colour, shape=shape))

    redraw_graph()


@notify_on_netgraph_error
def edit_node(name, colour, shape, notes):
    print(f"Editing node: '{name}' to colour {colour} and shape {shape} with notes: {notes}")
    node = netgraph.get_node(name)
    node.colour = colour
    node.shape = shape
    node.notes = notes
    redraw_graph()


@notify_on_netgraph_error
def connect_nodes(nodeA: str, nodeB: str, msg: str=""):
    print(f"Connecting '{nodeA}' to '{nodeB}' with message: '{msg}'")
    netgraph.add_link(nodeA, nodeB, msg)
    redraw_graph()


@notify_on_netgraph_error
def remove_node(name: str):
    print(f"Deleting node '{name}'")
    netgraph.delete_node(name)
    redraw_graph()


@notify_on_netgraph_error
def remove_link(nodeA: str, nodeB: str):
    print(f"Deleting link between {nodeA} and {nodeB}")
    netgraph.remove_link(nodeA, nodeB)
    redraw_graph()


##TODO edit link
##TODO rename node


def create_buttons_row():
    with ui.row():
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
                    new_node_dialog.close()
                    add_node(node_name_field.value, create_node_colour_select.value, create_node_shape_select.value)
                    if (link_from_field.value):
                        connect_nodes(node_name_field.value, link_from_field.value, link_msg_field.value)
                    node_name_field.value = ""
                    link_from_field.value = ""
                    link_msg_field.value = ""
                ui.button('Create', on_click=create_node_clicked)
                ui.button('Close', on_click=new_node_dialog.close)

        ui.button('Create Node', on_click=new_node_dialog.open)
        


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
                    exists = value in node_names
                    if exists:
                        node = netgraph.get_node(value)
                        edit_node_colour_select.value = node.colour
                        edit_node_shape_select.value = node.shape
                        edit_node_notes_ta.value = node.notes
                    return exists

                column.bind_visibility_to(edit_node_select, 'value', column_visible)

            with ui.row():
                def edit_node_clicked():
                    edit_node_dialog.close()
                    edit_node(edit_node_select.value, edit_node_colour_select.value, 
                              edit_node_shape_select.value, edit_node_notes_ta.value)
                    edit_node_select.value = ""
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
                    delete_node_dialog.close()
                    remove_node(delete_node_select.value)
                    delete_node_select.value=""
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
                    new_link_dialog.close()
                    connect_nodes(nodeA_select.value, nodeB_select.value, msg_text.value)
                    nodeA_select.value = ""
                    nodeB_select.value = ""
                    msg_text.value = ""
                ui.button('Create', on_click=create_link_clicked)
                ui.button('Close', on_click=new_link_dialog.close)

        ui.button('Add Link', on_click=new_link_dialog.open)


        # Remove Link Button
        with ui.dialog() as remove_link_dialog, ui.card():
            ui.markdown("Remove Link")
            remove_nodeA_select = ui.input(label="First Node", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)
            remove_nodeB_select = ui.input(label="Second Node", autocomplete=node_names).style(DEFAULT_FIELD_STYLE)
            with ui.row():
                def remove_link_clicked():
                    remove_link_dialog.close()
                    remove_link(remove_nodeA_select.value, remove_nodeB_select.value)
                    remove_nodeA_select.value = ""
                    remove_nodeB_select.value = ""
                ui.button('Remove', on_click=remove_link_clicked)
                ui.button('Close', on_click=remove_link_dialog.close)
        
        ui.button('Remove Link', on_click=remove_link_dialog.open)

    ## TODO add notes to node
    ## TODO rename node
    ## TODO edit link
    ## TODO button to download HTML
    ## TODO button to download json data

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
        ui.button('Exit', on_click=app.shutdown)

    
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

    ## Allow javscript resources for pyvsi to be served
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
    # ui.run(reload=reload, title="Network Visualiser", dark=True)


if __name__ in {"__main__", "__mp_main__"}:
    import multiprocessing
    multiprocessing.freeze_support() ## Required for PyInstaller
    main()