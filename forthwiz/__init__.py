import chuckmoore as wizard
from os import path

cache_filename = 'forth_wizard_cache.txt'

ops = [ 'dup',
        'drop',
        'swap',
        'over',
        'rot',
        '>r',
        'r>',
        '2dup',
        '2drop',
        '2swap',
        '2over',
        '2rot',
        'nip',
        'tuck',
        '-rot',
        'r@',
        '2>r',
        '2r>',
        '2r@',
        '3pick',
        '4pick',
        '5pick',
        '6pick'
]

pick_ops =  [ '3pick',
              '4pick',
              '5pick',
              '6pick'
]

n_ops = 0 # ops added to solver

def convert_stacks(in_stack, out_stack):
    symbols = {}
    counter = 0
    def convert(symbol):
        nonlocal counter
        if symbol not in symbols:
            symbols[ symbol ] = counter
            counter += 1
        return symbols[ symbol ]
    s_in = [convert(s) for s in in_stack]
    s_out = [convert(s) for s in out_stack]
    # normalize stacks
    for i, n in enumerate(s_out):
        if s_out[i] != i: break
        if s_out.count(n) != 1:
            s_in = [x - n for x in s_in[n:]]
            s_out = [x - n for x in s_out[n:]]
            break
    return s_in, s_out

def set_stacks(in_stack, out_stack):
    s_in, s_out = convert_stacks(in_stack, out_stack)
    wizard.init()
    wizard.set_stack_in(s_in)
    wizard.set_stack_out(s_out)

def solve_next():
    if n_ops == 0:
        add_all_ops()
    code = wizard.solve()
    if code is None:
        return []
    if code == -1:
        return None
    return [ ops[ op ] for op in code ]

code_map = { "3pick" : ["3", "pick"],
             "4pick" : ["4", "pick"],
             "5pick" : ["5", "pick"],
             "6pick" : ["6", "pick"]
}

def convert_code(code):
    ret = []
    for x in code:
        c = code_map.get(x)
        ret.extend(c) if c else ret.append(x)
    return ret

def add_pick_ops():
    global n_ops
    n_ops += len(pick_ops)
    for o in pick_ops:
        wizard.add_op(ops.index(o))

def add_none_pick_ops():
    global n_ops
    for o in ops:
        if o not in pick_ops:
            n_ops += 1
            wizard.add_op(ops.index(o))

def add_all_ops():
    global n_ops
    n_ops += len(ops)
    for o in ops:
        wizard.add_op(ops.index(o))

def find_solution(use_pick):
    # find solution without pick
    add_none_pick_ops()
    without_pick = solve_next()
    if not use_pick:
        return without_pick
    # find solution with pick
    wizard.reset_solver()
    add_pick_ops()
    with_pick = solve_next()
    c_without_pick = convert_code(without_pick)
    c_with_pick = convert_code(with_pick)
    # an attempt at choose the 'best' solution
    # When does it become preferable to use pick?
    len_with = len(c_with_pick)
    len_without = len(c_without_pick)
    if len_with < len_without:
        # using pick made the solution shorter
        return c_with_pick, with_pick
    if len_with == len_without:
        # if there are at least as many 'drop's as 'pick's, prefer 'pick'
        if ( ( c_without_pick.count('drop') + c_without_pick.count('nip') )
             >= c_with_pick.count('pick') ):
            return c_with_pick, with_pick
        # otherwise solutions are tied, don't use pick
    return c_without_pick, without_pick

def solve(in_stack, out_stack, use_cache=True, use_pick=True):
    if not cache and use_cache:
        cache_read()
    s_in, s_out = convert_stacks(in_stack, out_stack)
    key = tuple(s_in + [-1] + s_out)
    if use_cache:
        code = cache.get(key)
        if code:
            return code
    wizard.init()
    wizard.set_stack_in(s_in)
    wizard.set_stack_out(s_out)
    code, cache_code = find_solution(use_pick)
    if code and use_cache:
        # cache unconverted code so that it can be changed per forth target
        cache_save(key, cache_code)
    return code

cache = {}

def cache_read():
    if not path.exists(cache_filename):
        return
    with open(cache_filename,'r') as f:
        for line in f.readlines():
            k,v = line.split('=')
            cache[tuple(map(int, k.split()))] = v.split()

def cache_save(key, value):
    cache[key] = value
    k=' '.join([str(x) for x in key])
    v=' '.join([str(x) for x in value])
    flag = 'a' if path.exists(cache_filename) else 'w'
    with open(cache_filename,flag) as f:
        f.write('{}={}\n'.format(k,v))
