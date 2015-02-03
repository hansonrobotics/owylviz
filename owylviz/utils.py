from functools import update_wrapper

def get_enclosed(func, typ):
    """Return values in func's closure of type typ as a dictionary, which maps
    their position in the cell list to the actual values."""
    cells = {i: cell.cell_contents for i, cell in enumerate(func.__closure__)
             if isinstance(cell.cell_contents, typ)}
    return cells


INJECTEDKEY = "injected_{}"
OUTERLINE = "    outer_{0} = injected_{0}"
INNERLINE = "        inner_{0} = outer_{0}"
SOURCE= ("def not_important():",
         "    def also_not_important():",
         "    return also_not_important")

def inject_closure(f, dct):
    """Return a copy of f, with a new closure.

    The new closure will have cells at indices dct.keys()
    overwritten with corresponding dct.values()

    Taken from:
    http://code.activestate.com/recipes/577760-change-a-functions-closure/
    """

    # build a dictionary that contains the complete desired closure content
    final_dct = get_enclosed(f, object)
    final_dct.update(dct)

    # build the source to exec
    injected = {}
    source = list(SOURCE)
    for i in range(len(final_dct)):
        source.insert(1, OUTERLINE.format(i))
        source.insert(-1, INNERLINE.format(i))
        injected[INJECTEDKEY.format(i)] = final_dct[i]

    # exec the source and pull the new closure
    exec("\n".join(source), injected, injected)
    closure = injected["not_important"]().__closure__

    # build the new function object
    func = type(f)(f.__code__, f.__globals__, f.__name__,
                             f.__defaults__, closure)
    update_wrapper(func, f)

    return func
