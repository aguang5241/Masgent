import os
import warnings
import datetime
from ase.build import bulk
from ase.io import write
from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

from masgent.utils import os_path_setup

# Do not show warnings
warnings.filterwarnings('ignore')

def generate_simple_poscar(
        name: str = 'Cu',
        crystalstructure: str = 'fcc',
        a: float = None,
        b: float = None,
        c: float = None,
        alpha: float = None,
    ) -> str:
    '''Creating a simple bulk POSCAR file using ASE's bulk function.

    Before calling this tool, infer any missing or underspecified parameters from chemistry knowledge.
    
    If this tool return status "Error", analyze the message and call the tool again with corrected parameters.

    name: str
        Materials chemical formula, such as 'Cu', 'NaCl' or 'Al2O3'.
    crystalstructure: str
        Crystal structure type.
        Must be one of sc, fcc, bcc, tetragonal, bct, hcp, rhombohedral,
        orthorhombic, mcl, diamond, zincblende, rocksalt, cesiumchloride,
        fluorite or wurtzite.
    a: float
        Lattice constant in Angstroms
    b: float
        Lattice constant in Angstroms
    c: float
        Lattice constant in Angstroms
    alpha: float
        Angle in degrees for rhombohedral lattice.
    '''
    print(f'\n[Function Calling] generate_poscar( name={name}, crystalstructure={crystalstructure}, a={a}, b={b}, c={c}, alpha={alpha} )')

    # Set up directories
    target_dir = os_path_setup()[1]
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = os.urandom(4).hex()
    save_dir = os.path.join(target_dir, f'run_{timestamp}_{random_suffix}')
    os.makedirs(save_dir, exist_ok=True)
    print(f'\n[Info] Created directory: {save_dir}')

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
        write(os.path.join(save_dir, 'POSCAR'), atoms, format='vasp')

        # Let user to decide whether to generate other VASP inputs
        user_input = input(f'\n[Action Required] {name} POSCAR generated successfully. Do you want to generate standard VASP input files (INCAR, KPOINTS, POTCAR) now? (y/n): ').strip().lower()
        if user_input == 'y':
            structure = Structure.from_file(os.path.join(save_dir, 'POSCAR'))
            vis = MPRelaxSet(structure)
            vis.write_input(save_dir)
        
        print(f'\n[Info] Generated {name} POSCAR and standard VASP input files in {save_dir}.')
        return {
            'status': 'Success',
            'message': ''
        }
    
    except Exception as e:
        if os.path.exists(save_dir):
            os.rmdir(save_dir)
            print(f'\n[Info] Removed directory due to error: {save_dir}')
        
        return {
            'status': 'Error',
            'message': f'Failed to generate POSCAR, please provide more information. Error details: {e}'
        }

def generate_vasp_inputs_from_poscar() -> str:
    '''Generate standard VASP input files using pymatgen's MPRelaxSet from an existing POSCAR file in the base directory.
    '''
    print(f'[Function Calling: generate_vasp_inputs_from_poscar] Generating VASP input files from POSCAR...')
    base_dir, target_dir = os_path_setup()

    if not os.path.exists(os.path.join(target_dir, 'POSCAR')):
        return {
            'status': 'error',
            'message': f'POSCAR file not found in {target_dir}. Please generate POSCAR first.'
        }

    structure = Structure.from_file(os.path.join(target_dir, 'POSCAR'))
    vis = MPRelaxSet(structure)

    os.makedirs(target_dir, exist_ok=True)
    vis.write_input(target_dir)

    return {
        'status': 'success',
        'message': f'Generated VASP input files (INCAR, KPOINTS, POTCAR) from POSCAR and saved to {target_dir}.'
    }

