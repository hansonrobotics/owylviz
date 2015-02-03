from functools import wraps
import websocket
import struct

from . import utils

__all__ = ['OwylTree']

class OwylTree:

    def __init__(self, tree):
        self.tree = tree
        self.parsed = self._parse(tree)
        self.on_step = Event()
        self._connection = None

    def get_structure(self):
        return self._get_structure(self.parsed)

    def attach(self, url='ws://owylviz.heroku.com'):
        # if self.connection != None:
        #     raise Exception('This method can only be called once.')
        # self._connection = Connection(url)
        # self.on_step += [self._connection.step]
        return self._deepwrap(self.tree, self._wrapnode)

    @classmethod
    def _get_structure(cls, parsed):
        node, children = list(parsed.items())[0]
        return {'name': node.__name__,
                'children': [cls._get_structure(child) for child in children]}

    @classmethod
    def _parse(cls, tree):
        """Converts an owyl tree to a dictionary tree."""
        # If there's only one tuple in the closure, we assume it's the *args.
        # I.e. children. Specifically, owyl makeIterator functions.
        cell = utils.get_enclosed(tree, tuple)
        if len(cell) == 1:
            index, children = list(cell.items())[0]
            parsed = [cls._parse(child) for child in children]
            return {tree: parsed}
        else:
            return {tree: []}

    @classmethod
    def _deepwrap(cls, tree, wrapper):
        cell = utils.get_enclosed(tree, tuple)
        if len(cell) == 1:
            index, children = list(cell.items())[0]
            new_children = [cls._deepwrap(child, wrapper) for child in children]
            new_tree = utils.inject_closure(tree, {index: tuple(new_children)})
            return wrapper(new_tree)
        else:
            return wrapper(tree)

    def _wrapnode(self, makeIterator):
        def _new_iterator(iterator):
            self.on_step(new_makeIterator)
            result = None
            while True:
                result = yield iterator.send(result)

        @wraps(makeIterator)
        def new_makeIterator(*args, **kwargs):
            iterator = makeIterator(*args, **kwargs)
            return _new_iterator(iterator)
        return new_makeIterator

class Event(list):
    def __call__(self, *args, **kwargs):
        for f in self:
            f(*args, **kwargs)

class Connection:

    def __init__(self, url):
        self.ws = websocket.create_connection(url)

    def step(self, makeIterator):
        self.ws.send(self.strhash(makeIterator))

    def close(self):
        self.ws.close()

    @staticmethod
    def strhash(obj):
        return struct.pack('>q', hash(obj))
