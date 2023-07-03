from __future__ import annotations
from typing import List
from pyvis.network import Network
from uuid import uuid4
import jsonpickle

COLOURS = ['White', 'Pink', 'Red', 'Maroon', 'Yellow', 'Green', 'Lime', 'Green', 'Olive', 'Aqua', 'Blue', 'Navy', 'Fuchsia', 'Purple', 'Teal', 'Silver', 'Gold']
SHAPES = ['dot', 'circle', 'ellipse', 'triangle', 'triangleDown', 'square', 'box', 'diamond', 'star', 'database']


class NetGraphException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg


class Link():
    def __init__(self, _to: str, msg: str=""):
        self._to = _to.strip()
        self.msg = msg.strip()

    def __str__(self) -> str:
        return str(self.__dict__)


class Node():
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        ## Add default values for new fields since jsonpickle will give them null values
        obj.notes = ""
        return obj

    def __init__(self, name: str, colour='White', shape='dot', notes=""):
        self.id = str(uuid4())
        self.name = name.strip()
        self.colour = colour.strip()
        self.shape = shape.strip()
        self.links = list()
        self.notes = notes.strip()
    

    def get_link(self, other_id: str) -> Link:
        ''' Fetch link to other node by id. None if no link could be found '''
        for link in self.links:
            if link._to == other_id:
                return link
        return None


    def add_link(self, link: Link):
        self.links.append(link)


    def remove_link(self, name):
        self.links[:] = [x for x in self.links if x._to != name]


    def is_valid(self):
        return self.id and self.name and \
            self.colour in COLOURS and \
            self.shape in SHAPES
    

    def __str__(self) -> str:
        return str(self.__dict__)



class NetworkGraph():
    def __init__(self, nodes: List[Node]=[]):
        self._nodes = { n.id: n for n in nodes }
        self._names_map = { n.name: n.id for n in nodes }

    def set_nodes(self, netgraph: NetworkGraph):
        self._nodes.clear()
        self._names_map.clear()

        self._nodes.update(netgraph._nodes)
        self._names_map.update(netgraph._names_map)


    def get_all_node_names(self) -> List[str]:
        return list(self._names_map.keys())


    def get_node_by_id(self, id: str) -> Node:
        if not id in self._nodes:
            raise NetGraphException("Node does not exist: " + id)
        return self._nodes[id]


    def get_node(self, name: str) -> Node:
        if not self.contains_node(name):
            raise NetGraphException("Node does not exist: " + name)
        id = self._names_map[name]
        return self._nodes[id]


    def contains_node(self, name: str) -> bool:
        return name in self._names_map


    def add_node(self, node: Node):
        if not node.is_valid():
            raise NetGraphException("Node is not valid")
        if self.contains_node(node.name):
            raise NetGraphException("Node already exists: " + node.name)
        self._nodes[node.id] = node
        self._names_map[node.name] = node.id


    def rename_node(self, old_name, new_name):
        node = self.get_node(old_name)
        node.name = new_name
        self._names_map.pop(old_name)
        self._names_map[new_name] = node.id


    def get_link(self, nodeA: str, nodeB: str, throw_not_found=True):
        a = self.get_node(nodeA)
        b = self.get_node(nodeB)
        link = a.get_link(b.id)

        if not link: # try other node if link was not found
            link = b.get_link(a.id)
        
        if not link and throw_not_found:
            raise(NetGraphException(f"Link not found between '{nodeA}' and '{nodeB}'"))
        return link
    

    def add_link(self, from_node: str, to_node: str, msg: str=""):        
        node = self.get_node(from_node)
        other_node = self.get_node(to_node)

        if self.get_link(from_node, to_node, throw_not_found=False):
            raise(NetGraphException(f"A link between '{from_node}' and '{to_node}' already exists"))

        node.add_link(Link(other_node.id, msg))

    
    def remove_link(self, nodeA: str, nodeB: str):
        a = self.get_node(nodeA)
        b = self.get_node(nodeB)
        a.remove_link(b.id)
        b.remove_link(a.id)


    def edit_link(self, nodeA: str, nodeB: str, msg: str):
        link = self.get_link(nodeA, nodeB)
        link.msg = msg


    def delete_node(self, name: str):
        node = self.get_node(name)
        if node.id in self._nodes:
            self._nodes.pop(node.id)
        if node.name in self._names_map:
            self._names_map.pop(node.name)
        
        ## Delete links from other nodes
        for n in self._nodes.values():
            n.remove_link(node.id)



def generate_custom(net: Network, graph: NetworkGraph) -> str:
    ''' Generate HTML to display the network graph '''
    for n in graph._nodes.values():
        net.add_node(n.name, label=n.name, title=f'{n.name}\n{n.notes}', color=n.colour, shape=n.shape)
    
    for n in graph._nodes.values():
        for e in n.links:
            to_node = graph.get_node_by_id(e._to)
            net.add_edge(n.name, to_node.name, title=e.msg)
    
    return net.generate_html()



def generate(graph: NetworkGraph) -> str:
    ''' Generate HTML to display the network graph '''
    net = Network(height="90vh", width="100%", bgcolor="#222222", font_color="white",
                  select_menu=True, filter_menu=False)
    net.toggle_physics(True)
    #net.show_buttons()

    return generate_custom(net, graph)



def save_network_graph(path: str, netgraph: NetworkGraph):
    print(f"Saving net graph to file: {path}")
    with open(path, 'w', encoding='utf-8') as f:
        json = save_network_graph_to_json(netgraph)
        f.write(json)


def load_network_graph(path: str) -> NetworkGraph:
    print(f"Loading netgraph from file: {path}")
    with open(path, encoding='utf-8') as f:
        json = f.read()
        return load_network_graph_from_json(json)
    

def save_network_graph_to_json(netgraph: NetworkGraph) -> str:
    return jsonpickle.encode(netgraph, indent=2)


def load_network_graph_from_json(pjson: str) -> NetworkGraph:
    return jsonpickle.decode(pjson)



class UndoHistory():
    def __init__(self):
        self.undos = list()
        self.redos = list()


    def add_undo(self, obj):
        jp = jsonpickle.encode(obj)
        self.undos.append(jp)


    def add_redo(self, obj):
        jp = jsonpickle.encode(obj)
        self.redos.append(jp)


    def undo(self, obj):
        if self.undos:
            self.add_redo(obj)
            jp = self.undos.pop(-1)
            return jsonpickle.decode(jp)
        return None


    def redo(self, obj):
        if self.redos:
            self.add_undo(obj)
            jp = self.redos.pop(-1)
            return jsonpickle.decode(jp)
        return None


    def clear_redos(self):
        self.redos.clear()