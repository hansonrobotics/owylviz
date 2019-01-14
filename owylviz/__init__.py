#Copyright (c) 2013-2018 Hanson Robotics, Ltd.
import platform, sys, re
from functools import wraps
import socketIO_client
from socketIO_client import SocketIO, BaseNamespace
import time
from types import FunctionType
import logging

from . import utils

class OwylTree:

    def __init__(self, tree):
        self.tree = tree
        self.on_enter = Event()
        self.on_yield = Event()
        self._new_tree = None
        self._parsed = self._parse(tree)
        self._connection = None

    @property
    def tree_with_hooks(self):
        """ A copy of the tree that will trigger on_enter and on_yield events """
        if not self._new_tree:
            self._new_tree = self._deepwrap(self.tree, self._wrapnode)
        return self._new_tree

    def get_structure(self):
        """ Returns tree structure in json-encodable format """
        return self._get_structure(self._parsed)

    def connect(self, connection=None):
        """ Connects to a webserver.
        To specify host, port or room name, pass an owylviz.Connection instance.
        """
        if self._connection != None:
            raise Exception('This method can only be called once.')

        if connection == None:
            connection = Connection()
        connection.set_introduction(self.get_structure())
        self.on_enter += [connection.step]
        self.on_yield += [connection.step]
        self._connection = connection

    @classmethod
    def _get_structure(cls, parsed):
        node, children = list(parsed.items())[0]
        return {'name': node.__name__,
                'desc': cls._get_desc(node),
                'id': utils.b52int(id(node)),
                'children': [cls._get_structure(child) for child in children]}

    DESC_TYPES = [str, int, float, bool, type(None)]
    @classmethod
    def _get_desc(cls, node):
        """ Concatenates all primitives in args and kwargs enclosed in node. """

        strs = []
        cell = utils.get_enclosed(node, tuple)
        for index, args in cell.items():
            strs += [str(arg) for arg in args if type(arg) in cls.DESC_TYPES]

        cell = utils.get_enclosed(node, dict)
        for index, kwargs in cell.items():
            strs += [str(val) for key, val in
                     sorted(kwargs.items(), key=lambda x: x[0])
                     if type(val) in cls.DESC_TYPES]

        return ' '.join(strs)

    @classmethod
    def _parse(cls, tree):
        """ Converts an owyl tree to a dictionary tree. """
        # If there's only one tuple in the closure, we assume it's the *args and
        # all functions in *args - children. Specifically, owyl makeIterator functions.
        cell = utils.get_enclosed(tree, tuple)
        if len(cell) == 1:
            index, args = list(cell.items())[0]
            children = [arg for arg in args if isinstance(arg, FunctionType)]
            parsed = [cls._parse(child) for child in children]
            return {tree: parsed}
        else:
            return {tree: []}

    @classmethod
    def _deepwrap(cls, tree, wrapper):
        cell = utils.get_enclosed(tree, tuple)
        if len(cell) == 1:
            index, args = list(cell.items())[0]
            new_args = [cls._deepwrap(arg, wrapper)
                        if isinstance(arg, FunctionType) else arg
                        for arg in args]
            new_tree = utils.inject_closure(tree, {index: tuple(new_args)})
            new_tree.original_id = id(tree)
            return wrapper(new_tree)
        else:
            return wrapper(tree)

    def _wrapnode(self, makeIterator):
        def _new_iterator(iterator):
            taskid = utils.b52int(
                getattr(makeIterator, 'original_id', id(makeIterator)))
            self.on_enter(taskid)
            sendval = None
            while True:
                result = iterator.send(sendval)
                if result in [True, False, None]:
                    self.on_yield(taskid, result)
                sendval = yield result

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

    ASSUMED_TIMEOUT = 30 # inactivity seconds to reconnect after

    def __init__(self, room=None, host='owylviz.herokuapp.com', port=80):
        self.host = host
        self.port = port
        self.room = room if room else self.generate_name()

    def set_introduction(self, data):
        self.intro_data = data
        self._reconnect()

    def step(self, taskid, yieldval=None):
        self._check_reconnect()
        self._emit('step', taskid, yieldval)

    def _emit(self, *args):
        self.ns.emit(*args)
        self.last_emit = time.time()
        self.io.heartbeat_pacemaker.send(next(self.io.gen_elapsed_time))

    def _check_reconnect(self):
        if time.time() - self.last_emit > self.ASSUMED_TIMEOUT:
            self._reconnect()

    def _reconnect(self):
        # Initialize connection
        self.io = SocketIO(self.host, self.port, wait_for_connection=False)
        self.ns = self.io.define(BaseNamespace, '/accept')

        # Prepare to send manual heartbeat
        self.io.gen_elapsed_time = socketIO_client._yield_elapsed_time()
        next(self.io.gen_elapsed_time)

        self._emit('introduce', self.room, self.intro_data)
        logging.info("Publishing your Owyl tree: http://{}:{}/{}".format(self.host, self.port, self.room))

    @staticmethod
    def generate_name():
        name = '{}-{}'.format(platform.node(), sys.argv[0])
        name = re.sub('[^0-9a-zA-Z/]+', '-', name)
        return name
