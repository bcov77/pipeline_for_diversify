#!/usr/bin/env python

import os
import sys
import re
import subprocess

from pyrosetta import *
from pyrosetta.rosetta import *

init("-mute all")

out_fol = "before_ppi" #sys.argv[1]
output_file = sys.argv[1]
in_pdbs = sys.argv[2:]

def cmd(command, wait=True):
    # print ""
    # print command
    the_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (not wait):
        return
    the_stuff = the_command.communicate()
    return the_stuff[0] + the_stuff[1]

if (not os.path.exists(out_fol)):
    os.mkdir(out_fol)

scorefxn = get_fa_scorefxn()

rifres_sel = core.select.residue_selector.ResiduePDBInfoHasLabelSelector("RIFRES")
align_sel = core.select.residue_selector.PrimarySequenceNeighborhoodSelector(3, 3, rifres_sel)

created_pdbs = []
for in_pdb in in_pdbs:
    pdb_fol = os.path.dirname(in_pdb)
    pdb_name = os.path.basename(in_pdb)
    print pdb_name

    files = os.listdir(pdb_fol)

    og_dock_pdb = ""

    for file in files:
        if (re.match(".*[0-9]{9}.*[0-9]{9}.*", file) != None):
            assert(og_dock_pdb == "")
            og_dock_pdb = file

    assert(og_dock_pdb != "")

    scaffold = pose_from_file(in_pdb)
    og_dock = pose_from_file(os.path.join(pdb_fol, og_dock_pdb))

    og_split = og_dock.split_by_chain()
    og_monomer = og_split[1]
    og_target = og_split[2]


    align_sub = rifres_sel.apply(scaffold)
    align_res = core.select.get_residues_from_subset(align_sub)

    rmsd = protocols.toolbox.pose_manipulation.superimpose_pose_on_subset_CA( 
    scaffold, og_monomer, align_res, 0 )
    print "Aligned rmsd: %.3f"%rmsd

    scaffold.append_pose_by_jump(og_target, 1)

    out_name = pdb_name.rstrip(".gz").rstrip(".pdb")
    out_name += "d"
    out_name += ".pdb.gz"

    out_pdb = os.path.join(out_fol, out_name)
    scaffold.dump_pdb(out_pdb)

    created_pdbs.append(out_pdb)



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
for created_pdb in created_pdbs:
    f.write("%s\n"%(created_pdb))
close_atomic(f, output_file)








