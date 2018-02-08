#!/usr/bin/env python


import os
import sys
import itertools
import subprocess

from pyrosetta import *
from pyrosetta.rosetta import *

init("-mute all")

output_file = sys.argv[1]
the_dock = sys.argv[2]
fragments = int(sys.argv[3])
# the_scaffold = sys.argv[2]
output_folder = "docks"

gabe_scaff_path = "/home/bcov/from/gabe/hts_verified_jan17/"
if (os.path.exists("/suppscr")):
    gabe_scaff_path = gabe_scaff_path.replace("/home/bcov", "/suppscr/baker/bcov")


def cmd(command, wait=True):
    # print ""
    # print command
    the_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (not wait):
        return
    the_stuff = the_command.communicate()
    return the_stuff[0] + the_stuff[1]


the_scaffold = cmd("find %s -iname $(basename %s | sed 's/_000000000.pdb.gz//g')*"%(
    gabe_scaff_path, the_dock)).strip()


if (not os.path.exists(output_folder)):
    try:
        os.mkdir(output_folder)
    except:
        pass

dock_base = os.path.basename(the_dock).rstrip(".gz").rstrip(".pdb")


dock = pose_from_file(the_dock)
scaffold = pose_from_file(the_scaffold)

scaffold_ress = utility.vector1_unsigned_long()
for i in range(1, scaffold.size() + 1):
    scaffold_ress.append(i)

aligned_rmsd = protocols.toolbox.pose_manipulation.superimpose_pose_on_subset_CA( 
    scaffold, dock, scaffold_ress, 0 )

if (aligned_rmsd > 1):
    print "Error!!!! Aligned RMSD = %.3f"%aligned_rmsd




chainA = core.select.residue_selector.ChainSelector("A")
chainB = core.select.residue_selector.ChainSelector("B")

scorefxn = get_fa_scorefxn()
scorefxn(dock)

on_A = core.select.residue_selector.NeighborhoodResidueSelector(
        chainB, 9, False )
to_modify = core.select.residue_selector.PrimarySequenceNeighborhoodSelector(
    3, 3, on_A)

subset = to_modify.apply(dock)

monomer_size = dock.split_by_chain()[1].size()
assert(monomer_size == scaffold.size())

to_remove = [1, monomer_size - 1, monomer_size]

for item in to_remove:
    subset[item] = False

residues = core.select.get_residues_from_subset(subset)

print "+".join([str(x) for x in residues])




dssp = core.scoring.dssp.Dssp(scaffold)
ss = dssp.get_dssp_secstruct()

ss_elements = []

element_start = 1
for ss_type, iterr in itertools.groupby(ss):
    length = len(list(iterr))
    end = element_start + length - 1
    ss_elements.append([ss_type, element_start, end, length])
    element_start += length

print ss_elements

motifs = ["HLE", "ELH", "ELE"]

good_motifs = []

for i in range(len(ss_elements)):
    these_three = ""
    for j in range(3):
        if (i+j >= len(ss_elements)):
            break
        these_three += ss_elements[i+j][0]
    if (these_three not in motifs):
        continue

    ss0 = ss_elements[i+0]
    ss1 = ss_elements[i+1]
    ss2 = ss_elements[i+2]
    end_of_0 = ss0[2]
    start_of_2 = ss2[1]

    all_good = True
    for seq_pos in range(end_of_0, start_of_2+1):
        if (not subset[seq_pos]):
            all_good = False
            break

    if (not all_good):
        continue

    good_motifs.append([these_three, ss0, ss1, ss2])
    # print these_three


created_directories = []

