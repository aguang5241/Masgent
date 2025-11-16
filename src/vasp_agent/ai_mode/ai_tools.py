import os
import warnings
from ase.build import bulk
from ase.io import write
from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

from vasp_agent.utils import os_path_setup

# Do not show warnings
warnings.filterwarnings('ignore')

def generate_poscar(
        name: str = 'Cu',
        crystalstructure: str = 'fcc',
        a: float = None,
        b: float = None,
        c: float = None,
        alpha: float = None,
    ) -> str:
    '''Creating bulk systems.

    Before calling this tool, infer any missing or underspecified parameters from chemistry knowledge.
    
    If this tool return status "error", analyze the message and call the tool again with corrected parameters.

    name: str
        Chemical symbol or symbols as in 'MgO' or 'NaCl'.
    crystalstructure: str
        Must be one of sc, fcc, bcc, tetragonal, bct, hcp, rhombohedral,
        orthorhombic, mcl, diamond, zincblende, rocksalt, cesiumchloride,
        fluorite or wurtzite.
    a: float
        Lattice constant in Angstroms
    a: float
        Lattice constant.
    b: float
        Lattice constant.  If only a and b is given, b will be interpreted
        as c instead.
    c: float
        Lattice constant.
    alpha: float
        Angle in degrees for rhombohedral lattice.
    '''
    print(f'[Function Calling] generate_poscar( name={name}, crystalstructure={crystalstructure}, a={a}, b={b}, c={c}, alpha={alpha} )')

    # Set up directories
    target_dir = os_path_setup()[1]
    os.makedirs(target_dir, exist_ok=True)

    # Generate bulk structure and write POSCAR
    try:
        atoms = bulk(
            name=name,
            crystalstructure=crystalstructure,
            a=a,
            b=b,
            c=c,
            alpha=alpha,
        )
        write(os.path.join(target_dir, 'POSCAR'), atoms, format='vasp')
        return {
            'status': 'success',
            'message': f'Generated {crystalstructure} {name} POSCAR with a={a}, b={b}, c={c}, alpha={alpha} Angstroms and saved to {target_dir}/POSCAR.'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error generating POSCAR: {e}'
        }

def generate_vasp_inputs_from_poscar() -> str:
    '''Generate standard VASP input files using pymatgen's MPRelaxSet from an existing POSCAR file in the base directory.
    '''
    print(f'[Function Calling: generate_vasp_inputs_from_poscar] Generating VASP input files from POSCAR...')
    base_dir, target_dir = os_path_setup()

    if not os.path.exists(os.path.join(target_dir, 'POSCAR')):
        return f'No POSCAR file found in {target_dir}. Please provide a valid POSCAR file first or let the AI generate one for you.'

    structure = Structure.from_file(os.path.join(target_dir, 'POSCAR'))
    vis = MPRelaxSet(structure)

    os.makedirs(target_dir, exist_ok=True)
    vis.write_input(target_dir)

    return f'Generated VASP input files (INCAR, KPOINTS, POTCAR) from POSCAR and saved to {target_dir}.'

