#!/usr/bin/env python

# The purpose of this program is to take a folder where RifDock was run and to grab the first X designs
#  and determine which residues need to be repacked in order to stabilize.
#  Then make an output folder with nested inner folders that contain the complex, and the monomer,
#  and a list of residues to design

# input: scaffold.pdb out_fol in_fol...

import os
import sys
import re
import subprocess
import stat

from pyrosetta import *
from pyrosetta.rosetta import *

init("-mute all")

xml = "pipeline_files/pipe_monomer_design1.xml"
designs_to_grab = 3

out_fol = "monomer_stabilize" #sys.argv[1]
output_file = sys.argv[1]
in_fols = sys.argv[2:]


def cmd(command, wait=True):
    # print ""
    # print command
    the_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (not wait):
        return
    the_stuff = the_command.communicate()
    return the_stuff[0] + the_stuff[1]

xml = cmd("readlink -f %s"%xml).strip()

if (not os.path.exists(out_fol)):
    os.mkdir(out_fol)
score_fol = os.path.join(out_fol, "scores")
if (not os.path.exists(score_fol)):
    os.mkdir(score_fol)

created_folders = []

for in_fol in in_fols:
    in_fol_base = os.path.basename(in_fol)
    rifdock_out = os.path.join(in_fol, "rifdock_out")

    scaffold_pdb = os.path.join(in_fol, cmd("grep 'scaffolds' %s/morph.flag | awk '{print $2}'"%in_fol).strip())

    scorefxn = get_fa_scorefxn()
    scaffold = pose_from_file(scaffold_pdb)

    num_alanines = 0
    for i in range(scaffold.size()):
        i += 1
        if (scaffold.residue(i).name1() == "A"):
            num_alanines += 1



    all_dock = cmd("ls %s/*dok*"%rifdock_out).strip().split("\n")[-1].strip()





    try:
        f = open(all_dock)
        lines = f.readlines()
        f.close()
    except:
        print "No results for:" + in_fol
        continue

    good_full_lines = []
    good_lines = []
    for line in lines: 
        line = line.strip()
        if (len(line) == 0):
            continue
        sp = line.split()
        good_lines.append(sp)
        good_full_lines.append(line)

        if (len(good_lines) == designs_to_grab):
            break

    ctrl = False
    matches = re.match(".*?([0-9]{2})-([0-9]{2})", in_fol)
    try:
        cut_low = int(matches.group(1))
        cut_high = int(matches.group(2))
    except:
        assert("ctrl" in in_fol)
        ctrl = True
        cut_low = 5
        cut_high = 6


    score_file = os.path.join(score_fol, in_fol_base + ".dok")
    g = open(score_file, "w")


    range_sel = core.select.residue_selector.ResidueIndexSelector("%i-%i"%(cut_low, cut_high))
    neighbors = core.select.residue_selector.NeighborhoodResidueSelector(range_sel, 7, True)

    layers = core.select.residue_selector.LayerSelector()
    layers.set_layers(True, True, False)

    restricted_neighbors = core.select.residue_selector.AndResidueSelector(neighbors, layers)
    design_sel = core.select.residue_selector.OrResidueSelector(restricted_neighbors, range_sel)

    for desno in range(min(designs_to_grab, len(good_lines))):
        name = in_fol_base + "_%i"%desno
        fol = os.path.join(out_fol, name)

        dok = good_lines[desno]
        dock_path = os.path.join(in_fol, dok[16])
        assert(os.path.exists(dock_path))

        monomer_name = name + "_.pdb"
        monomer_path = os.path.join(fol, monomer_name)

        g.write(good_full_lines[desno] + " " + monomer_name + "\n")

        if (os.path.exists(fol)):
            print name + " exists!!!"
            continue
        else:
            os.mkdir(fol)

        created_folders.append(fol)

        cmd("cp %s %s"%(dock_path, fol))
        cmd("zgrep ' A ' %s > %s"%(dock_path, monomer_path))
        cmd("zgrep 'RIFRES' %s >> %s"%(dock_path, monomer_path))


        monomer = pose_from_file(monomer_path)
        scorefxn(monomer)

        design_sub = design_sel.apply(monomer)

        energies = monomer.energies()
        pdb_info = monomer.pdb_info()
        for i in range(monomer.size()):
            i += 1
            fa_rep = energies.residue_total_energies(i)[core.scoring.fa_rep]
            if (fa_rep > 5):
                design_sub[i] = True

            if (pdb_info.res_haslabel(i, "RIFRES") and not pdb_info.res_haslabel(i, "PRUNED") 
                and not monomer.residue(i).name1() == "A"):
                design_sub[i] = False

            if (ctrl):
                design_sub[i] = False
        
        to_design = core.select.get_residues_from_subset(design_sub)
        if (ctrl):
            to_design.append(1000)

        f = open(os.path.join(fol, "to_design.list"), "w")
        f.write(",".join(str(x) for x in to_design))
        f.close()

        f = open(os.path.join(fol, "ala.comp"), "w")
        f.write("PENALTY_DEFINITION\n")
        f.write("TYPE ALA\n")
        f.write("ABSOLUTE %i\n"%num_alanines)
        f.write("PENALTIES 0 0 4 8 \n")
        f.write("DELTA_START -1\n")
        f.write("DELTA_END 2\n")
        f.write("BEFORE_FUNCTION CONSTANT\n")
        f.write("AFTER_FUNCTION QUADRATIC\n")
        f.write("END_PENALTY_DEFINITION\n")
        f.close()


        full_fol = cmd("readlink -f %s"%fol).strip()

        gen_name = fol + "/command.sh"
        f = open(gen_name, "w")

        f.write("#!/bin/bash\n")
        # f.write("#SBATCH -p medium\n")
        f.write("#SBATCH --mem=5g\n")
        f.write("#SBATCH -o %s/log2.log\n"%full_fol)
        f.write("#SBATCH -n 1\n")
        f.write("#SBATCH -N 1\n")
        f.write("cd %s\n"%full_fol)
        # f.write("/home/bcov/rifdock/scheme/build/apps/rosetta/rif_dock_test @rifdock_v4.flags -scaffolds $1 > phase2.log\n")
        f.write("/software/rosetta/latest/bin/rosetta_scripts -ex1 -ex2aro -s %s -aa_composition_setup_file ala.comp -parser:protocol %s -parser:script_vars design_res=$(cat to_design.list) > command.log\n"
            %(monomer_name, xml))

        f.close()


        st = os.stat(gen_name)
        os.chmod(gen_name, st.st_mode | stat.S_IEXEC)





    g.close()



def make_temp_filename(filename):
    return filename + ".tmp"

def open_atomic(filename):
    tmp = make_temp_filename(filename)
    return open(tmp, "w")

def close_atomic(handle, filename):
    handle.close()
    tmp = make_temp_filename(filename)
    os.rename(tmp, filename)


f = open_atomic(output_file)
if (len(created_folders) > 0):
    for directory in created_folders:
        f.write("%s\n"%(directory))
else:
    f.write("-")
close_atomic(f, output_file)



