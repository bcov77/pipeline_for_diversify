#!/usr/bin/python

import os
import sys
import re
import subprocess

def cmd(command, wait=True):
    # print ""
    # print command
    the_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (not wait):
        return
    the_stuff = the_command.communicate()
    return the_stuff[0] + the_stuff[1]





#need these score files:
# 1. lines from gabe score per res
# 2. lx packscores
# 3. my packscores
# 4. monomer scores
# 5. ppi scores

# input files

# add_new_scores_to_history.py
# list of rifdock_outputs   
# file with all original *.dok
# monomer_stabilize folder
# ppi_scores.sc

add_new_scores_to_history = sys.argv[1]
rifdock_outputs_file = sys.argv[2]
all_og_dok_file = sys.argv[3]
monomer_stabilize_fol = sys.argv[4]
ppi_scores_file = sys.argv[5]

tmp = "scrounge_temp"

if (not os.path.exists(tmp)):
    os.mkdir(tmp)


# step 1, identifiy starting scaffolds

f = open(rifdock_outputs_file)
lines = f.readlines()
f.close()

rifdock_outputs = []
unique_scaffolds = {}
unique_scaffolds_order = []

for line in lines:
    line = line.strip()
    if (len(line) == 0):
        continue
    rifdock_outputs.append(line)

    base = os.path.basename(line)
    scaffold = re.match("(.*)_[0-9]{9}.pdb(.gz)?", base).group(1)

    if (scaffold not in unique_scaffolds):
        unique_scaffolds[scaffold] = True
        unique_scaffolds_order.append(scaffold)

scaffolds_list = os.path.join(tmp, "scaffolds.list")
f = open(scaffolds_list, "w")
for scaffold in unique_scaffolds_order:
    f.write("%s\n"%scaffold)
f.close()


# step 2, get data for starting scaffolds


gabe_scores = "/home/bcov/sc/random/scaffold_score_per_res/hts_verified_jan17/to_add_lengths.sc.converted"
want_from_gabe = ["AlaCount", "p_aa_pp", "score_per_res", "res_count_monomer", "description"]

f = open(gabe_scores)
lines = f.readlines()
f.close()

headers = lines[0].strip()
sp = headers.split()

new_headers = []
wanted_cols = []
for want in want_from_gabe:
    wanted_cols.append(sp.index(want) + 1)
    new_headers.append("og_" + want + " ")
new_headers.pop()
new_headers.append("name1")

awk_string = ",".join("$%i"%x for x in wanted_cols)

history_file1 = "diversify_scores.history"
f = open(history_file1, "w")
f.write(" ".join(new_headers) + "\n")
f.close()

out = cmd("cat %s | parallel 'grep \"{}\" %s' | awk '{print %s}' >> %s"%(scaffolds_list, gabe_scores, awk_string, history_file1)).strip()
if (len(out) != 0):
    print out
    sys.exit(1)


# step 3, get data for og docks

og_packscores = os.path.join(tmp, "packscores.dat")
f = open(og_packscores, "w")
f.write("packscore description\n")
f.close()

out = cmd("for j in $(cat %s); do echo $(basename $j); done | parallel 'grep \"{}\" %s' | awk '{print $9,$17}' >> %s"%
    (rifdock_outputs_file, all_og_dok_file, og_packscores)).strip()
if (len(out) != 0):
    print out
    sys.exit(1)


out = cmd("%s %s %s 0 0 12 17"%(add_new_scores_to_history, history_file1, og_packscores)).strip()
if (len(out) != 0):
    print out
    sys.exit(1)


history_file2 = cmd("ls -tr *.history").strip().split()[-1]


# step 4, get data for div docks

score_folder = os.path.join(monomer_stabilize_fol, "scores")
div_packscores = os.path.join(tmp, "div_packscores.dat")

f = open(div_packscores, "w")
f.write("div_packscore description\n")
f.close()

out = cmd("cat %s/*.dok* | awk '{print $9,$18}' >> %s"%(score_folder, div_packscores)).strip()
if (len(out) != 0):
    print out
    sys.exit(1)


out = cmd("%s %s %s 12 7 0 13"%(add_new_scores_to_history, history_file2, div_packscores)).strip()
if (len(out) != 0):
    print out
    sys.exit(1)


history_file3 = cmd("ls -tr *.history").strip().split()[-1]


# step 5, get monomer stability scores

monomer_scores_want = ["AlaCount", "mismatch_probability", "p_aa_pp", "score_per_res", "description"]

monomer_combined_sc = os.path.join(monomer_stabilize_fol, "combined.sc")
assert(os.path.exists(monomer_combined_sc))

f = open(monomer_combined_sc)
lines = f.readlines()
f.close()

headers = lines[0].strip()
sp = headers.split()

new_headers = []
wanted_cols = []
for want in monomer_scores_want:
    wanted_cols.append(sp.index(want) + 1)
    new_headers.append("mon_" + want + " ")

awk_string = ",".join("$%i"%x for x in wanted_cols)

monomer_score_dat = os.path.join(tmp, "monomer_score.dat")
f = open(monomer_score_dat, "w")
f.write(" ".join(new_headers) + "\n")
f.close()

out = cmd("cat %s | tail -n+2 | awk '{print %s}' >> %s"%(monomer_combined_sc, awk_string, monomer_score_dat)).strip()
if (len(out) != 0):
    print out
    sys.exit(1)


out = cmd("%s %s %s 0 4 0 5"%(add_new_scores_to_history, history_file3, monomer_score_dat)).strip()
if (len(out) != 0):
    print out
    sys.exit(1)


history_file4 = cmd("ls -tr *.history").strip().split()[-1]


# step 5, get ppi scores

ppi_scores_want = ["ddg", "interface_buried_sasa", "interface_sc", "interface_sc_int_area",
                   "new_buns_all_heavy", "p_aa_pp", "score_per_res", "description"]

assert(os.path.exists(ppi_scores_file))

f = open(ppi_scores_file)
lines = f.readlines()
f.close()

header_line = -1
sp = []
while (len(sp) < 2):
    header_line += 1
    headers = lines[header_line].strip()
    sp = headers.split()

new_headers = []
wanted_cols = []
for want in ppi_scores_want:
    wanted_cols.append(sp.index(want) + 1)
    new_headers.append( want + " ")

awk_string = ",".join("$%i"%x for x in wanted_cols)

ppi_score_dat = os.path.join(tmp, "ppi_score.dat")
f = open(ppi_score_dat, "w")
f.write(" ".join(new_headers) + "\n")
f.close()

out = cmd("cat %s | tail -n+%i | awk '{print %s}' >> %s"%(ppi_scores_file, header_line + 2, awk_string, ppi_score_dat)).strip()
if (len(out) != 0):
    print out
    sys.exit(1)


out = cmd("%s %s %s 0 0 9 6"%(add_new_scores_to_history, history_file4, ppi_score_dat)).strip()
if (len(out) != 0):
    print out
    sys.exit(1)


history_file5 = cmd("ls -tr *.history").strip().split()[-1]





