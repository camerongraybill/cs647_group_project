from collections import defaultdict
from pathlib import Path
from parse_data_file import get_data, get_end
from sys import argv
import matplotlib.pyplot as plt

def parse_data_folder(path_to_folder):
    f = Path(path_to_folder)
    new_data = defaultdict(lambda: dict())
    for child in f.iterdir():
        data = get_data(str(child))
        end = get_end(data)
        for k, v in data['metadata'].items():
            new_data[k][v] = end
    return new_data

def make_a_graph(path_to_folder):
    print(parse_data_folder(path_to_folder))


if __name__ == '__main__':
    #try:
    path = argv[2]
    cmd = argv[1]
    try:
        {
            'a': make_a_graph
        }[cmd](path)
        plt.show()
    except KeyError:
        print("valid commands are ")
    #except:
    #    print(f"usage: {argv[0]} | path/to/json/file")
