from itertools import count, chain
from json import loads
from sys import argv

import cv2
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

unique_val = count(0)


def make_peer_graph(path_to_input):
    vid = cv2.VideoWriter(f'./test.avi', 0, 2, (640, 480))
    data = get_data(path_to_input)
    G = nx.Graph()
    target_clients = sorted(list(set(x['id'] for x in data['data'])))
    all_peers = set(chain.from_iterable(x['peers'] for x in data['data'] if x['id'] in target_clients))
    original_baddies = {
        x['id'] for x in data['data'] if x['free_rider'] and x['iteration'] == 0
    }
    all_clients = all_peers | set(target_clients)
    G.add_nodes_from(all_clients)
    pos = nx.circular_layout(all_clients)

    for iteration in range(get_end(data)):
        entries = [x for x in data['data'] if
                   x['iteration'] == iteration and (x['id'] in all_peers or x['id'] in target_clients)]
        good_entries = [x for x in entries if not x['free_rider']]
        bad_entries = [x for x in entries if x['free_rider']]
        clients_at_this_iter = (x for x in entries if x['id'] in target_clients)

        def edges():
            for client in clients_at_this_iter:
                for peer in client['peers']:
                    yield (client['id'], peer)

        G.add_edges_from(edges())
        nx.draw_networkx_nodes(G, pos, nodelist=[x['id'] for x in good_entries], node_color='g', node_size=100,
                               alpha=0.8, with_labels=True, label="Good Citizens")
        nx.draw_networkx_nodes(G, pos, nodelist=[x['id'] for x in bad_entries if x['id'] in original_baddies], node_color='r', node_size=100,
                               alpha=0.8, with_labels=True, label="Free Riders")
        nx.draw_networkx_nodes(G, pos, nodelist=[x['id'] for x in bad_entries if x['id'] not in original_baddies], node_color='y', node_size=100,
                               alpha=0.8, with_labels=True, label="Defectors")
        nx.draw_networkx_labels(G, pos)
        nx.draw_networkx_edges(G, pos, alpha=0.5)
        plt.xlim((-1.75, 1.1))
        plt.ylim((-1.1, 1.1))
        plt.axis("off")
        plt.title(f"{data['metadata']['strategy']} Iteration {iteration}")
        plt.legend(loc='upper left')
        plt.savefig('./img.png', format='png')
        img = cv2.imread('./img.png')
        vid.write(img)
        plt.clf()
        G.remove_edges_from(list(G.edges))
    cv2.destroyAllWindows()
    vid.release()


def get_data(path_to_file):
    with open(path_to_file) as f:
        all_data = loads(f.read())
        return all_data


def get_end(all_data):
    return all_data['metadata']['iterations']
    try:
        all_points = [sum([a['amount_acquired'] for a in all_data['data'] if a['iteration'] == x] or [0]) for x in
                      range(all_data['metadata']['iterations'])]
        return all_points.index(0) + 1
    except ValueError:
        return all_data['metadata']['iterations']


def get_good_bad_partition(all_data):
    good_guys = [
        y for y in all_data['data'] if not y['free_rider']
    ]

    bad_guys = [
        y for y in all_data['data'] if y['free_rider']
    ]
    return good_guys, bad_guys


def make_population_graphs(path_to_file):
    all_data = get_data(path_to_file)
    good, bad = get_good_bad_partition(all_data)

    num_agents = all_data['metadata']['starting_good_clients'] + all_data['metadata']['starting_bad_clients']
    num_iterations = get_end(all_data)
    f = plt.figure(next(unique_val))

    def add_plot(dataset, color, label, order):
        plt.plot([sum(a['iteration'] == x for a in dataset) for x in range(num_iterations)], color, label=label,
                 zorder=order)

    plt.title(f"{all_data['metadata']['strategy']}")
    plt.ylim(0 - .1 * num_agents, 1.1 * num_agents)
    plt.ylabel("Population Size")
    plt.xlabel("Iterations")
    add_plot(good, 'g', "Normal Users", 1)
    add_plot(bad, 'r', "Free Rider", 2)
    plt.legend()
    f.show()


def make_happiness_graphs(path_to_file):
    all_data = get_data(path_to_file)
    good, bad = get_good_bad_partition(all_data)

    # Find the end
    num_iterations = get_end(all_data)
    f = plt.figure(next(unique_val))

    def add_plot(dataset, color, label, order):
        plt.plot([np.mean([a['amount_acquired'] for a in dataset if a['iteration'] == x] or [0]) for x in
                  range(num_iterations)], color, label=label, zorder=order)

    plt.title(f"{all_data['metadata']['strategy']}")
    plt.ylabel("Mean Files Acquired")
    plt.xlabel("Iterations")
    add_plot(good, 'g', "Normal Users", 1)
    add_plot(bad, 'r', "Free Rider", 2)
    add_plot(all_data['data'], 'b', "All Users", 0)

    plt.ylim(0, all_data['metadata']['max_down'])

    plt.legend()

    f.show()


def make_utility_graphs(path_to_file):
    all_data = get_data(path_to_file)
    good, bad = get_good_bad_partition(all_data)

    # Find the end
    num_iterations = get_end(all_data)
    f = plt.figure(next(unique_val))

    def utility(entry):
        return (entry['amount_acquired'] / all_data['metadata']['max_down']) - (
            (.25 * entry['willing_to_give'] / all_data['metadata']['max_up']) if not entry['free_rider'] else 0)

    def add_plot(dataset, color, label, order):
        plt.plot([np.mean([utility(a) for a in dataset if a['iteration'] == x] or [0]) for x in range(num_iterations)],
                 color, label=label, zorder=order)

    plt.title(f"{all_data['metadata']['strategy']}")
    plt.ylabel("Mean Utility")
    plt.xlabel("Iterations")
    add_plot(good, 'g', "Normal Users", 1)
    add_plot(bad, 'r', "Free Rider", 2)
    add_plot(all_data['data'], 'b', "All Users", 0)

    ylim = plt.ylim()

    plt.ylim(ylim[0], 1)

    plt.legend()

    f.show()


def make_all_graphs(path_to_file, vid=False):
    make_population_graphs(path_to_file)
    make_happiness_graphs(path_to_file)
    make_utility_graphs(path_to_file)
    if vid:
        make_peer_graph(path_to_file)


if __name__ == '__main__':
    try:
        path = argv[2]
        cmd = argv[1]
        try:
            {
                'pop': make_population_graphs,
                'happy': make_happiness_graphs,
                'util': make_utility_graphs,
                'all': make_all_graphs,
                'allv': lambda x: make_all_graphs(x, True),
                'vid': make_peer_graph
            }[cmd](path)
            if cmd != 'vid':
                plt.show()
        except KeyError:
            print("valid commands are 'pop', 'happy', 'util', 'vid', 'allv', and 'all'")
    except:
        print(f"usage: {argv[0]} pop|happy|util|all|vid|allv path/to/json/file")
