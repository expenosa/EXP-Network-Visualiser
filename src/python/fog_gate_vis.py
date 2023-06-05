#######################################################################################################
#
#######################################################################################################
import csv
from typing import Iterable, Dict
from argparse import ArgumentParser
from pyvis.network import Network

VERSION=0.1

DEFAULT_AREA_NAME='DEFAULT'

AREA_COLUMN='Area'
COLOUR_COLUMN='Colour'
SHAPE_COLUMN='Shape'
CUSTOMIZATION_COLUMNS=[AREA_COLUMN, COLOUR_COLUMN, SHAPE_COLUMN]

FROM_COLUMN='From'
TO_COLUMN='To'
GATEINFO_COLUMN='Gate Info'
NETWORK_COLUMNS=[FROM_COLUMN, TO_COLUMN, GATEINFO_COLUMN]


def show_network(all_areas: Dict, network: Iterable[Dict]):
    net = Network(height="90vh", width="100%", bgcolor="#222222", font_color="white",
                  select_menu=True, filter_menu=False)

    for row in network:
        node_from = row[FROM_COLUMN].strip()
        node_to = row[TO_COLUMN].strip()
        edge_comment = row[GATEINFO_COLUMN]

        add_missing_node(net, node_from, all_areas)
        add_missing_node(net, node_to, all_areas)
        net.add_edge(node_from, node_to, title=edge_comment)

    #net.show_buttons()
    net.toggle_physics(True)
    net.show('foggate.html', notebook=False, local=False)


def add_missing_node(net: Network, name: str, all_areas: Dict):
    if name in net.node_ids:
        return

    if name in all_areas:
        area_dict = all_areas[name]
    else:
        area_dict = all_areas[DEFAULT_AREA_NAME]

    colour = area_dict[COLOUR_COLUMN].strip()
    shape = area_dict[SHAPE_COLUMN].strip()
    net.add_node(name, color=colour, shape=shape)


def main():
    parser = ArgumentParser(f"Expenosa's Fog Gate Network Visualiser {VERSION}")
    parser.add_argument("all_areas_file", help="CSV containing all areas")
    parser.add_argument("network_file", help="Input Network CSV file")
    args = parser.parse_args()

    with open(args.all_areas_file) as f:
        all_areas_reader = csv.DictReader(f, skipinitialspace=True)
        all_areas_dict = {x['Area']:x for x in all_areas_reader}
    
    with open(args.network_file) as f:
        network_reader = csv.DictReader(f, skipinitialspace=True)
        network_csv = list(network_reader)
    
    show_network(all_areas_dict, network_csv)


if __name__ == "__main__":
    try:
        main()
        print("Process Finished!")
    except KeyboardInterrupt:
        print("Exiting due to keyboard interupt")