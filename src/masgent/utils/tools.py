# !/usr/bin/env python3

# Do not show warnings
import os, warnings, random, shutil, re, joblib
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from typing import Literal, List
from pathlib import Path
from dotenv import load_dotenv
from ase.io import read, write
from pymatgen.core import Structure, Lattice
from pymatgen.io.vasp import Poscar, Kpoints, Vasprun
from pymatgen.io.vasp.sets import (
    MPStaticSet, 
    MPRelaxSet, 
    MPMetalRelaxSet,
    MPNonSCFSet, 
    MPMDSet,
    NEBSet,
    )

from masgent.utils import schemas
from masgent.utils.utils import (
    write_comments,
    ask_for_mp_api_key,
    validate_mp_api_key,
    generate_submit_script,
    generate_batch_script,
    list_files_in_dir,
    fit_eos,
    create_deformation_matrices,
    visualize_structure,
    )

# Track whether Materials Project key has been checked during this process
_mp_key_checked = False

def with_metadata(input: schemas.ToolMetadata):
    '''
    Decorator to add metadata to tool functions.
    '''
    def decorator(func):
        func._tool_metadata = input
        return func
    return decorator

@with_metadata(schemas.ToolMetadata(
    name='List Files',
    description='List all files in the current session runs directory.',
    requires=[],
    optional=[],
    defaults={},
    prereqs=[],
))
def list_files() -> dict:
    runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

    file_list = []
    base_dir = Path(runs_dir)
    for item in base_dir.rglob('*'):
        if item.is_file():
            file_list.append(os.path.join(runs_dir, str(item.relative_to(base_dir))))
    return {
        'status': 'success',
        'message': f'Found {len(file_list)} files in the current session runs directory.',
        'files': file_list,
    }

@with_metadata(schemas.ToolMetadata(
    name='Read File',
    description='Read a file from the current session runs directory.',
    requires=['name'],
    optional=[],
    defaults={},
    prereqs=[],
))
def read_file(name: str) -> dict:
    runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
    base_dir = Path(runs_dir)

    try:
        with open(base_dir / name, "r") as f:
            content = f.read()
        return {
            'status': 'success',
            'message': f'File {name} read successfully.',
            'content': content,
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'An error occurred while reading file {name}: {e}',
        }

@with_metadata(schemas.ToolMetadata(
    name='Rename File',
    description='Rename a file in the current session runs directory.',
    requires=['name', 'new_name'],
    optional=[],
    defaults={},
    prereqs=[],
))
def rename_file(name: str, new_name: str) -> dict:
    runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
    base_dir = Path(runs_dir)

    try:
        new_path = base_dir / new_name
        if not str(new_path).startswith(str(base_dir)):
            return {
                'status': 'error',
                'message': f'Renaming to {new_name} would move the file outside the session runs directory, which is not allowed.',
            }

        os.makedirs(new_path.parent, exist_ok=True)
        shutil.copy2(base_dir / name, new_path)
        return {
            'status': 'success',
            'message': f'File {name} renamed to {new_name} successfully.',
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'An error occurred while renaming file {name} to {new_name}: {e}',
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate POSCARs from Materials Project',
    description='Generate all possible POSCAR files from Materials Project database based on chemical formula, with the most stable structure saved as POSCAR by default and all matched structures saved in a separate folder.',
    requires=['formula'],
    optional=[],
    defaults={},
    prereqs=[],
))
def generate_vasp_poscar(formula: str) -> dict:
    '''
    Generate VASP POSCAR file from Materials Project database.
    '''
    try:
        schemas.GenerateVaspPoscarSchema(formula=formula)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        poscars_dir = os.path.join(runs_dir, f'POSCARs/{formula}')
        os.makedirs(poscars_dir, exist_ok=True)

        # Ensure Materials Project API key exists and validate it only once per process
        load_dotenv(dotenv_path='.env')

        global _mp_key_checked
        if not _mp_key_checked:
            if 'MP_API_KEY' not in os.environ:
                ask_for_mp_api_key()
            else:
                validate_mp_api_key(os.environ['MP_API_KEY'])
            _mp_key_checked = True
        
        from mp_api.client import MPRester
        with MPRester(mute_progress_bars=True) as mpr:
            docs = mpr.materials.summary.search(formula=formula)
            if not docs:
                return {
                    'status': 'error',
                    'message': f'No materials found in Materials Project database for formula: {formula}'
                }
            
        # Get all material_ids and their energy above hull
        mid_energy = {}
        for doc in docs:
            mid_energy[str(doc.material_id)] = doc.energy_above_hull
        # Sort by energy above hull
        sorted_mids = sorted(mid_energy.items(), key=lambda x: x[1])
        # Get the most stable structure
        mid_0 = sorted_mids[0][0]
        structure_0 = mpr.get_structure_by_material_id(mid_0, conventional_unit_cell=True)
        poscar_0 = Poscar(structure_0)
        # Save as POSCAR_{formula} and rewrite POSCAR
        poscar_0.write_file(os.path.join(runs_dir, 'POSCAR'), direct=True)
        poscar_0.write_file(os.path.join(runs_dir, f'POSCAR_{formula}'), direct=True)
        comments_0 = f'# (Most Stable) Generated by Masgent from Materials Project entry {mid_0}, crystal system: {docs[0].symmetry.crystal_system}, space group: {docs[0].symmetry.symbol}.'
        write_comments(os.path.join(runs_dir, 'POSCAR'), 'poscar', comments_0)
        write_comments(os.path.join(runs_dir, f'POSCAR_{formula}'), 'poscar', comments_0)
        
        # Save all matched structures in the poscars directory
        for doc in docs:
            mid = doc.material_id
            crystal_system = doc.symmetry.crystal_system
            space_group_symbol = doc.symmetry.symbol
            structure = mpr.get_structure_by_material_id(mid)
            poscar = Poscar(structure)

            # If "/" in space group symbol, replace with "_"
            space_group_symbol_ = space_group_symbol.replace('/', '_')
            poscar.write_file(os.path.join(poscars_dir, f'POSCAR_{crystal_system}_{space_group_symbol_}_{mid}'), direct=True)

            comments = f'# Generated by Masgent from Materials Project entry {mid}, crystal system: {crystal_system}, space group: {space_group_symbol}.'
            write_comments(os.path.join(poscars_dir, f'POSCAR_{crystal_system}_{space_group_symbol_}_{mid}'), 'poscar', comments)
        
        poscar_files = list_files_in_dir(poscars_dir) + [os.path.join(runs_dir, 'POSCAR')]
        
        return {
            'status': 'success',
            'message': f'Generated POSCAR(s) in {poscars_dir}.',
            'all_poscars': poscar_files,
            'most_stable_poscar': os.path.join(runs_dir, f'POSCAR_{formula}'),
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'POSCAR generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate VASP Inputs (INCAR, KPOINTS, POTCAR, POSCAR)',
    description='Generate VASP input files (INCAR, KPOINTS, POTCAR, POSCAR) from a given POSCAR file using pymatgen input sets (MPMetalRelaxSet, MPRelaxSet, MPStaticSet, MPNonSCFBandSet, MPNonSCFDOSSet, MPMDSet).',
    requires=['vasp_input_sets'],
    optional=['poscar_path', 'only_incar'],
    defaults={
        'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
        'only_incar': False,
        },
    prereqs=[],
))
def generate_vasp_inputs_from_poscar(
    vasp_input_sets: str,
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
    only_incar: bool = False
) -> dict:
    '''
    Generate VASP input files (INCAR, KPOINTS, POTCAR, POSCAR) from a given POSCAR file using pymatgen input sets.
    '''
    try:
        schemas.GenerateVaspInputsFromPoscar(
            poscar_path=poscar_path,
            vasp_input_sets=vasp_input_sets,
            only_incar=only_incar,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    VIS_MAP = {
        'MPMetalRelaxSet': MPMetalRelaxSet,
        'MPRelaxSet': MPRelaxSet,
        'MPStaticSet': MPStaticSet,
        'MPNonSCFBandSet': MPNonSCFSet,
        'MPNonSCFDOSSet': MPNonSCFSet,
        'MPMDSet': MPMDSet,
    }
    vis_class = VIS_MAP[vasp_input_sets]

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        vasp_inputs_dir = os.path.join(runs_dir, f'vasp_inputs/{vasp_input_sets}')
        os.makedirs(vasp_inputs_dir, exist_ok=True)

        structure = Structure.from_file(poscar_path)
        
        if vasp_input_sets == 'MPRelaxSet':
            vis = vis_class(structure, user_incar_settings={'ISMEAR': 0})
        elif vasp_input_sets == 'MPNonSCFDOSSet':
            vis = vis_class(structure, mode='uniform', nedos=5000)
        else:
            vis = vis_class(structure)

        if only_incar:
            vis.incar.write_file(os.path.join(vasp_inputs_dir, 'INCAR'))
            vis.poscar.write_file(os.path.join(vasp_inputs_dir, 'POSCAR'))
            incar_comments = f'# Generated by Masgent using {vasp_input_sets} set provided by Materials Project.'
            write_comments(os.path.join(vasp_inputs_dir, 'INCAR'), 'incar', incar_comments)
            return {
                'status': 'success',
                'message': f'Generated INCAR based on {vasp_input_sets} in {os.path.join(vasp_inputs_dir, "INCAR")}.',
            }
        
        vis.incar.write_file(os.path.join(vasp_inputs_dir, 'INCAR'))
        vis.poscar.write_file(os.path.join(vasp_inputs_dir, 'POSCAR'))
        vis.kpoints.write_file(os.path.join(vasp_inputs_dir, 'KPOINTS'))
        vis.potcar.write_file(os.path.join(vasp_inputs_dir, 'POTCAR'))

        incar_comments = f'# Generated by Masgent using {vasp_input_sets} set provided by Materials Project.'
        write_comments(os.path.join(vasp_inputs_dir, 'INCAR'), 'incar', incar_comments)
        poscar_comments = f'# Generated by Masgent using {vasp_input_sets} set provided by Materials Project.'
        write_comments(os.path.join(vasp_inputs_dir, 'POSCAR'), 'poscar', poscar_comments)
        kpoints_comments = f'# Generated by Masgent using {vasp_input_sets} set provided by Materials Project.'
        write_comments(os.path.join(vasp_inputs_dir, 'KPOINTS'), 'kpoints', kpoints_comments)
        
        return {
            'status': 'success',
            'message': f'Generated VASP input files based on {vasp_input_sets} in {vasp_inputs_dir}.',
            'incar_path': os.path.join(vasp_inputs_dir, 'INCAR'),
            'kpoints_path': os.path.join(vasp_inputs_dir, 'KPOINTS'),
            'potcar_path': os.path.join(vasp_inputs_dir, 'POTCAR'),
            'poscar_path': os.path.join(vasp_inputs_dir, 'POSCAR'),
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP input files generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate HPC Slurm Script',
    description='Generate HPC Slurm job submission script for VASP calculations.',
    requires=[],
    optional=['partition', 'nodes', 'ntasks', 'walltime', 'jobname', 'mail_type', 'mail_user', 'command'],
    defaults={
        'partition': 'normal',
        'nodes': 1,
        'ntasks': 8,
        'walltime': '01:00:00',
        'jobname': 'masgent_job',
        'command': 'srun vasp_std > vasp.out'
        },
    prereqs=[],
    ))
