#!/usr/bin/env python

# this program tries to find matches in the history as the names change
# assumption: a constant number of characters are appended as names are changed
# assumption2: the final column is the name


import os
import sys
import re

history_file = sys.argv[1]
to_add = sys.argv[2]
trim_start_present = int(sys.argv[3])
trim_end_present = int(sys.argv[4])
trim_start_new = int(sys.argv[5])
trim_end_new = int(sys.argv[6])

f = open(history_file)
lines = f.readlines()
f.close()

history_order = []
history = {}

hist_headers = lines[0].strip().split()
hyphens = 0
for line in lines[1:]:
    line = line.strip()
    if (len(line) == 0):
        continue
    sp = line.split()

    assert(len(sp) == len(hist_headers))

    name = sp[-1][trim_start_present:len(sp[-1])-trim_end_present]
    if (sp[-1] == "-"):
        name = "hyphen%i"%hyphens
        hyphens += 1
    # print name
    # assert(name not in history)
    if (not (name not in history) ):
        print "hello"
        print name
        assert(name not in history)
    sp.append([])
    history[name] = sp
    history_order.append(name)


f = open(to_add)
lines = f.readlines()
f.close()

new_headers = lines[0].strip().split()

for line in lines[1:]:
    line = line.strip()
    if (len(line) == 0):
        continue
    sp = line.split()
    
    assert(len(sp) == len(new_headers))

    name = sp[-1][trim_start_new:len(sp[-1])-trim_end_new]

    # print name
    if (not (name in history)):
        print "No parent: " + name
        continue
        # assert(name in history)
    history[name][-1].append(sp)


old_name = hist_headers[-1]
match = re.match("name([0-9]+)", old_name)
new_num = 1
if (match != None):
    new_num = int(match.group(1))+1

new_headers[-1] = "name%i"%new_num

initial_layout = [hist_headers + new_headers]
for name in history_order:
    data = history[name]
    children = data[-1]
    if (len(children) == 0):
        children.append(["-"]*len(new_headers))

    for child in children:
        this_dat = []
        for i in range(len(hist_headers)):
            this_dat.append(data[i])
        for i in range(len(new_headers)):
            this_dat.append(child[i])

        initial_layout.append(this_dat)


widths = [0]*len(initial_layout[0])

for row in initial_layout:
    assert(len(row) == len(widths))
    for i in range(len(widths)):
        widths[i] = max(widths[i], len(row[i]))



hist_name_part = ".".join(history_file.split(".")[:-1])
new_name_part = ".".join(os.path.basename(to_add).split(".")[:-1])

out_name = hist_name_part + "." + new_name_part + ".history"


f = open(out_name, "w")
for row in initial_layout:
    for i in range(len(row)):
        fmt = "%%-%is "%widths[i]
        f.write(fmt%row[i])
    f.write("\n")

f.close()





















