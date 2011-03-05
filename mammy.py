# coding: utf8
import re
global_line_rx = []
global_block_rx = []

def before():
    r = u""
    r += u"""import re\n"""
    r += u"""global_line_rx = []\n"""
    r += u"""global_block_rx = []\n"""
    return {"code":r}

def after():
	r = u""
	return {"code":r}

#each block /before:\n/:
#   >>> def before():\n
def each_block_rx0(line, token, position, level, ops_stack, group, groups, id=0):
    r = u""
    r += u"""def before():\n"""
    return {"code":r, "stop":True}
global_block_rx.append({"rx":re.compile("before:\n"), "func":each_block_rx0,"rx_str":"before:\n", "id":0})


#each block /after:\n/:
#   >>> def after():\n
def each_block_rx1(line, token, position, level, ops_stack, group, groups, id=1):
    r = u""
    r += u"""def after():\n"""
    return {"code":r, "stop":True}
global_block_rx.append({"rx":re.compile("after:\n"), "func":each_block_rx1,"rx_str":"after:\n", "id":1})

#each line />>> ([.]+)\n/:
#   >>> def before():\n
def each_line_rx2(line, token, position, level, ops_stack, group, groups, id=2):
    r = u""
    r += u"""def after():\n"""
    return {"code":r, "stop":True}
global_block_rx.append({"rx":re.compile(">>> (.+)\n"), "func":each_line_rx2,"rx_str":">>> ([.]+)\n", "id":2})