def generate_vasp_inputs_hpc_slurm_script(
    partition: str = 'normal',
    nodes: int = 1,
    ntasks: int = 8,
    walltime: str = '01:00:00',
    jobname: str = 'masgent_job',
    command: str = 'srun vasp_std > vasp.out'
) -> dict:
    '''
    Generate HPC Slurm job submission script for VASP calculations.
    '''
    try:
        schemas.GenerateVaspInputsHpcSlurmScript(
            partition=partition,
            nodes=nodes,
            ntasks=ntasks,
            walltime=walltime,
            jobname=jobname,
            command=command,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        scripts = f'''#!/bin/bash
#SBATCH --partition={partition}
#SBATCH --nodes={nodes}
#SBATCH --ntasks={ntasks}
#SBATCH --time={walltime}
#SBATCH --job-name={jobname}
#SBATCH --output={jobname}.out
#SBATCH --error={jobname}.err

# This Slurm script was generated by Masgent, customize as needed.
{command}
'''
        script_path = os.path.join(runs_dir, 'masgent_submit.sh')
        with open(script_path, 'w') as f:
            f.write(scripts)

        return {
            'status': 'success',
            'message': f'Generated Slurm script in {script_path}.',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Slurm script generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Convert Structure Format',
    description='Convert structure files between different formats (CIF, POSCAR, XYZ).',
    requires=['input_path', 'input_format', 'output_format'],
    optional=[],
    defaults={},
    prereqs=[],
))
def convert_structure_format(
    input_path: str,
    input_format: Literal['POSCAR', 'CIF', 'XYZ'],
    output_format: Literal['POSCAR', 'CIF', 'XYZ'],
) -> dict:
    '''
    Convert structure files between different formats (CIF, POSCAR, XYZ).
    '''
    try:
        schemas.ConvertStructureFormatSchema(
            input_path=input_path,
            input_format=input_format,
            output_format=output_format,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    format_map = {
        "POSCAR": "vasp",
        "CIF": "cif",
        "XYZ": "xyz"
    }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        convert_dir = os.path.join(runs_dir, 'convert')
        os.makedirs(convert_dir, exist_ok=True)

        atoms = read(input_path, format=format_map[input_format])
        filename_wo_ext = os.path.splitext(os.path.basename(input_path))[0]
        # Ignore the POSCAR, do not add extension
        if output_format == 'POSCAR':
            output_path = os.path.join(convert_dir, 'POSCAR')
        else:
            output_path = os.path.join(convert_dir, f'{filename_wo_ext}.{output_format.lower()}')
        write(output_path, atoms, format=format_map[output_format])

        return {
            'status': 'success',
            'message': f'Converted structure saved to {output_path}.',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Structure conversion failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Convert POSCAR Coordinates',
    description='Convert POSCAR between direct and cartesian coordinates.',
    requires=['to_cartesian'],
    optional=['poscar_path'],
    defaults={'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR'},
    prereqs=[],
))
def convert_poscar_coordinates(
    to_cartesian: bool,
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
) -> dict:
    '''
    Convert POSCAR between direct and cartesian coordinates.
    '''
    try:
        schemas.ConvertPoscarCoordinatesSchema(
            poscar_path=poscar_path,
            to_cartesian=to_cartesian,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        convert_dir = os.path.join(runs_dir, 'convert')
        os.makedirs(convert_dir, exist_ok=True)
        
        structure = Structure.from_file(poscar_path)
        poscar = Poscar(structure)
        poscar.write_file(os.path.join(convert_dir, 'POSCAR'), direct=not to_cartesian)
        coord_type = 'Cartesian' if to_cartesian else 'Direct'
        comments = f'# Generated by Masgent converted to {coord_type} coordinates.'
        write_comments(os.path.join(convert_dir, 'POSCAR'), 'poscar', comments)

        return {
            'status': 'success',
            'message': f'Converted POSCAR to {coord_type} coordinates in {os.path.join(convert_dir, "POSCAR")}.',
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'POSCAR coordinate conversion failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Customize KPOINTS',
    description='Customize VASP KPOINTS from POSCAR with specified accuracy level (Low, Medium, High, Custom).',
    requires=['accuracy_level'],
    optional=['poscar_path', 'custom_kppa', 'gamma_centered'],
    defaults={'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR', 'custom_kppa': None, 'gamma_centered': True},
    prereqs=[],
))
def customize_vasp_kpoints_with_accuracy(
    accuracy_level: Literal['Low', 'Medium', 'High', 'Custom'],
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
    custom_kppa: int = None,
    gamma_centered: bool = True,
) -> dict:
    '''
    Customize VASP KPOINTS from POSCAR with specified accuracy level.
    '''
    try:
        schemas.CustomizeVaspKpointsWithAccuracy(
            poscar_path=poscar_path,
            accuracy_level=accuracy_level,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    DENSITY_MAP = {
        'Low': 1000,
        'Medium': 3000,
        'High': 5000,
        'Custom': custom_kppa,
    }
    kppa = DENSITY_MAP[accuracy_level]

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        structure = Structure.from_file(poscar_path)
        kpts = Kpoints.automatic_density(structure, kppa=kppa).kpts[0]
        if gamma_centered:
            kpoints = Kpoints.gamma_automatic(kpts=kpts)
        else:
            kpoints = Kpoints.monkhorst_automatic(kpts=kpts)
        kpoints.write_file(os.path.join(runs_dir, 'KPOINTS'))
        comments = f'# Generated by Masgent with {accuracy_level} accuracy (Grid Density = {kppa} / number of atoms)'
        write_comments(os.path.join(runs_dir, 'KPOINTS'), 'kpoints', comments)
        
        return {
            'status': 'success',
            'message': f'Updated KPOINTS with {accuracy_level} accuracy in {os.path.join(runs_dir, "KPOINTS")}.',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP KPOINTS generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate Vacancy Defects',
    description='Generate VASP POSCAR with vacancy defects.',
    requires=['original_element', 'defect_amount'],
    optional=['poscar_path'],
    defaults={'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR'},
    prereqs=[],
))
def generate_vasp_poscar_with_vacancy_defects(
    original_element: str,
    defect_amount: float | int,
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
) -> dict:
    '''
    Generate VASP POSCAR with vacancy defects.
    '''
    try:
        schemas.GenerateVaspPoscarWithVacancyDefects(
            poscar_path=poscar_path,
            original_element=original_element,
            defect_amount=defect_amount,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        defect_dir = os.path.join(runs_dir, 'defects/vacancies')
        os.makedirs(defect_dir, exist_ok=True)
        
        atoms = read(poscar_path, format='vasp')

        all_indices = [i for i, atom in enumerate(atoms) if atom.symbol == original_element]
        if isinstance(defect_amount, float):
            num_defects = max(1, int(defect_amount * len(all_indices)))
        elif isinstance(defect_amount, int):
            num_defects = defect_amount

        vacancy_indices = random.sample(all_indices, num_defects)
        del atoms[vacancy_indices]

        write(os.path.join(defect_dir, 'POSCAR'), atoms, format='vasp', direct=True, sort=True)
        comments = f'# Generated by Masgent with vacancy defects of element {original_element} by randomly removing {num_defects} atoms, be careful to verify structure.'
        write_comments(os.path.join(defect_dir, 'POSCAR'), 'poscar', comments)

        # return f'\nGenerated POSCAR with vacancy defects in {os.path.join(target_dir, "POSCAR")}.'
        return {
            'status': 'success',
            'message': f'Generated POSCAR with vacancy defects in {os.path.join(defect_dir, "POSCAR")}.',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP POSCAR defect generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate Substitution Defects',
    description='Generate VASP POSCAR with substitution defects.',
    requires=['original_element', 'defect_element', 'defect_amount'],
    optional=['poscar_path'],
    defaults={'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR'},
    prereqs=[],
))
def generate_vasp_poscar_with_substitution_defects(
    original_element: str,
    defect_element: str,
    defect_amount: float | int,
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
) -> dict:
    '''
    Generate VASP POSCAR with substitution defects.
    '''
    try:
        schemas.GenerateVaspPoscarWithSubstitutionDefects(
            poscar_path=poscar_path,
            original_element=original_element,
            defect_element=defect_element,
            defect_amount=defect_amount,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        defect_dir = os.path.join(runs_dir, 'defects/substitutions')
        os.makedirs(defect_dir, exist_ok=True)
        
        atoms = read(poscar_path, format='vasp')

        all_indices = [i for i, atom in enumerate(atoms) if atom.symbol == original_element]
        if isinstance(defect_amount, float):
            num_defects = max(1, int(defect_amount * len(all_indices)))
        elif isinstance(defect_amount, int):
            num_defects = defect_amount

        substitution_indices = random.sample(all_indices, num_defects)
        for i in substitution_indices:
            atoms[i].symbol = defect_element
        
        write(os.path.join(defect_dir, 'POSCAR'), atoms, format='vasp', direct=True, sort=True)
        comments = f'# Generated by Masgent with substitution defect of element {original_element} to {defect_element} by randomly substituting {num_defects} atoms, be careful to verify structure.'
        write_comments(os.path.join(defect_dir, 'POSCAR'), 'poscar', comments)

        return {
            'status': 'success',
            'message': f'Generated POSCAR with substitution defects in {os.path.join(defect_dir, "POSCAR")}.',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP POSCAR defect generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate Interstitial (Voronoi) Defects',
    description='Generate VASP POSCAR with interstitial (Voronoi) defects.',
    requires=['defect_element'],
    optional=['poscar_path'],
    defaults={'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR'},
    prereqs=[],
))
def generate_vasp_poscar_with_interstitial_defects(
    defect_element: str,
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
) -> dict:
    '''
    Generate VASP POSCAR with interstitial (Voronoi) defects.
    '''
    try:
        schemas.GenerateVaspPoscarWithInterstitialDefects(
            poscar_path=poscar_path,
            defect_element=defect_element,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        defect_dir = os.path.join(runs_dir, 'defects/interstitials')
        os.makedirs(defect_dir, exist_ok=True)
        
        atoms = read(poscar_path, format='vasp')

        # Read atoms from ASE and convert to Pymatgen Structure
        from pymatgen.analysis.defects import generators

        structure = Structure.from_ase_atoms(atoms)
        interstitial_generator = generators.VoronoiInterstitialGenerator().generate(structure=structure, insert_species=[defect_element])
        defect_sites, defect_structures = [], []
        for defect in interstitial_generator:
            defect_sites.append(defect.site.frac_coords)
            defect_structures.append(defect.defect_structure)

        if len(defect_structures) == 0:
            return {
                'status': 'error',
                'message': f'No interstitial sites found for element {defect_element}.',
            }
        else:
            for i, defect_structure in enumerate(defect_structures):
                # Convert back to ASE Atoms for writing
                defect_atoms = defect_structure.to_ase_atoms()
                write(os.path.join(defect_dir, f'POSCAR_{i}'), defect_atoms, format='vasp', direct=True, sort=True)
                comments = f'# Generated by Masgent with interstitial (Voronoi) defect of element {defect_element} at fract. coords {defect_sites[i]}, be careful to verify structure.'
                write_comments(os.path.join(defect_dir, f'POSCAR_{i}'), 'poscar', comments)

        # return f'\nGenerated POSCAR with interstitial (Voronoi) defects in {target_dir}.'
        return {
            'status': 'success',
            'message': f'Generated POSCAR(s) with interstitial (Voronoi) defects in {defect_dir}.',
            'poscar_paths': [os.path.join(defect_dir, f'POSCAR_{i}') for i in range(len(defect_structures))],
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP POSCAR defect generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate Supercell',
    description='Generate supercell from POSCAR based on user-defined 3x3 scaling matrix.',
    requires=['scaling_matrix'],
    optional=['poscar_path'],
    defaults={'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR'},
    prereqs=[],
))
def generate_supercell_from_poscar(
    scaling_matrix: str,
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
) -> dict:
    '''
    Generate supercell from POSCAR based on user-defined 3x3 scaling matrix.
    '''
    try:
        schemas.GenerateSupercellFromPoscar(
            poscar_path=poscar_path,
            scaling_matrix=scaling_matrix,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    scaling_matrix_ = [
        [int(num) for num in line.strip().split()] 
        for line in scaling_matrix.split(';')
        ]

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        supercell_dir = os.path.join(runs_dir, 'supercell')
        os.makedirs(supercell_dir, exist_ok=True)
        
        structure = Structure.from_file(poscar_path).copy()
        supercell_structure = structure.make_supercell(scaling_matrix_)
        supercell_poscar = Poscar(supercell_structure)
        supercell_poscar.write_file(os.path.join(supercell_dir, 'POSCAR'), direct=True)
        
        comments = f'# Generated by Masgent as supercell with scaling matrix {scaling_matrix}.'
        write_comments(os.path.join(supercell_dir, 'POSCAR'), 'poscar', comments)

        return {
            'status': 'success',
            'message': f'Generated supercell POSCAR in {os.path.join(supercell_dir, "POSCAR")}.',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Supercell generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate Special Quasirandom Structures (SQS)',
    description='Generate Special Quasirandom Structures (SQS) using icet based on given POSCAR',
    requires=['target_configurations'],
    optional=['poscar_path', 'cutoffs', 'max_supercell_size', 'mc_steps'],
    defaults={
        'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
        'cutoffs': [8.0, 4.0],
        'max_supercell_size': 8,
        'mc_steps': 10000,
    },
    prereqs=[],
))
def generate_sqs_from_poscar(
    target_configurations: dict[str, dict[str, float]],
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
    cutoffs: list[float] = [8.0, 4.0],
    max_supercell_size: int = 8,
    mc_steps: int = 10000,
) -> dict:
    '''
    Generate Special Quasirandom Structures (SQS) using icet.
    '''
    try:
        schemas.GenerateSqsFromPoscar(
            poscar_path=poscar_path,
            target_configurations=target_configurations,
            cutoffs=cutoffs,
            max_supercell_size=max_supercell_size,
            mc_steps=mc_steps,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        from icet import ClusterSpace
        from icet.tools.structure_generation import generate_sqs
        from icet.input_output.logging_tools import set_log_config

        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        sqs_dir = os.path.join(runs_dir, 'sqs')
        os.makedirs(sqs_dir, exist_ok=True)

        set_log_config(
        filename=f'{sqs_dir}/masgent_sqs.log',
        level='INFO',
        )

        primitive_structure = read(poscar_path, format='vasp')

        # Get the all chemical symbols in the structure
        chem_symbols = [[site] for site in primitive_structure.get_chemical_symbols()]

        # Create target sites mapping based on target_configurations: {'La': ['La', 'Y'], 'Co': ['Al', 'Co']}
        target_sites = {}
        for site, config in target_configurations.items():
            target_sites[site] = list(config.keys())

        # Update chem_symbols to reflect target sites
        for i, site in enumerate(chem_symbols):
            for target_site, configurations in target_sites.items():
                if site == [target_site]:
                    chem_symbols[i] = configurations

        # Initialize ClusterSpace
        cs = ClusterSpace(
            structure=primitive_structure, 
            cutoffs=cutoffs, 
            chemical_symbols=chem_symbols,
            )
        
        # Get the sublattice (A, B, ...) configurations from ClusterSpace
        chemical_symbol_representation = cs._get_chemical_symbol_representation()
        
        # Map sublattice letters to actual element symbols
        sublattice_indices = {}
        sublattice_parts = chemical_symbol_representation.split('),')
        for i, part in enumerate(sublattice_parts):
            match = re.search(r"\['(.*)'\]", part)
            if match:
                elements = match.group(1).split("', '")
                sublattice_indices[chr(65 + i)] = elements
        
        # Initialize target concentrations: {'A': {'Al': 0.0, 'Co': 0.0}, 'B': {'La': 0.0, 'Y': 0.0}, 'O': {'O': 1.0}}
        unique_chem_symbols = [list(x) for x in dict.fromkeys(tuple(x) for x in chem_symbols)]
        target_concentrations = {}
        for sublattice, elements in sublattice_indices.items():
            for unique_list in unique_chem_symbols:
                if set(elements) == set(unique_list):
                    concentration_dict = {element: 0.0 for element in unique_list}
                    target_concentrations[sublattice] = concentration_dict
                if len(unique_list) == 1:
                    element = unique_list[0]
                    target_concentrations[element] = {element: 1.0}

        # Update target concentrations based on target_configurations
        for key, value in target_configurations.items():
            for sublattice, conc_dict in target_concentrations.items():
                if key in conc_dict:
                    target_concentrations[sublattice] = value

        # Generate SQS and write to POSCAR
        sqs = generate_sqs(cluster_space=cs,
                   max_size=max_supercell_size,
                   target_concentrations=target_concentrations,
                   n_steps=mc_steps
                   )
        write(os.path.join(sqs_dir, 'POSCAR'), sqs, format='vasp', direct=True, sort=True)
        comments = f'# Generated by Masgent as Special Quasirandom Structure (SQS) with target configurations {target_configurations} using icet.'
        write_comments(os.path.join(sqs_dir, 'POSCAR'), 'poscar', comments)

        return {
            'status': 'success',
            'message': f'Generated SQS POSCAR in {os.path.join(sqs_dir, "POSCAR")}.',
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'SQS generation failed: {str(e)}'
        }
    
@with_metadata(schemas.ToolMetadata(
    name='Generate suface slab from bulk POSCAR',
    description='Generate surface slab from bulk POSCAR based on Miller indices, vacuum thickness, and slab layers',
    requires=['miller_indices'],
    optional=['poscar_path', 'vacuum_thickness', 'slab_layers'],
    defaults={
        'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
        'vacuum_thickness': 15.0,
        'slab_layers': 4,
        },
    prereqs=[],
))
def generate_surface_slab_from_poscar(
    miller_indices: List[int],
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
    vacuum_thickness: float = 15.0,
    slab_layers: int = 4,
) -> dict:
    '''
    Generate VASP POSCAR for surface slab from bulk POSCAR based on Miller indices, vacuum thickness, and slab layers
    '''
    try:
        schemas.GenerateSurfaceSlabFromPoscar(
            poscar_path=poscar_path,
            miller_indices=miller_indices,
            vacuum_thickness=vacuum_thickness,
            slab_layers=slab_layers,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        surface_slab_dir = os.path.join(runs_dir, 'surface_slab')
        os.makedirs(surface_slab_dir, exist_ok=True)
        
        from ase.build import surface
        bulk_atoms = read(poscar_path, format='vasp')
        slab_atoms = surface(lattice=bulk_atoms, indices=miller_indices, layers=slab_layers, vacuum=vacuum_thickness, tol=1e-10, periodic=True)
        write(os.path.join(surface_slab_dir, 'POSCAR'), slab_atoms, format='vasp', direct=True, sort=True)
        comments = f'# Generated by Masgent as surface slab with Miller indices {miller_indices}, vacuum thickness {vacuum_thickness} Å, and slab layers {slab_layers}.'
        write_comments(os.path.join(surface_slab_dir, 'POSCAR'), 'poscar', comments)

        return {
            'status': 'success',
            'message': f'Generated surface slab POSCAR in {os.path.join(surface_slab_dir, "POSCAR")}.',
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Surface slab POSCAR generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate interface from two POSCARs',
    description='Generate VASP POSCAR for interface from two given POSCAR files based on specified parameters',
    requires=['lower_poscar_path', 'upper_poscar_path', 'lower_hkl', 'upper_hkl'],
    optional=['lower_slab_layers', 'upper_slab_layers', 'slab_vacuum', 'min_area', 'max_area', 'interface_gap', 'uv_tolerance', 'angle_tolerance', 'shape_filter'],
    defaults={
        'lower_slab_layers': 4,
        'upper_slab_layers': 4,
        'slab_vacuum': 15.0,
        'min_area': 50.0,
        'max_area': 500.0,
        'interface_gap': 2.0,
        'uv_tolerance': 5.0,
        'angle_tolerance': 5.0,
        'shape_filter': False,
        },
    prereqs=[],
))
def generate_interface_from_poscars(
    lower_poscar_path: str,
    upper_poscar_path: str,
    lower_hkl: List[int],
    upper_hkl: List[int],
    lower_slab_layers: int = 4,
    upper_slab_layers: int = 4,
    slab_vacuum: float = 15.0,
    min_area: float = 50.0,
    max_area: float = 500.0,
    interface_gap: float = 2.0,
    uv_tolerance: float = 5.0,
    angle_tolerance: float = 5.0,
    shape_filter: bool = False,
) -> dict:
    '''
    Generate VASP POSCAR for interface from two given POSCAR files based on specified parameters
    '''
    # print(f'\n[Debug: Function Calling] generate_interface_from_poscars with input: {input}', 'green')
    
    try:
        schemas.GenerateInterfaceFromPoscars(
            lower_poscar_path=lower_poscar_path,
            upper_poscar_path=upper_poscar_path,
            lower_hkl=lower_hkl,
            upper_hkl=upper_hkl,
            lower_slab_layers=lower_slab_layers,
            upper_slab_layers=upper_slab_layers,
            slab_vacuum=slab_vacuum,
            min_area=min_area,
            max_area=max_area,
            interface_gap=interface_gap,
            uv_tolerance=uv_tolerance,
            angle_tolerance=angle_tolerance,
            shape_filter=shape_filter,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        interfaces_dir = os.path.join(runs_dir, 'interface_maker')
        os.makedirs(interfaces_dir, exist_ok=True)

        from masgent.utils.interface_maker import run_interface_maker
        run_interface_maker(
            lower_conv=lower_poscar_path,
            upper_conv=upper_poscar_path,
            lower_hkl=lower_hkl,
            upper_hkl=upper_hkl,
            lower_slab_layers=lower_slab_layers,
            upper_slab_layers=upper_slab_layers,
            slab_vacuum=slab_vacuum,
            min_area=min_area,
            max_area=max_area,
            interface_gap=interface_gap,
            uv_tol=uv_tolerance,
            angle_tol=angle_tolerance,
            shape_filter=shape_filter,
            output_dir=interfaces_dir,
        )

        return {
            'status': 'success',
            'message': f'Generated interface POSCAR(s) in {interfaces_dir}.',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Interface POSCAR generation failed: {str(e)}'
        }
@with_metadata(schemas.ToolMetadata(
    name='Visualize Structure from POSCAR',
    description='Visualize structure from POSCAR using 3Dmol.js',
    requires=['poscar_path'],
    optional=[],
    defaults={},
    prereqs=[],
))
def visualize_structure_from_poscar(poscar_path: str) -> dict:
    '''
    Visualize structure from POSCAR using 3Dmol.js
    '''
    try:
        schemas.CheckPoscar(poscar_path=poscar_path)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        vis_dir = os.path.join(runs_dir, 'visualization')
        os.makedirs(vis_dir, exist_ok=True)

        save_path = os.path.join(vis_dir, f'OPEN_IN_BROWSER.html')
        count = 1
        while os.path.exists(save_path):
            save_path = os.path.join(vis_dir, f'OPEN_IN_BROWSER_{count}.html')
            count += 1

        visualize_structure(poscar_path=poscar_path, save_path=save_path)
        
        return {
            'status': 'success',
            'message': f'Structure visualization HTML file generated successfully at {save_path}.',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Structure visualization failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate VASP input files and submit bash script for workflow of convergence tests',
    description='Generate VASP workflow of convergence tests for k-points and energy cutoff based on given POSCAR',
    requires=[],
    optional=['poscar_path', 'test_type', 'kpoint_levels', 'encut_levels'],
    defaults={
        'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
        'test_type': 'both',
        'kpoint_levels': [1000, 2000, 3000, 4000, 5000],
        'encut_levels': [300, 400, 500, 600, 700],
        },
    prereqs=[],
))
def generate_vasp_workflow_of_convergence_tests(
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
    test_type: Literal['kpoints', 'encut', 'both'] = 'both',
    kpoint_levels: List[int] = [1000, 2000, 3000, 4000, 5000],
    encut_levels: List[int] = [300, 400, 500, 600, 700],
) -> dict:
    '''
    Generate VASP input files and submit bash script for workflow of convergence tests for k-points and energy cutoff based on given POSCAR
    '''
    try:
        schemas.GenerateVaspWorkflowOfConvergenceTests(
            poscar_path=poscar_path,
            test_type=test_type,
            kpoint_levels=kpoint_levels,
            encut_levels=encut_levels,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    def test_kpoints():
        os.makedirs(kpoint_tests_dir, exist_ok=True)
        vis = MPStaticSet(structure)
        vis.incar.write_file(os.path.join(kpoint_tests_dir, 'INCAR_temp'))
        vis.potcar.write_file(os.path.join(kpoint_tests_dir, 'POTCAR_temp'))
        incar_comments = f'# Generated by Masgent for k-point convergence test.'
        write_comments(os.path.join(kpoint_tests_dir, 'INCAR_temp'), 'incar', incar_comments)
        script_path = os.path.join(kpoint_tests_dir, 'submit_temp.sh')
        script = generate_submit_script()
        with open(script_path, 'w') as f:
            f.write(script)

        for kppa in kpoint_levels:
            test_dir = os.path.join(kpoint_tests_dir, f'kppa_{kppa}')
            os.makedirs(test_dir, exist_ok=True)
            
            vis = MPStaticSet(structure)
            vis.poscar.write_file(os.path.join(test_dir, 'POSCAR'))
            poscar_comments = f'# Generated by Masgent for k-point convergence test with kppa = {kppa}.'
            write_comments(os.path.join(test_dir, 'POSCAR'), 'poscar', poscar_comments)
            kpoints = Kpoints.automatic_density(structure, kppa=kppa)
            kpoints.write_file(os.path.join(test_dir, 'KPOINTS'))
            kpoint_comments = f'# Generated by Masgent for k-point convergence test with kppa = {kppa}.'
            write_comments(os.path.join(test_dir, 'KPOINTS'), 'kpoints', kpoint_comments)

        batch_script_path = os.path.join(kpoint_tests_dir, 'RUN_ME.sh')
        batch_script = generate_batch_script(update_incar=True, update_kpoints=False)
        with open(batch_script_path, 'w') as f:
            f.write(batch_script)

    def test_encut():
        os.makedirs(encut_tests_dir, exist_ok=True)
        vis = MPStaticSet(structure)
        vis.kpoints.write_file(os.path.join(encut_tests_dir, 'KPOINTS_temp'))
        vis.potcar.write_file(os.path.join(encut_tests_dir, 'POTCAR_temp'))
        kpoint_comments = f'# Generated by Masgent for energy cutoff convergence test.'
        write_comments(os.path.join(encut_tests_dir, 'KPOINTS_temp'), 'kpoints', kpoint_comments)
        script_path = os.path.join(encut_tests_dir, 'submit_temp.sh')
        script = generate_submit_script()
        with open(script_path, 'w') as f:
            f.write(script)

        for encut in encut_levels:
            test_dir = os.path.join(encut_tests_dir, f'encut_{encut}')
            os.makedirs(test_dir, exist_ok=True)

            vis = MPStaticSet(structure, user_incar_settings={'ENCUT': encut})
            vis.incar.write_file(os.path.join(test_dir, 'INCAR'))
            incar_comments = f'# Generated by Masgent for energy cutoff convergence test with ENCUT = {encut}.'
            write_comments(os.path.join(test_dir, 'INCAR'), 'incar', incar_comments)
            vis.poscar.write_file(os.path.join(test_dir, 'POSCAR'))
            poscar_comments = f'# Generated by Masgent for energy cutoff convergence test with ENCUT = {encut}.'
            write_comments(os.path.join(test_dir, 'POSCAR'), 'poscar', poscar_comments)

        batch_script_path = os.path.join(encut_tests_dir, 'RUN_ME.sh')
        batch_script = generate_batch_script(update_incar=False, update_kpoints=True)
        with open(batch_script_path, 'w') as f:
            f.write(batch_script)

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        convergence_tests_dir = os.path.join(runs_dir, 'convergence_tests')
        kpoint_tests_dir = os.path.join(convergence_tests_dir, 'kpoint_tests')
        encut_tests_dir = os.path.join(convergence_tests_dir, 'encut_tests')

        structure = Structure.from_file(poscar_path)

        if test_type == 'kpoints':
            test_kpoints()
        elif test_type == 'encut':
            test_encut()
        else:
            test_kpoints()
            test_encut()

        kpoint_tests_files = list_files_in_dir(kpoint_tests_dir) if os.path.exists(kpoint_tests_dir) else []
        encut_tests_files = list_files_in_dir(encut_tests_dir) if os.path.exists(encut_tests_dir) else []

        return {
            'status': 'success',
            'message': f'Generated VASP workflow of convergence tests of k-points in {kpoint_tests_dir} and energy cutoff in {encut_tests_dir}.',
            'kpoint_tests_files': kpoint_tests_files,
            'encut_tests_files': encut_tests_files,
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP convergence tests workflow generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate VASP input files and submit bash script for workflow of equation of state (EOS) calculations',
    description='Generate VASP input files and submit bash script for workflow of equation of state (EOS) calculations based on given POSCAR',
    requires=[],
    optional=['poscar_path', 'scale_factors'],
    defaults={
        'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
        'scale_factors': [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06],
        },
    prereqs=[],
))
def generate_vasp_workflow_of_eos(
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
    scale_factors: List[float] = [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06],
) -> dict:
    '''
    Generate VASP input files and submit bash script for workflow of equation of state (EOS) calculations based on given POSCAR
    '''
    try:
        schemas.GenerateVaspWorkflowOfEos(
            poscar_path=poscar_path,
            scale_factors=scale_factors,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        eos_dir = os.path.join(runs_dir, 'eos_calculations')
        os.makedirs(eos_dir, exist_ok=True)
        
        structure = Structure.from_file(poscar_path)
        vis = MPStaticSet(structure)
        vis.incar.write_file(os.path.join(eos_dir, 'INCAR_temp'))
        vis.kpoints.write_file(os.path.join(eos_dir, 'KPOINTS_temp'))
        vis.potcar.write_file(os.path.join(eos_dir, 'POTCAR_temp'))
        incar_comments = f'# Generated by Masgent for EOS calculation'
        write_comments(os.path.join(eos_dir, 'INCAR_temp'), 'incar', incar_comments)
        kpoint_comments = f'# Generated by Masgent for EOS calculation'
        write_comments(os.path.join(eos_dir, 'KPOINTS_temp'), 'kpoints', kpoint_comments)
        script_path = os.path.join(eos_dir, 'submit_temp.sh')
        script = generate_submit_script()
        with open(script_path, 'w') as f:
            f.write(script)

        for scale in scale_factors:
            scaled_structure = structure.copy()
            scaled_structure.scale_lattice(structure.volume * scale)
            scale_dir = os.path.join(eos_dir, f'scale_{scale:.3f}')
            os.makedirs(scale_dir, exist_ok=True)
            
            vis = MPStaticSet(scaled_structure)
            vis.poscar.write_file(os.path.join(scale_dir, 'POSCAR'))
            poscar_comments = f'# Generated by Masgent for EOS calculation with scale factor = {scale:.3f}.'
            write_comments(os.path.join(scale_dir, 'POSCAR'), 'poscar', poscar_comments)

        batch_script_path = os.path.join(eos_dir, 'RUN_ME.sh')
        batch_script = generate_batch_script(update_incar=True, update_kpoints=True)
        with open(batch_script_path, 'w') as f:
            f.write(batch_script)
        
        eos_files = list_files_in_dir(eos_dir) if os.path.exists(eos_dir) else []

        return {
            'status': 'success',
            'message': f'Generated VASP workflow of EOS calculations in {eos_dir}.',
            'eos_files': eos_files,
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP EOS workflow generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate VASP input files and submit bash script for workflow of elastic constants calculations',
    description='Generate VASP input files and submit bash script for workflow of elastic constants calculations based on given POSCAR',
    requires=[],
    optional=['poscar_path'],
    defaults={'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR'},
    prereqs=[],
))
def generate_vasp_workflow_of_elastic_constants(
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
) -> dict:
    '''
    Generate VASP input files and submit bash script for workflow of elastic constants calculations based on given POSCAR
    '''
    try:
        schemas.GenerateVaspWorkflowOfElasticConstants(poscar_path=poscar_path)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        elastic_dir = os.path.join(runs_dir, 'elastic_constants')
        os.makedirs(elastic_dir, exist_ok=True)
        
        structure = Structure.from_file(poscar_path)
        vis = MPStaticSet(structure, reciprocal_density=500)
        vis.incar.write_file(os.path.join(elastic_dir, 'INCAR_temp'))
        vis.kpoints.write_file(os.path.join(elastic_dir, 'KPOINTS_temp'))
        vis.potcar.write_file(os.path.join(elastic_dir, 'POTCAR_temp'))
        incar_comments = f'# Generated by Masgent for elastic constants calculation.'
        write_comments(os.path.join(elastic_dir, 'INCAR_temp'), 'incar', incar_comments)
        kpoint_comments = f'# Generated by Masgent for elastic constants calculation.'
        write_comments(os.path.join(elastic_dir, 'KPOINTS_temp'), 'kpoints', kpoint_comments)
        script_path = os.path.join(elastic_dir, 'submit_temp.sh')
        script = generate_submit_script()
        with open(script_path, 'w') as f:
            f.write(script)

        D_all = create_deformation_matrices()

        for D_dict in D_all:
            folder_name = list(D_dict.keys())[0]
            D = D_dict[folder_name]
            deformed_structure = structure.copy()
            F = np.eye(3) + np.array(D)
            deformed_lattice = Lattice(F @ structure.lattice.matrix)
            deformed_structure.lattice = deformed_lattice
            deform_dir = os.path.join(elastic_dir, folder_name)
            os.makedirs(deform_dir, exist_ok=True)
            
            vis = MPStaticSet(deformed_structure)
            vis.poscar.write_file(os.path.join(deform_dir, 'POSCAR'))
            poscar_comments = f'# Generated by Masgent for elastic constants calculation with deformation {folder_name}.'
            write_comments(os.path.join(deform_dir, 'POSCAR'), 'poscar', poscar_comments)
        
        batch_script_path = os.path.join(elastic_dir, 'RUN_ME.sh')
        batch_script = generate_batch_script(update_incar=True, update_kpoints=True)
        with open(batch_script_path, 'w') as f:
            f.write(batch_script)

        elastic_files = list_files_in_dir(elastic_dir) if os.path.exists(elastic_dir) else []

        return {
            'status': 'success',
            'message': f'Generated VASP workflow of elastic constants calculations in {elastic_dir}.',
            'elastic_files': elastic_files,
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP elastic constants workflow generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate VASP input files and submit bash script for workflow of ab initio molecular dynamics (AIMD) simulation',
    description='Generate VASP input files and submit bash script for workflow of ab initio molecular dynamics (AIMD) simulations based on given POSCAR',
    requires=[],
    optional=['poscar_path', 'temperature', 'md_steps', 'md_timestep'],
    defaults={
        'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
        'temperatures': [500, 1000, 1500, 2000, 2500],
        'md_steps': 1000,
        'md_timestep': 5.0,
        },
    prereqs=[],
))
def generate_vasp_workflow_of_aimd(
    poscar_path: str,
    temperatures: list[int],
    md_steps: int,
    md_timestep: float,
    ) -> dict:
    '''
    Generate VASP input files and submit bash script for workflow of ab initio molecular dynamics (AIMD) simulations based on given POSCAR
    '''
    try:
        schemas.GenerateVaspWorkflowOfAimd(
            poscar_path=poscar_path,
            temperatures=temperatures,
            md_steps=md_steps,
            md_timestep=md_timestep,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        aimd_dir = os.path.join(runs_dir, 'aimd_simulations')
        os.makedirs(aimd_dir, exist_ok=True)
        
        structure = Structure.from_file(poscar_path)
        vis = MPMDSet(structure, start_temp=temperatures[0], end_temp=temperatures[0], nsteps=md_steps, time_step=md_timestep)
        vis.kpoints.write_file(os.path.join(aimd_dir, 'KPOINTS_temp'))
        vis.potcar.write_file(os.path.join(aimd_dir, 'POTCAR_temp'))
        kpoint_comments = f'# Generated by Masgent for AIMD simulation.'
        write_comments(os.path.join(aimd_dir, 'KPOINTS_temp'), 'kpoints', kpoint_comments)
        script_path = os.path.join(aimd_dir, 'submit_temp.sh')
        script = generate_submit_script()
        with open(script_path, 'w') as f:
            f.write(script)

        for temperature in temperatures:
            temp_dir = os.path.join(aimd_dir, f'T_{temperature}K')
            os.makedirs(temp_dir, exist_ok=True)

            vis = MPMDSet(structure, start_temp=temperature, end_temp=temperature, nsteps=md_steps, time_step=md_timestep)
            vis.incar.write_file(os.path.join(temp_dir, 'INCAR'))
            incar_comments = f'# Generated by Masgent for AIMD simulation at {temperature} K for {md_steps} steps with timestep {md_timestep} fs.'
            write_comments(os.path.join(temp_dir, 'INCAR'), 'incar', incar_comments)
            vis.poscar.write_file(os.path.join(temp_dir, 'POSCAR'))
            poscar_comments = f'# Generated by Masgent for AIMD simulation at {temperature} K for {md_steps} steps with timestep {md_timestep} fs.'
            write_comments(os.path.join(temp_dir, 'POSCAR'), 'poscar', poscar_comments)
        
        batch_script_path = os.path.join(aimd_dir, 'RUN_ME.sh')
        batch_script = generate_batch_script(update_incar=False, update_kpoints=True)
        with open(batch_script_path, 'w') as f:
            f.write(batch_script)

        aimd_files = list_files_in_dir(aimd_dir) if os.path.exists(aimd_dir) else []
        
        return {
            'status': 'success',
            'message': f'Generated VASP workflow of AIMD simulations in {aimd_dir}.',
            'aimd_files': aimd_files,
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP AIMD workflow generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Generate VASP input files and submit bash script for workflow of nudged elastic band (NEB) calculations',
    description='Generate VASP input files and submit bash script for workflow of nudged elastic band (NEB) calculations based on given initial and final POSCARs',
    requires=['initial_poscar_path', 'final_poscar_path'],
    optional=['num_images'],
    defaults={'num_images': 5},
    prereqs=[],
))
def generate_vasp_workflow_of_neb(
        initial_poscar_path: str,
        final_poscar_path: str,
        num_images: int = 5,
    ) -> dict:
    '''
    Generate VASP input files and submit bash script for workflow of nudged elastic band (NEB) calculations based on given initial and final POSCARs
    '''
    try:
        schemas.GenerateVaspWorkflowOfNeb(
            initial_poscar_path=initial_poscar_path,
            final_poscar_path=final_poscar_path,
            num_images=num_images,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        neb_dir = os.path.join(runs_dir, 'neb_calculations')
        os.makedirs(neb_dir, exist_ok=True)

        from ase.mep import NEB

        initial_atoms = read(initial_poscar_path, format='vasp')
        final_atoms = read(final_poscar_path, format='vasp')
        images = [initial_atoms] + [initial_atoms.copy() for i in range(num_images)] + [final_atoms]
        neb = NEB(images)
        neb.interpolate()

        pmg_images = [Structure.from_ase_atoms(img) for img in images]
        vis = NEBSet(pmg_images, user_incar_settings={'LCLIMB': True, 'SPRING': -5})
        vis.incar.write_file(os.path.join(neb_dir, 'INCAR'))
        vis.kpoints.write_file(os.path.join(neb_dir, 'KPOINTS'))
        vis.potcar.write_file(os.path.join(neb_dir, 'POTCAR'))
        incar_comments = f'# Generated by Masgent for NEB calculation with {num_images} images.'
        write_comments(os.path.join(neb_dir, 'INCAR'), 'incar', incar_comments)
        kpoint_comments = f'# Generated by Masgent for NEB calculation with {num_images} images.'
        write_comments(os.path.join(neb_dir, 'KPOINTS'), 'kpoints', kpoint_comments)
        
        scripts = generate_submit_script()
        script_path = os.path.join(neb_dir, 'submit.sh')
        with open(script_path, 'w') as f:
            f.write(scripts)
        
        num_dirs = len(images)
        padding = max(2, len(str(num_dirs - 1)))
        for i, image in enumerate(images):
            image_dir = os.path.join(neb_dir, f'{i:0{padding}d}')
            os.makedirs(image_dir, exist_ok=True)
            write(os.path.join(image_dir, 'POSCAR'), image, format='vasp', direct=True, sort=True)
            poscar_comments = f'# Generated by Masgent for NEB calculation image {i}.'
            write_comments(os.path.join(image_dir, 'POSCAR'), 'poscar', poscar_comments)

        neb_files = list_files_in_dir(neb_dir) if os.path.exists(neb_dir) else []
        
        return {
            'status': 'success',
            'message': f'Generated VASP workflow of NEB calculations in {neb_dir}.',
            'neb_files': neb_files,
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP NEB workflow generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Analyze VASP workflow of convergence tests for k-points and energy cutoff',
    description='Analyze VASP workflow of convergence tests for k-points and energy cutoff',
    requires=['convergence_tests_dir'],
    optional=[],
    defaults={},
    prereqs=[],
))
def analyze_vasp_workflow_of_convergence_tests(
    convergence_tests_dir: str,
) -> dict:
    '''
    Analyze VASP workflow of convergence tests for k-points and energy cutoff
    '''
    try:
        os.path.exists(convergence_tests_dir)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = convergence_tests_dir

        # Get all vasprun.xml files in the encut_tests subdirectory
        encut_tests_dir = os.path.join(runs_dir, 'encut_tests')
        if os.path.exists(encut_tests_dir):
            encut_tests_dict = {}
            for root, dirs, files in os.walk(encut_tests_dir):
                for file in files:
                    if file == 'vasprun.xml':
                        vasprun_path = os.path.join(root, file)
                        vasprun = Vasprun(vasprun_path)
                        final_energy = vasprun.final_energy
                        natoms = len(vasprun.atomic_symbols)
                        final_energy_per_atom = final_energy / natoms
                        encut_value = int(os.path.basename(root).split('_')[-1])
                        encut_tests_dict[encut_value] = final_energy_per_atom

        # Get all vasprun.xml files in the kpoint_tests subdirectory
        kpoint_tests_dir = os.path.join(runs_dir, 'kpoint_tests')
        if os.path.exists(kpoint_tests_dir):
            kpoint_tests_dict = {}
            for root, dirs, files in os.walk(kpoint_tests_dir):
                for file in files:
                    if file == 'vasprun.xml':
                        vasprun_path = os.path.join(root, file)
                        vasprun = Vasprun(vasprun_path)
                        final_energy = vasprun.final_energy
                        natoms = len(vasprun.atomic_symbols)
                        final_energy_per_atom = final_energy / natoms
                        kpoints_value = int(os.path.basename(root).split('_')[-1])
                        kpoint_tests_dict[kpoints_value] = final_energy_per_atom

        # Plot the results: Final Energy per Atom vs Encut and Kpoints
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for plotting
        import matplotlib.pyplot as plt
        import seaborn as sns

        sns.set_theme(font_scale=1.2, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'

        # Plot Encut tests
        if encut_tests_dict:
            fig = plt.figure(figsize=(8, 6), constrained_layout=True)
            ax = plt.subplot()
            encut_values = sorted(encut_tests_dict.keys())
            encut_energies = [encut_tests_dict[encut] * 1000 for encut in encut_values]
            encut_energy_diffs = [encut_energies[i - 1] - encut_energies[i] for i in range(1, len(encut_energies))]
            sns.lineplot(x=encut_values[1:], y=encut_energy_diffs, marker='o', ax=ax, linestyle='-', linewidth=3.0, markersize=12, color='C0', markerfacecolor='C2')
            ax.axhline(y=1, color='r', linestyle='-', linewidth=1.0)
            ax.text(encut_values[-1], 1, 'Threshold < 1 meV/atom', color='r', ha='right', va='center', fontdict={'fontweight': 'bold'}, fontsize='small', bbox=dict(facecolor='white', edgecolor='none', pad=0.5))
            ax.set_xlabel('ENCUT (eV)')
            ax.set_ylabel('Energy Difference (meV/atom)')
            ax.set_title('Masgent ENCUT Convergence Test')
            plt.savefig(f'{runs_dir}/encut_tests.png', dpi=330)
            plt.close()

        # Plot Kpoint tests
        if kpoint_tests_dict:
            fig = plt.figure(figsize=(8, 6), constrained_layout=True)
            ax = plt.subplot()
            kpoint_values = sorted(kpoint_tests_dict.keys())
            kpoint_energies = [kpoint_tests_dict[kp] * 1000 for kp in kpoint_values]
            kpoint_energy_diffs = [kpoint_energies[i - 1] - kpoint_energies[i] for i in range(1, len(kpoint_energies))]
            sns.lineplot(x=kpoint_values[1:], y=kpoint_energy_diffs, marker='o', ax=ax, linestyle='-', linewidth=3.0, markersize=12, color='C0', markerfacecolor='C2')
            ax.axhline(y=1, color='r', linestyle='-', linewidth=1.0)
            ax.text(kpoint_values[-1], 1, 'Threshold < 1 meV/atom', color='r', ha='right', va='center', fontdict={'fontweight': 'bold'}, fontsize='small', bbox=dict(facecolor='white', edgecolor='none', pad=0.5))
            ax.set_xlabel('Kpoints Per Atom (kppa)')
            ax.set_ylabel('Energy Difference (meV/atom)')
            ax.set_title('Masgent Kpoint Convergence Test')
            plt.savefig(f'{runs_dir}/kpoint_tests.png', dpi=330)
            plt.close()

        return {
            'status': 'success',
            'message': f'Analyzed VASP workflow of convergence tests in {runs_dir}.',
            'encut_tests_plot': f'{runs_dir}/encut_tests.png' if encut_tests_dict else None,
            'kpoint_tests_plot': f'{runs_dir}/kpoint_tests.png' if kpoint_tests_dict else None,
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error analyzing VASP convergence tests workflow: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Analyze VASP workflow of equation of state (EOS) calculations',
    description='Analyze VASP workflow of equation of state (EOS) calculations',
    requires=['eos_dir'],
    optional=[],
    defaults={},
    prereqs=[],
))
def analyze_vasp_workflow_of_eos(
    eos_dir: str,
) -> dict:
    '''
    Analyze VASP workflow of equation of state (EOS) calculations
    '''
    try:
        os.path.exists(eos_dir)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = eos_dir

        scales = []
        structures = []
        volumes = []
        energies = []

        for root, dirs, files in os.walk(runs_dir):
            for dir_name in dirs:
                if dir_name.startswith('scale_'):
                    scale_value = float(dir_name.split('_')[-1])
                    scales.append(scale_value)
                    structure_path = os.path.join(root, dir_name, 'POSCAR')
                    structure = Structure.from_file(structure_path)
                    structures.append(structure)
                    vasprun_path = os.path.join(root, dir_name, 'vasprun.xml')
                    vasprun = Vasprun(vasprun_path)
                    final_energy = vasprun.final_energy
                    natoms = len(vasprun.atomic_symbols)
                    final_energy_per_atom = final_energy / natoms
                    structure = vasprun.final_structure
                    volume = structure.volume
                    volumes.append(volume)
                    energies.append(final_energy_per_atom)
        eos_df = pd.DataFrame({'Scale': scales, 'Volume[Å³]': volumes, 'Energy[eV/atom]': energies}).sort_values(by='Volume[Å³]')
        eos_df.to_csv(f'{runs_dir}/eos_cal.csv', index=False, float_format='%.8f')

        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for plotting
        import matplotlib.pyplot as plt
        import seaborn as sns

        volumes_fit, energies_fit = fit_eos(volumes, energies)
        eos_fit_df = pd.DataFrame({'Volume[Å³]': volumes_fit, 'Energy[eV/atom]': energies_fit})
        eos_fit_df.to_csv(f'{runs_dir}/eos_fit.csv', index=False, float_format='%.8f')
        equilibrium_volume = volumes_fit[energies_fit.argmin()]
        scale_temp = scales[0]
        volume_temp = volumes[0]
        structure_temp = structures[0]
        volume_at_scale_1 = volume_temp / scale_temp
        structure_at_scale_1 = structure_temp.copy()
        structure_at_scale_1.scale_lattice(structure_temp.volume / scale_temp)
        equilibrium_scale = equilibrium_volume / volume_at_scale_1
        structure_equilibrium = structure_at_scale_1.copy()
        structure_equilibrium.scale_lattice(equilibrium_volume)
        structure_equilibrium.to(filename=f'{runs_dir}/POSCAR_equilibrium')
        poscar_comments = f'# Generated by Masgent for EOS calculation with scale factor = {equilibrium_scale:.6f}.'
        write_comments(f'{runs_dir}/POSCAR_equilibrium', 'poscar', poscar_comments)
        
        # Plot the EOS curve
        sns.set_theme(font_scale=1.2, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'
        fig = plt.figure(figsize=(8, 6), constrained_layout=True)
        ax = plt.subplot()
        ax.scatter(volumes, energies, color='C2', label='Calculated', s=100, edgecolors='white', linewidths=1, zorder=5)
        ax.scatter(equilibrium_volume, energies_fit.min(), color='C3', marker='*', s=300, label='Equilibrium', edgecolors='white', linewidths=1, zorder=5)
        ax.plot(volumes_fit, energies_fit, color='C0', linestyle='-', linewidth=3.0, label='Fitted')
        ax.set_xlabel('Volume (Å³)')
        ax.set_ylabel('Energy (eV/atom)')
        ax.set_title('Masgent EOS')
        ax.legend(frameon=True, loc='upper right')
        plt.savefig(f'{runs_dir}/eos_curve.png', dpi=330)
        plt.close()

        return {
            'status': 'success',
            'message': f'Analyzed VASP workflow of EOS calculations in {runs_dir}.',
            'eos_fit_csv': f'{runs_dir}/eos_fit.csv',
            'eos_curve_plot': f'{runs_dir}/eos_curve.png',
            'poscar_equilibrium': f'{runs_dir}/POSCAR_equilibrium',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error analyzing VASP EOS workflow: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Analyze VASP workflow of elastic constants calculations',
    description='Analyze VASP workflow of elastic constants calculations',
    requires=['elastic_constants_dir'],
    optional=[],
    defaults={},
    prereqs=[],
))
def analyze_vasp_workflow_of_elastic_constants(
    elastic_constants_dir: str,
) -> dict:
    '''
    Analyze VASP workflow of elastic constants calculations
    '''
    try:
        os.path.exists(elastic_constants_dir)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = elastic_constants_dir

        D_all = create_deformation_matrices()
        strains, stresses = [], []
        
        for D_dict in D_all:
            folder_name = list(D_dict.keys())[0]
            D = D_dict[folder_name]
            strains.append(D)

            deform_dir = os.path.join(runs_dir, folder_name)
            vasprun_path = os.path.join(deform_dir, 'vasprun.xml')
            if os.path.exists(vasprun_path):
                vasprun = Vasprun(vasprun_path)
                stress = vasprun.ionic_steps[-1]['stress'] # in kBar
                stresses.append(stress)

        # Substract the stress of the undeformed structure
        eq_stress = stresses[0]
        strains = strains[1:]
        stresses = stresses[1:]

        from pymatgen.analysis.elasticity.strain import Strain
        from pymatgen.analysis.elasticity.stress import Stress
        from pymatgen.analysis.elasticity.elastic import ElasticTensor
        
        pmg_strains = [Strain(eps) for eps in strains]
        pmg_stresses = [Stress(sig) for sig in stresses]
        C = ElasticTensor.from_independent_strains(strains=pmg_strains, stresses=pmg_stresses, eq_stress=eq_stress, vasp=True)
        elastic_constants = C.voigt
        K_V = C.k_voigt
        K_R = C.k_reuss
        K_H = C.k_vrh
        G_V = C.g_voigt
        G_R = C.g_reuss
        G_H = C.g_vrh
        # Save elastic constants and properties to txt
        with open(f'{runs_dir}/elastic_constants.txt', 'w') as f:
            f.write(f'# Elastic constants and moduli calculated by Masgent\n')
            f.write(f'\nElastic Constants (GPa):\n')
            for row in elastic_constants:
                f.write('\t'.join([f'{val:.2f}' for val in row]) + '\n')
            f.write('\nMechanical Properties (GPa):')
            f.write(f'\nBulk Modulus (Voigt):\t\t{K_V:.2f}')
            f.write(f'\nBulk Modulus (Reuss):\t\t{K_R:.2f}')
            f.write(f'\nBulk Modulus (Hill):\t\t{K_H:.2f}')
            f.write(f'\nShear Modulus (Voigt):\t\t{G_V:.2f}')
            f.write(f'\nShear Modulus (Reuss):\t\t{G_R:.2f}')
            f.write(f'\nShear Modulus (Hill):\t\t{G_H:.2f}')

        return {
            'status': 'success',
            'message': f'Analyzed VASP workflow of elastic constants calculations in {runs_dir}.',
            'elastic_constants_txt': f'{runs_dir}/elastic_constants.txt',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error analyzing VASP elastic constants workflow: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Analyze VASP workflow of ab initio molecular dynamics (AIMD) simulations',
    description='Analyze VASP workflow of ab initio molecular dynamics (AIMD) simulations',
    requires=['aimd_dir', 'specie'],
    optional=[],
    defaults={},
    prereqs=[],
))
def analyze_vasp_workflow_of_aimd(
    aimd_dir: str,
    specie: str,
) -> dict:
    '''
    Analyze VASP workflow of ab initio molecular dynamics (AIMD) simulations
    '''
    try:
        os.path.exists(aimd_dir)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        schemas.CheckElement(element_symbol=specie)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try: 
        runs_dir = aimd_dir

        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for plotting
        import matplotlib.pyplot as plt
        import seaborn as sns

        sns.set_theme(font_scale=1.2, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'

        D_data= []
        for root, dirs, files in os.walk(runs_dir):
            for dir_name in dirs:
                if dir_name.startswith('T_') and dir_name.endswith('K'):
                    temperature = int(dir_name[2:-1])
                    folder_path = os.path.join(root, dir_name)
                    
                    # Parse the time step from INCAR
                    incar_path = os.path.join(folder_path, 'INCAR')
                    with open(incar_path, 'r') as f:
                        lines = f.readlines()
                        POTIM = 1.0
                        for line in lines:
                            if line.strip().startswith('POTIM'):
                                POTIM = float(line.strip().split('=')[1])
                    
                    # Parse the temperature and energy from OSZICAR
                    oszicar_path = os.path.join(folder_path, 'OSZICAR')
                    with open(oszicar_path, 'r') as f:
                        lines = f.readlines()
                        T_E_data = []
                        for line in lines:
                            if 'T=' in line:
                                T = float(line.split()[2])
                                E = float(line.split()[4])
                                T_E_data.append((T, E))
                    T_E_df = pd.DataFrame(T_E_data, columns=['Temperature (K)', 'Energy (eV)'])
                    T_E_df.to_csv(f'{folder_path}/aimd_temperature_energy.csv', index=False, float_format='%.6f')
                    
                    # Plot Time vs Temperature and Energy
                    time = np.arange(len(T_E_df)) * POTIM / 1000  # Convert to ps
                    fig, ax = plt.subplots(2, 1, figsize=(8, 6), constrained_layout=True, sharex=True)
                    ax[0].plot(time, T_E_df['Temperature (K)'], color='C0', label='Temperature', linewidth=1.0)
                    ax[0].hlines(temperature, 0, time[-1], colors='C3', linestyles='dashed', label='Target Temperature')
                    ax[0].set_ylabel('Temperature (K)')
                    ax[0].set_title(f'Masgent AIMD Temperature & Energy at {temperature} K')
                    ax[0].legend(frameon=True, loc='upper right')
                    ax[1].plot(time, T_E_df['Energy (eV)'], color='C1', label='Energy', linewidth=1.0)
                    ax[1].set_ylabel('Energy (eV)')
                    ax[1].set_xlabel('Time (ps)')
                    ax[1].legend(frameon=True, loc='upper right')
                    plt.savefig(f'{folder_path}/aimd_temperature_energy.png', dpi=330)
                    plt.close()

                    # Parse MSD, diffusion coefficient, and conductivity from XDATCAR
                    xdatcar_path = os.path.join(folder_path, 'XDATCAR')
                    traj = read(xdatcar_path, index=':')
                    indices = [i for i, a in enumerate(traj[0]) if a.symbol == 'Li']
                    positions_all = np.array([traj[i].get_positions() for i in range(len(traj))])
                    cell = traj[0].cell.array
                    unwrapped = positions_all.copy()
                    for i in range(1, len(positions_all)):
                        delta = positions_all[i] - positions_all[i-1]
                        delta -= np.round(delta @ np.linalg.inv(cell)) @ cell
                        unwrapped[i] = unwrapped[i-1] + delta
                    positions = unwrapped[:, indices]
                    positions_x = positions[:, :, 0]
                    positions_y = positions[:, :, 1]
                    positions_z = positions[:, :, 2]
                    msd_x = np.mean((positions_x - positions_x[0])**2, axis=1)
                    msd_y = np.mean((positions_y - positions_y[0])**2, axis=1)
                    msd_z = np.mean((positions_z - positions_z[0])**2, axis=1)
                    msd_total = np.mean(np.sum((positions - positions[0])**2, axis=2), axis=1)
                    time_ps = np.arange(len(msd_total)) * POTIM / 1000  # Convert to ps
                    msd_df = pd.DataFrame({
                        'Time (ps)': time_ps,
                        'MSD_x (Å²)': msd_x,
                        'MSD_y (Å²)': msd_y,
                        'MSD_z (Å²)': msd_z,
                        'MSD_total (Å²)': msd_total
                    })
                    msd_df.to_csv(f'{folder_path}/aimd_msd.csv', index=False, float_format='%.6f')
                    
                    # Plot time vs MSD
                    fig = plt.figure(figsize=(8, 6), constrained_layout=True)
                    ax = plt.subplot()
                    ax.plot(time_ps, msd_x, label='MSD_x', color='C0', linewidth=1.0)
                    ax.plot(time_ps, msd_y, label='MSD_y', color='C1', linewidth=1.0)
                    ax.plot(time_ps, msd_z, label='MSD_z', color='C2', linewidth=1.0)
                    ax.plot(time_ps, msd_total, label='MSD_total', color='C3', linewidth=1.0)
                    ax.set_xlabel('Time (ps)')
                    ax.set_ylabel('Mean Squared Displacement (Å²)')
                    ax.set_title(f'Masgent AIMD Mean Squared Displacement at {temperature} K')
                    ax.legend(frameon=True, loc='upper right')
                    plt.savefig(f'{folder_path}/aimd_msd.png', dpi=330)
                    plt.close()
                    
                    # Calculate diffusion coefficient from linear fit of MSD_total
                    slope, intercept = np.polyfit(time_ps, msd_total, 1)
                    diffusivity = slope / 6 / 1e4  # cm^2/s
                    D_data.append((temperature, diffusivity))

        D_df = pd.DataFrame(D_data, columns=['Temperature (K)', 'Diffusion Coefficient (cm²/s)']).sort_values(by='Temperature (K)')
        D_df.to_csv(f'{runs_dir}/aimd_diffusion_coefficients.csv', index=False, float_format='%.6e')

        # Plot Arrhenius plot
        fig = plt.figure(figsize=(8, 6), constrained_layout=True)
        ax = plt.subplot()
        D_df['Diffusion Coefficient (cm²/s)'] = D_df['Diffusion Coefficient (cm²/s)'].apply(lambda x: x if x > 0 else 1e-20)
        logD = np.log10(D_df['Diffusion Coefficient (cm²/s)'])
        inv_T = 1 / D_df['Temperature (K)']
        ax.plot(inv_T, logD, 'o', color='C0', label='Data')
        slope, intercept = np.polyfit(inv_T, logD, 1)
        ax.plot(inv_T, slope * inv_T + intercept, '-', color='C3', label='Fit', linewidth=1.0)
        ax.set_xlabel('1 / T $(K^{-1})$')
        ax.set_ylabel('logD $(cm^2/s)$')
        ax.set_title('Masgent AIMD Arrhenius Plot of Diffusion Coefficient')
        ax.legend(frameon=True, loc='upper right')
        plt.savefig(f'{runs_dir}/aimd_arrhenius_plot.png', dpi=330)
        plt.close()

        return {
            'status': 'success',
            'message': f'Analyzed VASP workflow of AIMD simulations in {runs_dir}.',
            'diffusion_coefficients_csv': f'{runs_dir}/aimd_diffusion_coefficients.csv',
            'arrhenius_plot': f'{runs_dir}/aimd_arrhenius_plot.png',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error analyzing VASP AIMD workflow: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Analyze VASP workflow of nudged elastic band (NEB) calculations',
    description='Analyze VASP workflow of nudged elastic band (NEB) calculations',
    requires=['neb_dir'],
    optional=[],
    defaults={},
    prereqs=[],
))
def analyze_vasp_workflow_of_neb(
    neb_dir: str,
) -> dict:
    '''
    Analyze VASP workflow of nudged elastic band (NEB) calculations
    '''
    try:
        os.path.exists(neb_dir)
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for plotting
        import matplotlib.pyplot as plt
        import seaborn as sns
        from pymatgen.analysis.transition_state import NEBAnalysis
        
        runs_dir = neb_dir

        neb = NEBAnalysis.from_dir(runs_dir)
        scale = 1 / neb.r[-1]
        xs = np.arange(0, np.max(neb.r), 0.01) * scale
        ys = neb.spline(xs / scale) * 1000
        data = pd.DataFrame({'Reaction Coordinate': xs, 'Energy (meV)': ys})
        data.to_csv(f'{runs_dir}/neb_data_spline.csv', index=False, float_format='%.8f')

        x = neb.r * scale
        relative_energies = neb.energies - neb.energies[0]
        y = relative_energies * 1000
        data_points = pd.DataFrame({'Reaction Coordinate': x, 'Relative Energy (meV)': y})
        data_points.to_csv(f'{runs_dir}/neb_data_points.csv', index=False, float_format='%.8f')

        energy_barrier = np.max(ys) - np.min(ys)
        with open(f'{runs_dir}/energy_barrier.txt', 'w') as f:
            f.write('# Masgent NEB Analysis\n\n')
            f.write(f'Energy Barrier: {energy_barrier:.8f} meV\n')

        # Plot NEB energy profile
        sns.set_theme(font_scale=1.2, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'
        fig = plt.figure(figsize=(8, 6), constrained_layout=True)
        ax = plt.subplot()
        # Scatter and line plot
        ax.plot(xs, ys, color='C0', linewidth=3.0, zorder=5)
        ax.scatter(x, y, color='C2', s=100, edgecolors='white', linewidths=1, zorder=6)
        # Plot the energy barrier
        x_mid = (xs[np.argmax(ys)] + xs[np.argmin(ys)]) / 2
        ax.hlines(np.max(ys), xmin=x_mid-0.2, xmax=x_mid+0.2, colors='C3', linestyles='-', linewidth=1.0)
        ax.hlines(np.min(ys), xmin=x_mid-0.2, xmax=x_mid+0.2, colors='C3', linestyles='-', linewidth=1.0)
        ax.vlines(x_mid, ymin=0, ymax=np.min(ys), colors='C3', linestyles='-', linewidth=1.0)
        ax.text(x_mid, np.max(ys), f'{energy_barrier:.2f} meV', color='C3', ha='center', va='center', fontdict={'weight': 'bold'}, fontsize='small', bbox=dict(facecolor='white', edgecolor='none', pad=0.5))
        ax.set_xlabel('Reaction Coordinate')
        ax.set_ylabel('Energy (meV)')
        ax.set_title('Masgent NEB Analysis')
        plt.savefig(f'{runs_dir}/neb_energy_profile.png', dpi=330)
        plt.close()

        return {
            'status': 'success',
            'message': f'Analyzed VASP workflow of NEB calculations in {runs_dir}.',
            'neb_data_spline_csv': f'{runs_dir}/neb_data_spline.csv',
            'neb_data_points_csv': f'{runs_dir}/neb_data_points.csv',
            'energy_barrier_txt': f'{runs_dir}/energy_barrier.txt',
            'neb_energy_profile_plot': f'{runs_dir}/neb_energy_profile.png',
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error analyzing VASP NEB workflow: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Run simulation using machine learning potentials (MLPs)',
    description='Run simulation using machine learning potentials (MLPs) based on given POSCAR. Supported tasks include: single point calculation, equation of state (EOS), elastic constants, and molecular dynamics (MD) simulations.',
    requires=[],
    optional=['poscar_path', 'mlps_type', 'task_type', 'fmax', 'max_steps', 'scale_factors', 'temperature', 'md_steps', 'md_timestep'],
    defaults={
        'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
        'mlps_type': 'CHGNet',
        'task_type': 'single',
        'fmax': 0.1,
        'max_steps': 500,
        'scale_factors': [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06],
        'temperature': 1000,
        'md_steps': 1000,
        'md_timestep': 5.0,
        },
    prereqs=[],
))
def run_simulation_using_mlps(
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
    mlps_type: Literal['SevenNet', 'CHGNet', 'Orb-v3', 'MatterSim'] = 'CHGNet',
    task_type: Literal['single', 'eos', 'elastic', 'md'] = 'single',
    fmax: float = 0.1,
    max_steps: int = 500,
    scale_factors: list = [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06],
    temperature: int = 1000,
    md_steps: int = 1000,
    md_timestep: float = 5.0,
) -> dict:
    '''
    Run simulation using machine learning potentials (MLPs) based on given POSCAR.
    Supported tasks include: single point calculation, equation of state (EOS), elastic constants, and molecular dynamics (MD) simulations.
    '''
    def fit_and_plot_eos(scales, structures, volumes, energies, mlps_type, task_dir):
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for plotting
        import matplotlib.pyplot as plt
        import seaborn as sns

        volumes_fit, energies_fit = fit_eos(volumes, energies)
        eos_fit_df = pd.DataFrame({'Volume[Å³]': volumes_fit, 'Energy[eV/atom]': energies_fit})
        eos_fit_df.to_csv(f'{task_dir}/eos_fit.csv', index=False, float_format='%.8f')
        equilibrium_volume = volumes_fit[energies_fit.argmin()]
        scale_temp = scales[0]
        volume_temp = volumes[0]
        structure_temp = structures[0]
        volume_at_scale_1 = volume_temp / scale_temp
        structure_at_scale_1 = structure_temp.copy()
        structure_at_scale_1.scale_lattice(structure_temp.volume / scale_temp)
        equilibrium_scale = equilibrium_volume / volume_at_scale_1
        structure_equilibrium = structure_at_scale_1.copy()
        structure_equilibrium.scale_lattice(equilibrium_volume)
        structure_equilibrium.to(filename=f'{task_dir}/POSCAR_equilibrium')
        poscar_comments = f'# Generated by Masgent for EOS calculation with scale factor = {equilibrium_scale:.6f}.'
        write_comments(f'{task_dir}/POSCAR_equilibrium', 'poscar', poscar_comments)
        
        # Plot the EOS curve
        sns.set_theme(font_scale=1.2, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'
        fig = plt.figure(figsize=(8, 6), constrained_layout=True)
        ax = plt.subplot()
        ax.scatter(volumes, energies, color='C2', label='Calculated', s=100, edgecolors='white', linewidths=1, zorder=5)
        ax.scatter(equilibrium_volume, energies_fit.min(), color='C3', marker='*', s=300, label='Equilibrium', edgecolors='white', linewidths=1, zorder=5)
        ax.plot(volumes_fit, energies_fit, color='C0', linestyle='-', linewidth=3.0, label='Fitted')
        ax.set_xlabel('Volume (Å³)')
        ax.set_ylabel('Energy (eV/atom)')
        ax.set_title(f'Masgent EOS using {mlps_type}')
        ax.legend(frameon=True, loc='upper right')
        plt.savefig(f'{task_dir}/eos_curve.png', dpi=330)
        plt.close()

    def parse_and_plot_md_log(logfile, mlps_type, task_dir):
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for plotting
        import matplotlib.pyplot as plt
        import seaborn as sns

        with open(logfile, 'r') as f:
            lines = f.readlines()
        data_lines = [line for line in lines if re.match(r'^\s*\d+\.\d+', line)]
        data = []
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 5:
                time_ps = float(parts[0])
                etot_per_atom = float(parts[1])
                epot_per_atom = float(parts[2])
                ekin_per_atom = float(parts[3])
                temperature_k = float(parts[4])
                data.append({
                    'Time[ps]': time_ps,
                    'Etot/N[eV]': etot_per_atom,
                    'Epot/N[eV]': epot_per_atom,
                    'Ekin/N[eV]': ekin_per_atom,
                    'T[K]': temperature_k
                })
        df = pd.DataFrame(data)
        sns.set_theme(font_scale=1.2, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'
        fig, ax = plt.subplots(4, 1, figsize=(8, 6), sharex=True, sharey=False, constrained_layout=True)
        ax[0].plot(df['Time[ps]'], df['Etot/N[eV]'], color='C0')
        ax[1].plot(df['Time[ps]'], df['Epot/N[eV]'], color='C1')
        ax[2].plot(df['Time[ps]'], df['Ekin/N[eV]'], color='C2')
        ax[3].plot(df['Time[ps]'], df['T[K]'], label='T', color='C3')
        ax[0].set_ylabel('$E_{tot}$ (eV/atom)')
        ax[1].set_ylabel('$E_{pot}$ (eV/atom)')
        ax[2].set_ylabel('$E_{kin}$ (eV/atom)')
        ax[3].set_ylabel('$T$ (K)')
        ax[3].set_xlabel('Time (ps)')
        ax[0].set_title(f'Masgent MD using {mlps_type}')
        plt.savefig(f'{task_dir}/md_log.png', dpi=330)
    
    try:
        schemas.RunSimulationUsingMlps(
            poscar_path=poscar_path,
            mlps_type=mlps_type,
            fmax=fmax,
            max_steps=max_steps,
            task_type=task_type,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        mlps_simulation_dir = os.path.join(runs_dir, f'mlps_simulation/{mlps_type}')
        os.makedirs(mlps_simulation_dir, exist_ok=True)

        if mlps_type == 'SevenNet':
            from sevenn.calculator import SevenNetCalculator
            calc = SevenNetCalculator(model='7net-0')
        elif mlps_type == 'CHGNet':
            from chgnet.model.dynamics import CHGNetCalculator
            calc = CHGNetCalculator()
        elif mlps_type == 'Orb-v3':
            from orb_models.forcefield import pretrained
            from orb_models.forcefield.calculator import ORBCalculator
            orbff = pretrained.orb_v3_conservative_inf_omat(
            device='cpu',
            precision="float32-high",   # or "float32-highest" / "float64
            )
            calc = ORBCalculator(orbff, device='cpu')
        elif mlps_type == 'MatterSim':
            from mattersim.forcefield import MatterSimCalculator
            calc = MatterSimCalculator()
        else:
            return {
                'status': 'error',
                'message': f'Invalid MLPs type: {mlps_type}.'
            }
        
        from ase.filters import FrechetCellFilter
        from ase.optimize import LBFGS

        if task_type == 'single':
            task_dir = os.path.join(mlps_simulation_dir, 'single')
            os.makedirs(task_dir, exist_ok=True)
            atoms = read(poscar_path, format='vasp')
            atoms.calc = calc
            # opt = LBFGS(FrechetCellFilter(atoms), logfile=f'{task_dir}/masgent_mlps_single.log')
            opt = LBFGS(atoms, logfile=f'{task_dir}/masgent_mlps_single.log')
            opt.run(fmax=fmax, steps=max_steps)
            atoms.write(f'{task_dir}/CONTCAR', format='vasp', direct=True, sort=True)
            comments = f'# Generated by Masgent from simulation using {mlps_type} with fmax = {fmax} eV/Å.'
            write_comments(f'{task_dir}/CONTCAR', 'poscar', comments)
            total_energy = atoms.get_potential_energy()
            energy_per_atom = total_energy / len(atoms)
            return {
                'status': 'success',
                'message': f'Completed simulation using {mlps_type} in {mlps_simulation_dir}.',
                'simulation_log_path': f'{task_dir}/masgent_mlps_single.log',
                'contcar_path': f'{task_dir}/CONTCAR',
                'total_energy (eV)': float(total_energy),
                'energy_per_atom (eV/atom)': float(energy_per_atom),
            }
        elif task_type == 'eos':
            task_dir = os.path.join(mlps_simulation_dir, 'eos')
            os.makedirs(task_dir, exist_ok=True)
            structure = Structure.from_file(poscar_path)
            scales, structures, volumes, energies = [], [], [], []
            for scale in scale_factors:
                scales.append(scale)
                # Create scaled structure
                scaled_structure = structure.copy()
                scaled_structure.scale_lattice(structure.volume * scale)
                scaled_structure_path = os.path.join(task_dir, f'POSCAR_{scale:.3f}')
                scaled_structure.to(fmt='poscar', filename=scaled_structure_path)
                comments = f'# Generated by Masgent for EOS calculation with scale factor = {scale:.3f} using {mlps_type}.'
                write_comments(scaled_structure_path, 'poscar', comments)
                structures.append(scaled_structure)
                # Load scaled structure and perform optimization
                atoms = read(scaled_structure_path, format='vasp')
                atoms.calc = calc
                # opt = LBFGS(FrechetCellFilter(atoms), logfile=f'{task_dir}/masgent_mlps_eos_{scale:.3f}.log')
                opt = LBFGS(atoms, logfile=f'{task_dir}/masgent_mlps_eos_{scale:.3f}.log')
                opt.run(fmax=fmax, steps=max_steps)
                atoms.write(f'{task_dir}/CONTCAR_{scale:.3f}', format='vasp', direct=True, sort=True)
                comments = f'# Generated by Masgent from simulation using {mlps_type} with fmax = {fmax} eV/Å.'
                write_comments(f'{task_dir}/CONTCAR_{scale:.3f}', 'poscar', comments)
                energy_per_atom = atoms.get_potential_energy() / len(atoms)
                volumes.append(atoms.get_volume())
                energies.append(energy_per_atom)
            # Save EOS results to CSV
            pd.DataFrame({'Scale Factor': scale_factors, 'Volume (Å³)': volumes, 'Energy (eV/atom)': energies}).to_csv(f'{task_dir}/eos_cal.csv', index=False, float_format='%.8f')
            # Fit and plot EOS
            fit_and_plot_eos(scales, structures, volumes, energies, mlps_type, task_dir)
            return {
                'status': 'success',
                'message': f'Completed EOS simulation using {mlps_type} in {mlps_simulation_dir}.',
                'eos_cal_csv_path': f'{task_dir}/eos_cal.csv',
                'eos_curve_png_path': f'{task_dir}/eos_curve.png',
            }
        elif task_type == 'elastic':
            from pymatgen.analysis.elasticity.strain import Strain
            from pymatgen.analysis.elasticity.stress import Stress
            from pymatgen.analysis.elasticity.elastic import ElasticTensor

            task_dir = os.path.join(mlps_simulation_dir, 'elastic')
            os.makedirs(task_dir, exist_ok=True)
            structure = Structure.from_file(poscar_path)
            D_all = create_deformation_matrices()
            strains, stresses = [], []
            for D_dict in D_all:
                folder_name = list(D_dict.keys())[0]
                D = D_dict[folder_name]
                # Create deformed structure
                deformed_structure = structure.copy()
                F = np.eye(3) + np.array(D)
                deformed_lattice = Lattice(F @ structure.lattice.matrix)
                deformed_structure.lattice = deformed_lattice
                deformed_structure_path = os.path.join(task_dir, f'POSCAR_{folder_name}')
                deformed_structure.to_ase_atoms().write(deformed_structure_path, format='vasp', direct=True, sort=True)
                comments = f'# Generated by Masgent for elastic constants calculation with deformation {folder_name} using {mlps_type}.'
                write_comments(deformed_structure_path, 'poscar', comments)
                # Load deformed structure and perform optimization
                atoms = read(deformed_structure_path, format='vasp')
                atoms.calc = calc
                # opt = LBFGS(FrechetCellFilter(atoms), logfile=f'{task_dir}/masgent_mlps_elastic_{folder_name}.log')
                opt = LBFGS(atoms, logfile=f'{task_dir}/masgent_mlps_elastic_{folder_name}.log')
                opt.run(fmax=fmax, steps=max_steps)
                atoms.write(f'{task_dir}/CONTCAR_{folder_name}', format='vasp', direct=True, sort=True)
                comments = f'# Generated by Masgent from simulation using {mlps_type} with fmax = {fmax} eV/Å.'
                write_comments(f'{task_dir}/CONTCAR_{folder_name}', 'poscar', comments)
                stress = atoms.get_stress(voigt=True)  # in eV/Å³
                stress_gpa = stress * 160.21766208  # convert to GPa
                stresses.append(stress_gpa)
                strains.append(D)
            eq_stress = Stress.from_voigt(stresses[0])
            strains = strains[1:]
            stresses = stresses[1:]
            # Calculate elastic constants and other properties
            pmg_strains = [Strain(eps) for eps in strains]
            pmg_stresses = [Stress.from_voigt(sig) for sig in stresses]
            C = ElasticTensor.from_independent_strains(strains=pmg_strains, stresses=pmg_stresses, eq_stress=eq_stress, vasp=False)
            elastic_constants = C.voigt
            K_V = C.k_voigt
            K_R = C.k_reuss
            K_H = C.k_vrh
            G_V = C.g_voigt
            G_R = C.g_reuss
            G_H = C.g_vrh
            # Save elastic constants and properties to txt
            with open(f'{task_dir}/elastic_constants.txt', 'w') as f:
                f.write(f'# Elastic constants and moduli calculated using {mlps_type} by Masgent\n')
                f.write(f'\nElastic Constants (GPa):\n')
                for row in elastic_constants:
                    f.write('\t'.join([f'{val:.2f}' for val in row]) + '\n')
                f.write('\nMechanical Properties (GPa):')
                f.write(f'\nBulk Modulus (Voigt):\t\t{K_V:.2f}')
                f.write(f'\nBulk Modulus (Reuss):\t\t{K_R:.2f}')
                f.write(f'\nBulk Modulus (Hill):\t\t{K_H:.2f}')
                f.write(f'\nShear Modulus (Voigt):\t\t{G_V:.2f}')
                f.write(f'\nShear Modulus (Reuss):\t\t{G_R:.2f}')
                f.write(f'\nShear Modulus (Hill):\t\t{G_H:.2f}')
            return {
                'status': 'success',
                'message': f'Completed elastic constants simulation using {mlps_type} in {mlps_simulation_dir}.',
                'elastic_constants_path': f'{task_dir}/elastic_constants.txt',
            }
        elif task_type == 'md':
            from ase import units
            from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
            from ase.md.nose_hoover_chain import NoseHooverChainNVT
            from ase.md import MDLogger

            task_dir = os.path.join(mlps_simulation_dir, 'md')
            os.makedirs(task_dir, exist_ok=True)
            atoms = read(poscar_path, format='vasp')
            atoms.calc = calc
            MaxwellBoltzmannDistribution(atoms, temperature_K=temperature)
            Stationary(atoms)
            dyn = NoseHooverChainNVT(
                atoms=atoms,
                timestep=md_timestep * units.fs,
                temperature_K=temperature,
                tdamp=100 * md_timestep * units.fs,
                trajectory=f'{task_dir}/masgent_mlps_md.traj',
                loginterval=10,
                append_trajectory=False,
            )
            dyn.attach(MDLogger(
                dyn=dyn,
                atoms=atoms,
                logfile=f'{task_dir}/masgent_mlps_md.log',
                header=True,
                peratom=True,
                mode='w',
            ), interval=10)
            dyn.run(md_steps)
            parse_and_plot_md_log(f'{task_dir}/masgent_mlps_md.log', mlps_type, task_dir)
            return {
                'status': 'success',
                'message': f'Completed MD simulation using {mlps_type} in {mlps_simulation_dir}.',
                'mlps_simulation_dir': mlps_simulation_dir,
                'md_trajectory_path': f'{task_dir}/masgent_mlps_md.traj',
                'md_log_path': f'{task_dir}/masgent_mlps_md.log',
                'md_log_png_path': f'{task_dir}/md_log.png',
            }
        else:
            return {
                'status': 'error',
                'message': f'Invalid task type: {task_type}.'
            }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Simulation using MLPs failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Analyze features for machine learning',
    description='Analyze features (correlation matrix) for machine learning based on given input and output datasets',
    requires=['input_data_path', 'output_data_path'],
    optional=[],
    defaults={},
    prereqs=[],
))
def analyze_features_for_machine_learning(
    input_data_path: str,
    output_data_path: str,
) -> dict:
    '''
    Analyze features (correlation matrix) for machine learning based on given input and output datasets
    '''
    try:
        schemas.AnalyzeFeaturesForMachineLearning(
            input_data_path=input_data_path,
            output_data_path=output_data_path,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        machine_learning_dir = os.path.join(runs_dir, 'machine_learning')
        os.makedirs(machine_learning_dir, exist_ok=True)

        ml_feature_analysis_dir = os.path.join(machine_learning_dir, 'ml_feature_analysis')
        os.makedirs(ml_feature_analysis_dir, exist_ok=True)

        input_df = pd.read_csv(input_data_path)
        output_df = pd.read_csv(output_data_path)
        # Save the input and output data in machine learning directory for reference
        input_df.to_csv(os.path.join(machine_learning_dir, 'ml_input_data.csv'), index=False, float_format='%.8f')
        output_df.to_csv(os.path.join(machine_learning_dir, 'ml_output_data.csv'), index=False, float_format='%.8f')

        combined_df = pd.concat([input_df, output_df], axis=1)
        corr_matrix = combined_df.corr()
        corr_matrix.to_csv(os.path.join(ml_feature_analysis_dir, 'correlation_matrix.csv'), float_format='%.8f')
        
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for plotting
        import matplotlib.pyplot as plt
        import seaborn as sns

        sns.set_theme(font_scale=1.0, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'
        fig = plt.figure(figsize=(13, 12), constrained_layout=True)
        ax = plt.subplot()
        sns.heatmap(
            corr_matrix, 
            annot=True, 
            fmt='.2f',
            cmap='coolwarm', 
            center=0, 
            cbar=False, 
            ax=ax
            )
        ax.set_title('Masgent Feature Correlation Matrix')
        plt.savefig(os.path.join(ml_feature_analysis_dir, 'correlation_matrix.png'), dpi=330)

        return {
            'status': 'success',
            'message': f'Completed feature analysis for machine learning in {ml_feature_analysis_dir}.',
            'ml_feature_analysis_dir': ml_feature_analysis_dir,
            'correlation_matrix_csv_path': os.path.join(ml_feature_analysis_dir, 'correlation_matrix.csv'),
            'correlation_matrix_png_path': os.path.join(ml_feature_analysis_dir, 'correlation_matrix.png'),
            'input_data_path': os.path.join(machine_learning_dir, 'ml_input_data.csv'),
            'output_data_path': os.path.join(machine_learning_dir, 'ml_output_data.csv'),
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Feature analysis for machine learning failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Reduce dimensions for machine learning',
    description='Reduce dimensions for machine learning based on given input dataset using PCA method',
    requires=['input_data_path'],
    optional=['n_components'],
    defaults={'n_components': 2},
    prereqs=[],
))
def reduce_dimensions_for_machine_learning(
    input_data_path: str,
    n_components: int = 2,
) -> dict:
    '''
    Reduce dimensions for machine learning based on given input dataset using PCA method
    '''
    try:
        schemas.ReduceDimensionsForMachineLearning(
            input_data_path=input_data_path,
            n_components=n_components,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        machine_learning_dir = os.path.join(runs_dir, 'machine_learning')
        os.makedirs(machine_learning_dir, exist_ok=True)

        ml_dimension_reduction_dir = os.path.join(machine_learning_dir, 'ml_dimension_reduction')
        os.makedirs(ml_dimension_reduction_dir, exist_ok=True)

        input_df = pd.read_csv(input_data_path)

        from sklearn.decomposition import PCA
        reducer = PCA(n_components=n_components)
        joblib.dump(reducer, os.path.join(ml_dimension_reduction_dir, "pca_reducer.pkl"))
        reduced_data = reducer.fit_transform(input_df.values)
        reduced_df = pd.DataFrame(reduced_data, columns=[f'Component_{i+1}' for i in range(n_components)])
        reduced_df.to_csv(os.path.join(ml_dimension_reduction_dir, 'ml_input_data_reduced.csv'), index=False, float_format='%.8f')

        return {
            'status': 'success',
            'message': f'Completed dimension reduction for machine learning in {ml_dimension_reduction_dir}.',
            'input_data_reduced_path': os.path.join(ml_dimension_reduction_dir, 'ml_input_data_reduced.csv'),
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Dimension reduction for machine learning failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Augment data for machine learning',
    description='Augment data for machine learning based on given input and output datasets using VAE-based method',
    requires=['input_data_path', 'output_data_path'],
    optional=['num_augmentations', 'max_epochs', 'loss_threshold'],
    defaults={'num_augmentations': 100},
    prereqs=[],
))
def augment_data_for_machine_learning(
    input_data_path: str,
    output_data_path: str,
    num_augmentations: int = 100,
) -> dict:
    '''
    Augment data for machine learning by VAE-based method
    '''
    try:
        schemas.AugmentDataForMachineLearning(
            input_data_path=input_data_path,
            output_data_path=output_data_path,
            num_augmentations=num_augmentations,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        machine_learning_dir = os.path.join(runs_dir, 'machine_learning')
        os.makedirs(machine_learning_dir, exist_ok=True)

        ml_data_augmentation_dir = os.path.join(machine_learning_dir, 'ml_data_augmentation')
        os.makedirs(ml_data_augmentation_dir, exist_ok=True)

        input_df = pd.read_csv(input_data_path)
        output_df = pd.read_csv(output_data_path)

        # Run VAE for data augmentation
        from masgent.utils.ml_cvae import run_cvae_augmentation

        x_aug_df, y_aug_df = run_cvae_augmentation(input_df=input_df, output_df=output_df, num_aug=num_augmentations)
        x_all_df = pd.concat([input_df, x_aug_df], ignore_index=True)
        y_all_df = pd.concat([output_df, y_aug_df], ignore_index=True)
        x_all_df.to_csv(os.path.join(ml_data_augmentation_dir, 'ml_input_data_augmented.csv'), index=False, float_format='%.8f')
        y_all_df.to_csv(os.path.join(ml_data_augmentation_dir, 'ml_output_data_augmented.csv'), index=False, float_format='%.8f')

        return {
            'status': 'success',
            'message': f'Completed data augmentation for machine learning in {ml_data_augmentation_dir}.',
            'input_data_augmented_path': os.path.join(ml_data_augmentation_dir, 'ml_input_data_augmented.csv'),
            'output_data_augmented_path': os.path.join(ml_data_augmentation_dir, 'ml_output_data_augmented.csv'),
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Data augmentation for machine learning failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Design model for machine learning',
    description='Design model for machine learning using Optuna-based hyperparameter optimization based on given input and output datasets',
    requires=['input_data_path', 'output_data_path'],
    optional=['n_trials'],
    defaults={'n_trials': 100},
    prereqs=[],
))
def design_model_for_machine_learning(
    input_data_path: str,
    output_data_path: str,
    n_trials: int = 100,
) -> dict:
    '''
    Design model for machine learning using Optuna-based hyperparameter optimization
    '''
    try:
        schemas.DesignModelForMachineLearning(
            input_data_path=input_data_path,
            output_data_path=output_data_path,
            n_trials=n_trials,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        machine_learning_dir = os.path.join(runs_dir, 'machine_learning')
        os.makedirs(machine_learning_dir, exist_ok=True)

        ml_model_design_dir = os.path.join(machine_learning_dir, 'ml_model_design')
        os.makedirs(ml_model_design_dir, exist_ok=True)

        # Run Optuna for model design
        from masgent.utils.ml_nn_design import optimize

        optimize(
            input_data=input_data_path,
            output_data=output_data_path,
            save_path=ml_model_design_dir,
            n_trials=n_trials,
        )

        ml_files = list_files_in_dir(ml_model_design_dir)

        return {
            'status': 'success',
            'message': f'Completed model design for machine learning in {ml_model_design_dir}.',
            'ml_model_design_files': ml_files,
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Model design for machine learning failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Train & evaluate model for machine learning',
    description='Train model for machine learning based on given input and output datasets as well as best model structure and parameters',
    requires=['input_data_path', 'output_data_path', 'best_model_path', 'best_model_params_path'],
    optional=['max_epochs', 'patience'],
    defaults={'max_epochs': 1000, 'patience': 50},
    prereqs=[],
))
def train_model_for_machine_learning(
    input_data_path: str,
    output_data_path: str,
    best_model_path: str,
    best_model_params_path: str,
    max_epochs: int = 1000,
    patience: int = 50,
) -> dict:
    '''
    Train & evaluate model for machine learning based on given input and output datasets as well as best model structure and parameters
    '''
    try:
        schemas.TrainModelForMachineLearning(
            input_data_path=input_data_path,
            output_data_path=output_data_path,
            best_model_path=best_model_path,
            best_model_params_path=best_model_params_path,
            max_epochs=max_epochs,
            patience=patience,
        )
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Invalid input parameters: {str(e)}'
        }
    
    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        machine_learning_dir = os.path.join(runs_dir, 'machine_learning')
        os.makedirs(machine_learning_dir, exist_ok=True)

        ml_model_training_dir = os.path.join(machine_learning_dir, 'ml_model_training')
        os.makedirs(ml_model_training_dir, exist_ok=True)

        # Run model training
        from masgent.utils.ml_nn_train import train
        
        train(
            input_data=input_data_path,
            output_data=output_data_path,
            best_model_pkl=best_model_path,
            best_model_params=best_model_params_path,
            epochs=max_epochs,
            patience=patience,
            save_path=ml_model_training_dir,
        )

        ml_files = list_files_in_dir(ml_model_training_dir)

        return {
            'status': 'success',
            'message': f'Completed model training for machine learning in {ml_model_training_dir}.',
            'ml_model_training_files': ml_files,
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Model training for machine learning failed: {str(e)}'
        }