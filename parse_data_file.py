from json import loads
import matplotlib.pyplot as plt
import numpy as np


def open_file(path_to_file):
    with open(path_to_file) as f:
        all_data = loads(f.read())
        good_guys = [
            y for y in all_data['data'] if not y['free_rider']
        ]

        bad_guys = [
            y for y in all_data['data'] if y['free_rider']
        ]

    plt.plot([sum(a['iteration'] == x for a in good_guys) for x in range(all_data['metadata']['iterations'])], 'g')
    plt.plot([sum(a['iteration'] == x for a in bad_guys) for x in range(all_data['metadata']['iterations'])], 'r')
    plt.plot([sum(a['iteration'] == x for a in all_data['data']) for x in range(all_data['metadata']['iterations'])], 'b')
    plt.show()