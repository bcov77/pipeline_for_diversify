#!/usr/bin/python

import os
import sys
import subprocess

def cmd(command, wait=True):
    # print ""
    # print command
    the_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (not wait):
        return
    the_stuff = the_command.communicate()
    return the_stuff[0] + the_stuff[1]


num_alanines = int(cmd("pdb2fasta %s | head -n 2 | tail -n 1 | tr -cd 'A' | wc -c"%sys.argv[1]).strip())

f = open("ala.comp", 'w')
f.write('PENALTY_DEFINITION\n')
f.write('TYPE ALA\n')
f.write('ABSOLUTE %d\n' % num_alanines)
f.write('PENALTIES 0 0 4 8\n')
f.write('DELTA_START -1\n')
f.write('DELTA_END 2\n')
f.write('BEFORE_FUNCTION CONSTANT\n')
f.write('AFTER_FUNCTION QUADRATIC\n')
f.write('END_PENALTY_DEFINITION\n')
f.close()

