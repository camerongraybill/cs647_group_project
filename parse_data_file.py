from itertools import count
from json import loads
from sys import argv

import matplotlib.pyplot as plt
import numpy as np

unique_val = count(0)

import networkx as nx
import io
import cv2
from itertools import chain

def makevid():
    G = nx.Graph()
    vid = cv2.VideoWriter(f'./test.avi', 0, 2.5, (640, 480))

    with open('./results/DropZeros/50_80_20_4_100_100.json') as f:
        data = loads(f.read())
        id = 0

        gud = []
        bad = []
        edges = []

        for i in range(data['metadata']['iterations']):
            idx = i * (data['metadata']['starting_good_clients'] + data['metadata']['starting_bad_clients'])
            agent = data['data'][idx]
            print(agent)
            edges.append([(agent['id'], data['data'][idx + p]['id']) for p in agent['peers']])
            for p in agent['peers']:
                peer_idx = idx + p
                peer = data['data'][peer_idx]
                if peer['free_rider']:
                    bad.append(peer['id'])
                else:
                    gud.append(peer['id'])

        print(len(gud))
        print(gud)
        print(len(bad))
        print(bad)
        #G.add_nodes_from(chain(gud, bad))


        #nx.draw(G)
        #plt.show()
        for grp in edges:
            plt.clf()
            G = nx.Graph()
            G.add_nodes_from(chain(data['data'][0], gud, bad))

            #G.remove_edges_from([x for x in G.edges()])
            print(grp)
            G.add_edges_from(grp)

            pos = nx.spring_layout(G)

            nx.draw_networkx_nodes(G, pos, nodelist=gud, node_color='g', node_size=100, alpha=0.8)
            nx.draw_networkx_nodes(G, pos, nodelist=bad, node_color='r', node_size=100, alpha=0.8)
            nx.draw_networkx_edges(G, pos, alpha=0.5)

            plt.savefig('./img.png', format='png')
            img = cv2.imread('./img.png')

            vid.write(img)

        cv2.destroyAllWindows()
        vid.release()


if __name__ == '__main__':
    makevid()

def get_data(path_to_file):
    with open(path_to_file) as f:
        all_data = loads(f.read())
        return all_data


def get_end(all_data):
    try:
        all_points = [np.mean([a['amount_acquired'] for a in all_data['data'] if a['iteration'] == x] or [0]) for x in
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



def make_all_graphs(path_to_file):
    make_population_graphs(path_to_file)
    make_happiness_graphs(path_to_file)
    make_utility_graphs(path_to_file)


if __name__ == '__main__':
    makevid()
    # try:
    #     path = argv[2]
    #     cmd = argv[1]
    #     try:
    #         {
    #             'pop': make_population_graphs,
    #             'happy': make_happiness_graphs,
    #             'util': make_utility_graphs,
    #             'all': make_all_graphs
    #         }[cmd](path)
    #         plt.show()
    #     except KeyError:
    #         print("valid commands are 'pop', 'happy', 'util', and 'all'")
    # except:
    #     print(f"usage: {argv[0]} pop|happy|util|all path/to/json/file")
    #     good_guys = [
    #         y for y in all_data['data'] if not y['free_rider']
    #     ]

    #     bad_guys = [
    #         y for y in all_data['data'] if y['free_rider']
    #     ]

    # plt.plot([sum(a['iteration'] == x for a in good_guys) for x in range(all_data['metadata']['iterations'])], 'g')
    # plt.plot([sum(a['iteration'] == x for a in bad_guys) for x in range(all_data['metadata']['iterations'])], 'r')
    # plt.plot([sum(a['iteration'] == x for a in all_data['data']) for x in range(all_data['metadata']['iterations'])], 'b')
    # plt.show()
