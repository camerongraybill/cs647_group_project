from itertools import count
from json import loads
from sys import argv

import matplotlib.pyplot as plt
import numpy as np

unique_val = count(0)


def get_data(path_to_file):
    with open(path_to_file) as f:
        all_data = loads(f.read())
        return all_data


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
    all_points = [np.mean([a['amount_acquired'] for a in all_data['data'] if a['iteration'] == x] or [0]) for x in
                  range(all_data['metadata']['iterations'])]
    num_iterations = all_points.index(0) + 1 if all_points.index(0) is not None else all_data['metadata']['iterations']
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
    all_points = [np.mean([a['amount_acquired'] for a in all_data['data'] if a['iteration'] == x] or [0]) for x in
                  range(all_data['metadata']['iterations'])]
    num_iterations = all_points.index(0) + 1 if all_points.index(0) is not None else all_data['metadata']['iterations']
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
    all_points = [np.mean([a['amount_acquired'] for a in all_data['data'] if a['iteration'] == x] or [0]) for x in
                  range(all_data['metadata']['iterations'])]
    num_iterations = all_points.index(0) + 1 if all_points.index(0) is not None else all_data['metadata']['iterations']
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
    try:
        path = argv[2]
        cmd = argv[1]
        try:
            {
                'pop': make_population_graphs,
                'happy': make_happiness_graphs,
                'util': make_utility_graphs,
                'all': make_all_graphs
            }[cmd](path)
            plt.show()
        except KeyError:
            print("valid commands are 'pop', 'happy', 'util', and 'all'")
    except:
        print(f"usage: {argv[0]} pop|happy|util|all path/to/json/file")
