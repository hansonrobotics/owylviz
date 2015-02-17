import unittest
from mock import Mock, call
import copy

import owyl
from owyl import blackboard
from owylviz import OwylTree

def truncate(obj, allowedkeys):
    """ Removes all keys not in the allowed list in the tree. """
    if isinstance(obj, list):
        return [truncate(val, allowedkeys) for val in obj]
    elif isinstance(obj, dict):
        new_obj = copy.copy(obj)
        for key in obj:
            if not (key in allowedkeys):
                del new_obj[key]
            elif type(obj[key]) in [dict, list]:
                new_obj[key] = truncate(obj[key], allowedkeys)
        return new_obj
    else:
        return obj

class Tests(unittest.TestCase):

    def testStructure(self):
        tree = owyl.sequence(owyl.succeed(),
                             owyl.fail())
        viztree = OwylTree(tree)
        structure = truncate(viztree.get_structure(), ['name', 'children'])
        self.assertEquals(structure,
                          {'name': 'sequence',
                           'children': [{'name': 'succeed', 'children': []},
                                        {'name': 'fail', 'children': []}]})

    def testStructureBig(self):
        tree = owyl.parallel(owyl.sequence(owyl.repeatAlways(blackboard.setBB()), owyl.log()),
                             owyl.selector(owyl.repeatUntilSucceed(blackboard.checkBB())),
                             owyl.repeatUntilFail(owyl.fail()))
        viztree = OwylTree(tree)
        structure = truncate(viztree.get_structure(), ['name', 'children'])
        self.assertEquals(structure,
                          {'name': 'parallel',
                           'children': [{'name': 'sequence',
                                         'children': [{'name': 'repeatAlways',
                                                       'children': [{'name': 'setBB',
                                                                     'children': []}]},
                                                      {'name': 'log',
                                                       'children': []}]},
                                        {'name': 'selector',
                                         'children': [{'name': 'repeatUntilSucceed',
                                                       'children': [{'name': 'checkBB',
                                                                     'children': []}]}]},
                                        {'name': 'repeatUntilFail',
                                         'children': [{'name': 'fail',
                                                       'children': []}]}]})

    def testDescriptionSetBB(self):
        tree = blackboard.setBB(key='somekey', val=3)
        viztree = OwylTree(tree)
        structure = truncate(viztree.get_structure(), ['desc'])
        self.assertEquals(structure, {'desc': 'somekey 3'})

    def testDescriptionCheckBB(self):
        tree = blackboard.checkBB(key='somekey', check=lambda x: x == 3)
        viztree = OwylTree(tree)
        structure = truncate(viztree.get_structure(), ['desc'])
        self.assertEquals(structure, {'desc': 'somekey'})

    def testDescriptionLog(self):
        tree = owyl.log('some message')
        viztree = OwylTree(tree)
        structure = truncate(viztree.get_structure(), ['desc'])
        self.assertEquals(structure, {'desc': 'some message'})

    def testDescriptionSmallTree(self):
        tree = owyl.sequence(owyl.failAfter(after=10),
                             owyl.log('How did you execute me?'))

        viztree = OwylTree(tree)
        structure = truncate(viztree.get_structure(), ['name', 'desc', 'children'])
        self.assertEquals(structure, {'name': 'sequence', 'desc': '',
                                      'children': [{'name': 'failAfter', 'desc': '10',
                                                    'children': []},
                                                   {'name': 'log', 'desc': 'How did you execute me?',
                                                    'children': []}]})

    def testYieldHookSmallTree(self):
        tree = owyl.sequence(owyl.succeed(),
                             owyl.fail())
        viztree = OwylTree(tree)
        structure = viztree.get_structure()

        mock = Mock()
        viztree.on_yield += [mock]
        tree = viztree.tree_with_hooks
        [x for x in owyl.visit(tree)]

        mock.assert_has_calls([call(structure['children'][0]['id'], True),
                               call(structure['children'][1]['id'], False),
                               call(structure['id'], False)])

    def testEnterHookSmallTree(self):
        tree = owyl.sequence(owyl.succeed(),
                             owyl.fail())
        viztree = OwylTree(tree)
        structure = viztree.get_structure()

        mock = Mock()
        viztree.on_enter += [mock]
        tree = viztree.tree_with_hooks
        [x for x in owyl.visit(tree)]

        mock.assert_has_calls([call(structure['id']),
                               call(structure['children'][0]['id']),
                               call(structure['children'][1]['id'])])

    def testHooksLog(self):
        tree = owyl.log('some message')
        viztree = OwylTree(tree)
        structure = viztree.get_structure()
        taskid = structure['id']

        mock = Mock()
        viztree.on_enter += [mock]
        viztree.on_yield += [mock]
        tree = viztree.tree_with_hooks
        [x for x in owyl.visit(tree)]

        mock.assert_has_calls([call(taskid),
                               call(taskid, True)])

if __name__ == "__main__":
    unittest.main()
