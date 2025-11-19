# masgent/ai_mode/tools.py

import os
import warnings
import datetime
from ase.build import bulk
from ase.io import write
from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

from masgent.utils import os_path_setup
from masgent.ai_mode.schemas import GenerateSimplePOSCARSchema

# Do not show warnings
warnings.filterwarnings('ignore')

def generate_simple_poscar(input: GenerateSimplePOSCARSchema) -> str:
    '''Creating a simple bulk POSCAR
    Pure execution tool.

    Must ALWAYS return a STRING.

    Success → return a human-readable message string.

    Failure → return error message string.
    '''
    print(f'[Debug: Function Calling] generate_simple_poscar with input: {input}')

    name = input.name
    crystalstructure   = input.crystalstructure
    a    = input.a
    b    = input.b
    c    = input.c
    alpha = input.alpha
    generate_vasp_inputs = input.generate_vasp_inputs

    try:
        base_dir, target_dir = os_path_setup()
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        save_dir = os.path.join(target_dir, f"{name}_{timestamp}")
        os.makedirs(save_dir, exist_ok=True)

        atoms = bulk(
            name=name,
            crystalstructure=crystalstructure,
            a=a,
            b=b,
            c=c,
            alpha=alpha,
        )
        write(os.path.join(save_dir, 'POSCAR'), atoms, format='vasp')

        if generate_vasp_inputs:
            structure = Structure.from_file(os.path.join(save_dir, 'POSCAR'))
            vis = MPRelaxSet(structure)
            vis.write_input(save_dir)

        msg = f'\nGenerated POSCAR in {save_dir}.'
        if generate_vasp_inputs:
            msg += ' VASP input files (INCAR, KPOINTS, POTCAR) generated.'

        return msg

    except Exception as e:
        return f'\nPOSCAR generation failed: {str(e)}'