import sys,os
from pmx import *
from pmx.options import *
from pmx.parser import *
from pmx import library
from pmx.mutdb import *
from pmx.geometry import *
from pmx.builder import *

def create_mdp( fname ):
    fp = open(fname,'w')
    fp.write('''
define                  = 
integrator              = steep
emtol                   = 1000.0
nsteps                  = 10000
nstlist                 = 10
cutoff-scheme           = Verlet
rlist                   = 1.2
vdwtype                 = Cut-off
rvdw                    = 1.2
coulombtype             = cutoff
rcoulomb                = 1.2
constraints             = none\n''')
    fp.close()

# identify atoms to be removed and an offset 
def identify_atoms_to_remove( topol, firstResNum=1, lastResNum=2 ):
    removeID = []
    offset = 0
    for a in topol.atoms:
        if a.resnr==firstResNum:
            removeID.append(a.id)
            offset+=1
        if a.resnr==lastResNum:
            removeID.append(a.id)
    return(removeID,offset)

# remove atoms and apply offset
def remove_atoms( topol, removeID ):
    # atoms
    rem = []
    for a in topol.atoms:
        if a.id in removeID:
            rem.append(a)
    for r in rem:
        topol.atoms.remove(r)

    # bonds
    rem = []
    for b in topol.bonds:
        if (b[0].id in removeID) or (b[1].id in removeID):
            rem.append(b)
    for r in rem:
        topol.bonds.remove(r)

    # pairs
    rem = []
    for p in topol.pairs:
        if (p[0].id in removeID) or (p[1].id in removeID):
            rem.append(p)
    for r in rem:
        topol.pairs.remove(r)

    # angles
    rem = []
    for a in topol.angles:
        if (a[0].id in removeID) or (a[1].id in removeID) or (a[2].id in removeID):
            rem.append(a)
    for r in rem:
        topol.angles.remove(r)

    # dihedrals
    rem = []
    for d in topol.dihedrals:
        if (d[0].id in removeID) or (d[1].id in removeID) or (d[2].id in removeID) or (d[3].id in removeID):
            rem.append(d)
    for r in rem:
        topol.dihedrals.remove(r)
  
# renumber atoms in the topology 
def renumber_atoms( topol, offset ):
    # atoms 
    for a in topol.atoms:
        a.id -= offset
        a.cgnr -= offset
        a.resnr -= 1       

# remove residues from topology
def remove_residues( topol ):
    del topol.residues[0]
    del topol.residues[-1]

# add a bond to close the cycle
def add_bond( topol ):
    firstResNum = 1
    lastResNum = len(topol.residues)
    # identify two atoms
    a1 = ''
    a2 = ''
    for a in topol.atoms:
        if a.resnr==firstResNum and a.name=='N':
            a1 = a
        if a.resnr==lastResNum and a.name=='C':
            a2 = a
    # create and add a bond
    newb = [a1,a2,1]
    topol.bonds.insert(0,newb)

    ###### now 1-4 ######
    # create a dictionary of bonded partners for each atom: dict[atom] = [a1,a2,a3,...]
    partners = {}
    for b in topol.bonds:
        if b[0] in partners.keys():
            partners[b[0]].append(b[1])
        else:
            partners[b[0]] = [b[1]]
        if b[1] in partners.keys():
            partners[b[1]].append(b[0])
        else:
            partners[b[1]] = [b[0]]

    # go over bonds and identify 1-4 interactions for a1 and a2 atoms
    pairs = []
    list13 = []
    # atom 1 
    parse14( pairs, list13, a1, partners, topol )
    # atom 2
    parse14( pairs, list13, a2, partners, topol )
    # also partners of a1
    for a in partners[a1]:
        if a!=a2:
            parse14( pairs, list13, a, partners, topol )
    # also partners of a2
    for a in partners[a2]:
        if a!=a1:
            parse14( pairs, list13, a, partners, topol )
    # append
    for p in pairs:
        if [p[0],p[1]] not in list13:
            topol.pairs.append(p)

