from collections import defaultdict
from collections import namedtuple
from pathlib import Path
from sys import argv

import matplotlib.pyplot as plt

from parse_data_file import get_data, get_end

entry = namedtuple('entry',
                   ['strategy', 'iterations', 'max_up', 'max_down', 'starting_good_clients', 'starting_bad_clients',
                    'peer_size'])


def parse_data_folder(path_to_folder):
    f = Path(path_to_folder)
    new_data = defaultdict(lambda: dict())
    for child in f.iterdir():
        data = get_data(str(child))
        end = get_end(data)
        meta = data['metadata']
        new_data[
            entry(meta['strategy'], meta['iterations'], meta['max_up'], meta['max_down'], meta['starting_good_clients'],
                  meta['starting_bad_clients'], meta['peer_size'])] = end
    return new_data


def make_a_graph(path_to_folder):
    data = parse_data_folder(path_to_folder)
    print(data)

if __name__ == '__main__':
    # try:
    path = argv[2]
    cmd = argv[1]
    try:
        {
            'a': make_a_graph
        }[cmd](path)
        plt.show()
    except KeyError:
        print("valid commands are ")
    # except:
    #    print(f"usage: {argv[0]} | path/to/json/file")