for these_three, ss0, ss1, ss2 in good_motifs + [["XXX", "", "", ""]]:
    starts = []

    if (these_three[0] == "E"):
        ss0_start = ss0[1]
        starts.append(ss0_start - 1)
        starts.append(ss0_start)
        starts.append(ss0_start + 1)
        starts.append(ss0_start + 2)

    if (these_three[0] == "H"):
        ss0_end = ss0[2]
        starts.append(ss0_end - 1 )
        starts.append(ss0_end )
        starts.append(ss0_end + 1)

    use_starts = []
    for start in starts:
        try:
            if (subset[start]):
                use_starts.append(start)
        except:
            pass

    ends = []
    if (these_three[2] == "E"):
        ss2_end = ss2[2]
        ends.append(ss2_end - 2)
        ends.append(ss2_end - 1)
        ends.append(ss2_end)
        ends.append(ss2_end + 1)

    if (these_three[2] == "H"):
        ss2_start = ss2[1]
        ends.append(ss2_start - 1)
        ends.append(ss2_start)
        ends.append(ss2_start + 1)

    use_ends = []
    for end in ends:
        try:
            if (subset[end]):
                use_ends.append(end)
        except:
            pass

    if (these_three == "XXX"):
        starts = [-1, -1]
        ends = [-1, -1]

    earliest_start = min(starts)
    latest_end = max(ends)
    extra_name = "_%02i-%02i"%(earliest_start, latest_end)

###################
    if (earliest_start == -1):
        extra_name = "_ctrl_"


    this_name = dock_base + extra_name

    this_fol = os.path.join(output_folder, this_name)
    if (os.path.exists(this_fol)):
        print "%s exists"%this_name
        continue
    else:
        os.mkdir(this_fol)

    created_directories.append(this_fol)


    cmd("cp pipeline_files/rifdock_inputs/input_files/* %s"%this_fol)
    rifgen = cmd("readlink -f pipeline_files/rifdock_inputs/rifgen_*").strip()
    assert(len(rifgen) > 0)
    rifgen_base = os.path.basename(rifgen)
    cmd("ln -s %s %s"%(rifgen, os.path.join(this_fol, rifgen_base)))

    scaffold_name = dock_base + "_og.pdb"

    f = open(os.path.join(this_fol, "morph.flag"), "w")
    f.write("-tether_to_input_position 5\n")
    f.write("-scaffolds %s\n"%scaffold_name)
    if (earliest_start != -1):
        f.write("-scaff_search_mode morph_dive_pop\n")
        f.write("-max_insertion 0\n")
        f.write("-max_deletion 0\n")
        f.write("-indexed_structure_store:fragment_store /home/bcov/from/alex/vall.h5\n")
        f.write("-fragment_cluster_tolerance 0.2\n")
        f.write("-max_fragments %i\n"%fragments)
        f.write("-fragment_max_rmsd 4\n")
        f.write("-match_this_rmsd 2\n")
        f.write("-dive_resl 6\n")
        f.write("-pop_resl 5\n")
        f.write("-match_this_pdb %s\n"%scaffold_name)
        f.write("-low_cut_site %i\n"%(earliest_start+1))
        f.write("-high_cut_site %i\n"%(latest_end-1))
        f.write("-use_parent_body_energies true\n")
        f.write("-include_parent\n")
        f.write("-max_beam_multiplier 1000000\n")
        f.write("-morph_rules_files binder.morph_rules\n")

    f.close()

    scaffold.dump_pdb(os.path.join(this_fol, scaffold_name))


    if (earliest_start != -1):
        f = open(os.path.join(this_fol, "binder.morph_rules"), "w")


        for start, end in list(itertools.product(use_starts, use_ends)):
            print "select resi " + "+".join(str(x) for x in range(start, end+1))
            f.write("S: %i %i 0 0 %i\n"%(start+1, end-1, fragments))

        f.close()
    
    cmd("sed -i 's^/home/bcov^/suppscr/baker/bcov^g' %s"%os.path.join(this_fol, "*.flag"))


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
if (len(created_directories) > 0):
    for directory in created_directories:
        f.write("%s\n"%(directory))
else:
    f.write("-")
close_atomic(f, output_file)