def parse14( pairs, list13, a, partners, topol ):
    for a12 in partners[a]:
        for a13 in partners[a12]:
            if a13==a:
                continue
            list13.append( [a,a13] )
            list13.append( [a13,a] )
            for a14 in partners[a13]:
                if a12==a14 or a==a14:
                    continue
                p = [a,a14,1]
                pinv = [a14,a,1]
                if (p in pairs) or (pinv in pairs):
                    continue
                if (p in topol.pairs) or (pinv in topol.pairs):
                    continue
                pairs.append(p)

def main(argv):

   options=[
   Option( "-seq", "string", "PVWLVVV" , "peptide sequence"),
   Option( "-chir", "string", "LDLDLDL" , "peptide sequence"),
        ]
    
   files = [
#       FileOption("-seq", "string",[""],"protein.pdb", "input structure of a cyclic peptide"),
       FileOption("-o", "w",["pdb","gro"],"out.pdb", "output structure file"),
       FileOption("-p", "w",["top"],"topol.top", "output topology file"),
       ]
    
   help_text = ('The script builds a cyclic peptide top for gromacs',
                'based on https://github.com/visvaldask/gmx_makecyclictop',
               )

    
   cmdl = Commandline( argv, options = options,
                       fileoptions = files,
                       program_desc = help_text,
                       check_for_existing_files = False )
    
#   iname = cmdl['-f']
   oname = cmdl['-o']
   otopname = cmdl['-p']
#   ff = cmdl['-ft']

   # 1. construct the peptide, e.g XYZ
   m = build_chain(cmdl['-seq'],bCyclic=True,chirality=cmdl['-chir'])
   seq = cmdl['-seq']
#   print(seq)

   # 2. add termini, e.g. ZXYZX
   extendedSeq = seq[-1]+seq+seq[0]
#   print(extendedSeq) 
   # take first and last residues
   first_res = m.residues[0].copy()
   last_res = m.residues[-1].copy()
   # append them (there will be overlaps, these residues are just dummy appends)
   m.append(first_res)
   m.insert_residue(0,last_res)
   m.write(oname)

   # 3. pdb2gmx
   cmd = 'gmx pdb2gmx -f out.pdb -ff amber99sb-star-ildn -water tip3p -o out.pdb'
   os.system(cmd)
   # clean after
   cmd = 'rm *# posre.itp'
   os.system(cmd)

   # 4. modify the topology
   topol = Topology( 'topol.top',  version = 'new', assign_types=False )
   removeID,offset = identify_atoms_to_remove( topol, firstResNum=1, lastResNum=len(m.residues) )
   remove_atoms( topol, removeID )   
   renumber_atoms( topol, offset )
   remove_residues( topol )
   add_bond( topol )

   # 5. modify the structure: remove first and last residues
   # read the structure from pdb2gmx
   m = Model( 'out.pdb' )
   # get the first and last residues anew
   last_res = m.fetch_residue( len(m.residues) )
   m.remove_residue( last_res )
   first_res = m.fetch_residue( 1 )
   m.remove_residue( first_res )

   # output
   topol.write(otopname)
   m.write(oname)#,bPDBTER=True)

   # 6. minimize
   os.system('mkdir em')
   os.chdir('em')
   # box
   cmd = 'gmx editconf -f ../out.pdb -o box.pdb -bt cubic -box 3 3 3'
   os.system(cmd)
   # grompp
   create_mdp( 'em.mdp' )
   cmd = 'gmx grompp -p ../topol.top -c box.pdb -f em.mdp -o em.tpr'
   os.system(cmd)
   # mdrun
   mdrun = '/usr/local/gromacs/2021/2021.2-impi2017-fftw337-gcc93-cuda11.1/bin/mdrun_threads'
#   mdrun = 'gmx mdrun'
   cmd = '{0} -s em.tpr -c minimized.pdb -v -ntomp 1 -ntmpi 1'.format(mdrun)
   os.system(cmd)
   # clean after
   cmd = 'rm *# md.log mdout.mdp *xtc *trr *edr'
   os.system(cmd)


if __name__=='__main__':
    main(sys.argv)

