#######################################################################################################
# Simple program that transcodes a clip to a smaller version that fits within the file size limit given
#######################################################################################################
from typing import List
from pyvis.network import Network
import jsonpickle

COLOURS = ['White', 'Pink', 'Red', 'Maroon', 'Yellow', 'Green', 'Lime', 'Green', 'Olive', 'Aqua', 'Blue', 'Navy', 'Fuchsia', 'Purple', 'Teal', 'Silver', 'Gold']
SHAPES = ['dot', 'circle', 'ellipse', 'triangle', 'triangleDown', 'square', 'box', 'diamond', 'star', 'database']


class NetGraphException(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg


class Link():
    def __init__(self, _to:str, msg: str=""):
        self._to = _to.strip()
        self.msg = msg.strip()


class Node():
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        ## Add default values for new fields since jsonpickle will give them null values
        obj.notes = ""
        return obj

    def __init__(self, name: str, colour='white', shape='dot', notes=""):
        self.name = name.strip()
        self.colour = colour.strip()
        self.shape = shape.strip()
        self.links = list()
        self.notes = notes.strip()
    
    def add_link(self, link: Link):
        self.links.append(link)

    def remove_link(self, name):
        self.links = [x for x in self.links if x._to != name]


## TODO use unique ids for nodes so that renames do not require searching through every node?
class NetworkGraph():
    def __init__(self, nodes: List[Node]=[]):
        self._nodes = { n.name: n for n in nodes }
        self.add_node(Node("First Node"))


    def get_all_node_names(self) -> List[str]:
        return list(self._nodes.keys())


    def get_node(self, name: str) -> Node:
        if not self.contains_node(name):
            raise NetGraphException("Node does not exist: " + name)
        return self._nodes[name]


    def contains_node(self, name: str) -> bool:
        all_names = {x.lower() for x in self.get_all_node_names()}
        return name.lower() in all_names


    def add_node(self, node: Node):
        if self.contains_node(node.name):
            raise NetGraphException("Node already exists: " + node.name)
        self._nodes[node.name] = node


    def add_link(self, from_node: str, to_node: str, msg: str=""):
        ## make sure they exist
        if not self.contains_node(from_node):
            raise NetGraphException("Node does not exist: " + from_node)
        if not self.contains_node(to_node):
            raise NetGraphException("Node does not exist: " + to_node)
        node = self._nodes[from_node]
        node.add_link(Link(to_node, msg))

    
    def remove_link(self, nodeA: str, nodeB: str):
        a = self.get_node(nodeA)
        b = self.get_node(nodeB)
        a.remove_link(nodeB)
        b.remove_link(nodeA)

    ## TODO edit link
    
    ## TODO rename node

    def delete_node(self, name: str):
        if name in self._nodes:
            self._nodes.pop(name)
        
        ## Delete links from other nodes
        for n in self._nodes.values():
            n.remove_link(name)



def generate_custom(net: Network, graph: NetworkGraph) -> str:
    ''' Generate HTML to display the network graph '''
    for n in graph._nodes.values():
        net.add_node(n.name, label=n.name, title=f'{n.name}\n{n.notes}', color=n.colour, shape=n.shape)
    
    for n in graph._nodes.values():
        for e in n.links:
            net.add_edge(n.name, e._to, title=e.msg)
    
    return net.generate_html()



def generate(graph: NetworkGraph) -> str:
    ''' Generate HTML to display the network graph '''
    net = Network(height="85vh", width="100%", bgcolor="#222222", font_color="white",
                  select_menu=True, filter_menu=False)
    net.toggle_physics(True)
    #net.show_buttons()

    return generate_custom(net, graph)



def save_network_graph(path: str, netgraph: NetworkGraph):
    print(f"Saving net graph to file: {path}")
    with open(path, 'w', encoding='utf-8') as f:
        json = jsonpickle.encode(netgraph, indent=2)
        f.write(json)


def load_network_graph(path: str) -> NetworkGraph:
    print(f"Loading netgraph from file: {path}")
    with open(path, encoding='utf-8') as f:
        json = f.read()
        return jsonpickle.decode(json)