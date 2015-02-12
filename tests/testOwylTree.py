import unittest
from mock import Mock
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

    def testHook(self):
        tree = owyl.sequence(owyl.succeed(),
                             owyl.succeed())
        viztree = OwylTree(tree)
        structure = viztree.get_structure()
        ids = [structure['id']] + [child['id'] for child in structure['children']]

        mock = Mock()
        viztree.on_step += [mock]
        tree = viztree.tree_with_hooks
        [x for x in owyl.visit(tree)]

        for taskid in ids:
            mock.assert_any_call(taskid)

if __name__ == "__main__":
    unittest.main()
