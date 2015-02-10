import unittest
from mock import Mock
import copy

import owyl
from owyl import blackboard
from owylviz import OwylTree

def deepdel(obj, badkey):
    if isinstance(obj, list):
        return [deepdel(val, badkey) for val in obj]
    elif isinstance(obj, dict):
        new_obj = copy.copy(obj)
        for key in obj:
            if key == badkey:
                del new_obj[key]
            elif type(obj[key]) in [dict, list]:
                new_obj[key] = deepdel(obj[key], badkey)
        return new_obj
    else:
        return obj

class Tests(unittest.TestCase):

    def testStructure(self):
        tree = owyl.sequence(owyl.succeed(),
                             owyl.fail())
        viztree = OwylTree(tree)
        structure = deepdel(viztree.get_structure(), 'id')
        self.assertEquals(structure,
                          {'name': 'sequence',
                           'children': [{'name': 'succeed', 'children': []},
                                        {'name': 'fail', 'children': []}]})

    def testStructureBig(self):
        tree = owyl.parallel(owyl.sequence(owyl.repeatAlways(blackboard.setBB())),
                             owyl.selector(owyl.repeatUntilSucceed(blackboard.checkBB())),
                             owyl.repeatUntilFail(owyl.fail))
        viztree = OwylTree(tree)
        structure = deepdel(viztree.get_structure(), 'id')
        self.assertEquals(structure,
                          {'name': 'parallel',
                           'children': [{'name': 'sequence',
                                         'children': [{'name': 'repeatAlways',
                                                       'children': [{'name': 'setBB',
                                                                     'children': []}]}]},
                                        {'name': 'selector',
                                         'children': [{'name': 'repeatUntilSucceed',
                                                       'children': [{'name': 'checkBB',
                                                                     'children': []}]}]},
                                        {'name': 'repeatUntilFail',
                                         'children': [{'name': 'fail',
                                                       'children': []}]}]})

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
