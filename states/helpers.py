from termcolor import colored
from copy import deepcopy
import collections
from datetime import datetime


class FlatDictDiffer:
    def __init__(self, ref, target):
        self.ref, self.target = ref, target
        self.ref_set, self.target_set = set(ref.keys()), set(target.keys())
        self.isect = self.ref_set.intersection(self.target_set)
        self.differ = bool(self.added() or self.removed() or self.changed())

    def added(self):
        return self.target_set - self.isect

    def removed(self):
        return self.ref_set - self.isect

    def changed(self):
        return {k for k in self.isect if self.ref[k] != self.target[k]}

    def unchanged(self):
        return {k for k in self.isect if self.ref[k] == self.target[k]}

    def print_state(self):
        for k in self.added():
            print(colored("+", 'green'), f"{k} = {self.target[k]}")

        for k in self.removed():
            print(colored("-", 'red'), k)

        for k in self.changed():
            print(colored("~", 'yellow'), f"{k}:\n\t< {self.ref[k]}\n\t> {self.target[k]}")


def flatten(d, pkey='', sep='/'):
    items = []
    for k, v in d.items():
        new = f"{pkey}{sep}{k}" if pkey else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten(v, new, sep=sep).items())
        else:
            items.append((f"{sep}{new}", v))
    return dict(items)


def add(obj, path, value):
    parts = path.strip("/").split("/")
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = value


def search(state, path):
    result = state
    for p in path.strip("/").split("/"):
        result = result.get(p, {})
        if not result:
            break
    return {path: result}


def unflatten(d):
    output = {}
    for k, v in d.items():
        add(output, k, v)
    return output


def merge(a, b):
    result = deepcopy(a)
    for k, v in b.items():
        if isinstance(v, dict) and k in result and isinstance(result[k], dict):
            result[k] = merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result


def timestamp():
    return datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
