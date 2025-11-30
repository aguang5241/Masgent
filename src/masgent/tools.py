# !/usr/bin/env python3

import os, warnings, random, shutil, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for plotting
from typing import Literal, Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from mp_api.client import MPRester
from sevenn.calculator import SevenNetCalculator
from chgnet.model.dynamics import CHGNetCalculator
from ase import units
from ase.build import surface
from ase.filters import FrechetCellFilter
from ase.optimize import LBFGS
from ase.io import read, write
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
from ase.md.nose_hoover_chain import NoseHooverChainNVT
from ase.md import MDLogger
from icet import ClusterSpace
from icet.tools.structure_generation import generate_sqs
from icet.input_output.logging_tools import set_log_config
from pymatgen.core import Structure
from pymatgen.io.vasp import Poscar, Kpoints
from pymatgen.analysis.defects import generators
from pymatgen.io.vasp.sets import (
    MPStaticSet, 
    MPRelaxSet, 
    MPNonSCFSet, 
    MPScanRelaxSet, 
    MPScanStaticSet,
    MPMDSet,
    NEBSet,
    MVLElasticSet,
    )

from masgent import schemas
from masgent.utils.interface_maker import run_interface_maker
from masgent.utils.utils import (
    write_comments,
    color_print,
    ask_for_mp_api_key,
    validate_mp_api_key,
    generate_batch_script,
    list_files_in_dir,
    fit_eos,
    )

# Do not show warnings
warnings.filterwarnings('ignore')

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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_poscar with input: {input}', 'green')
    
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
                # color_print('[Info] Materials Project API key found in environment.\n', 'green')
                validate_mp_api_key(os.environ['MP_API_KEY'])
            _mp_key_checked = True
        
        with MPRester(mute_progress_bars=True) as mpr:
            docs = mpr.materials.summary.search(formula=formula)
            if not docs:
                return {
                    'status': 'error',
                    'message': f'No materials found in Materials Project database for formula: {formula}'
                }
        
        # Save the most stable structure in the runs directory
        mid_0 = docs[0].material_id
        structure_0 = mpr.get_structure_by_material_id(mid_0)
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
            'poscar_dir': poscars_dir,
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
    description='Generate VASP input files (INCAR, KPOINTS, POTCAR, POSCAR) from a given POSCAR file using pymatgen input sets (MPRelaxSet, MPStaticSet, MPNonSCFSet, MPScanRelaxSet, MPScanStaticSet, MPMDSet, NEBSet, MVLElasticSet).',
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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_inputs_from_poscar with input: {input}', 'green')
    
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
        'MPRelaxSet': MPRelaxSet,
        'MPStaticSet': MPStaticSet,
        'MPNonSCFSet': MPNonSCFSet,
        'MPScanRelaxSet': MPScanRelaxSet,
        'MPScanStaticSet': MPScanStaticSet,
        'MPMDSet': MPMDSet,
        'NEBSet': NEBSet,
        'MVLElasticSet': MVLElasticSet,
    }
    vis_class = VIS_MAP[vasp_input_sets]

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        vasp_inputs_dir = os.path.join(runs_dir, f'vasp_inputs/{vasp_input_sets}')
        os.makedirs(vasp_inputs_dir, exist_ok=True)

        structure = Structure.from_file(poscar_path)
        vis = vis_class(structure)

        if only_incar:
            vis.incar.write_file(os.path.join(vasp_inputs_dir, 'INCAR'))
            vis.poscar.write_file(os.path.join(vasp_inputs_dir, 'POSCAR'))
            incar_comments = f'# Generated by Masgent using {vasp_input_sets} set provided by Materials Project.'
            write_comments(os.path.join(vasp_inputs_dir, 'INCAR'), 'incar', incar_comments)
            return {
                'status': 'success',
                'message': f'Generated INCAR based on {vasp_input_sets} in {vasp_inputs_dir}.',
                'incar_path': os.path.join(vasp_inputs_dir, 'INCAR'),
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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_inputs_hpc_slurm_script with input: {input}', 'green')
    
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
            'script_path': script_path,
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
    # color_print(f'\n[Debug: Function Calling] convert_structure_format with input: {input}', 'green')
    
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
            'output_path': output_path
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
    # color_print(f'\n[Debug: Function Calling] convert_poscar_coordinates with input: {input}', 'green')
    
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
            'message': f'Converted POSCAR to {coord_type} coordinates in {convert_dir}.',
            'poscar_path': os.path.join(convert_dir, 'POSCAR'),
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'POSCAR coordinate conversion failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Customize KPOINTS',
    description='Customize VASP KPOINTS from POSCAR with specified accuracy level (Low, Medium, High).',
    requires=['accuracy_level'],
    optional=['poscar_path'],
    defaults={'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR'},
    prereqs=[],
))
def customize_vasp_kpoints_with_accuracy(
    accuracy_level: Literal['Low', 'Medium', 'High'],
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
) -> dict:
    '''
    Customize VASP KPOINTS from POSCAR with specified accuracy level.
    '''
    # color_print(f'\n[Debug: Function Calling] customize_vasp_kpoints_with_accuracy with input: {input}', 'green')
    
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
    }
    kppa = DENSITY_MAP[accuracy_level]

    try:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        
        structure = Structure.from_file(poscar_path)
        kpoints = Kpoints.automatic_density(structure, kppa=kppa)
        kpoints.write_file(os.path.join(runs_dir, 'KPOINTS'))
        comments = f'# Generated by Masgent with {accuracy_level} accuracy (Grid Density = {kppa} / number of atoms)'
        write_comments(os.path.join(runs_dir, 'KPOINTS'), 'kpoints', comments)
        
        return {
            'status': 'success',
            'message': f'Updated KPOINTS with {accuracy_level} accuracy in {runs_dir}.',
            'kpoints_path': os.path.join(runs_dir, 'KPOINTS'),
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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_poscar_with_vacancy_defects with input: {input}', 'green')
    
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
            'poscar_path': os.path.join(defect_dir, 'POSCAR'),
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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_poscar_with_substitution_defects with input: {input}', 'green')

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
            'poscar_path': os.path.join(defect_dir, 'POSCAR'),
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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_poscar_with_interstitial_defects with input: {input}', 'green')

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
    # color_print(f'\n[Debug: Function Calling] generate_supercell_from_poscar with input: {input}', 'green')
    
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
            'poscar_path': os.path.join(supercell_dir, 'POSCAR'),
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
    # color_print(f'\n[Debug: Function Calling] generate_sqs_from_poscar with input: {input}', 'green')

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
            'poscar_path': os.path.join(sqs_dir, 'POSCAR'),
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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_poscar_for_surface_slab with input: {input}', 'green')
    
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
        
        bulk_atoms = read(poscar_path, format='vasp')
        slab_atoms = surface(lattice=bulk_atoms, indices=miller_indices, layers=slab_layers, vacuum=vacuum_thickness, tol=1e-10, periodic=True)
        write(os.path.join(surface_slab_dir, 'POSCAR'), slab_atoms, format='vasp', direct=True, sort=True)
        comments = f'# Generated by Masgent as surface slab with Miller indices {miller_indices}, vacuum thickness {vacuum_thickness} Å, and slab layers {slab_layers}.'
        write_comments(os.path.join(surface_slab_dir, 'POSCAR'), 'poscar', comments)

        return {
            'status': 'success',
            'message': f'Generated surface slab POSCAR in {os.path.join(surface_slab_dir, "POSCAR")}.',
            'poscar_path': os.path.join(surface_slab_dir, 'POSCAR'),
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
            'interface_dir': interfaces_dir,
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Interface POSCAR generation failed: {str(e)}'
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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_workflow_of_convergence_tests with input: {input}', 'green')
    
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
        for kppa in kpoint_levels:
            vis = MPStaticSet(structure)
            os.makedirs(kpoint_tests_dir, exist_ok=True)
            test_dir = os.path.join(kpoint_tests_dir, f'kppa_{kppa}')
            os.makedirs(test_dir, exist_ok=True)
            vis.incar.write_file(os.path.join(test_dir, 'INCAR'))
            vis.poscar.write_file(os.path.join(test_dir, 'POSCAR'))
            vis.potcar.write_file(os.path.join(test_dir, 'POTCAR'))
            incar_comments = f'# Generated by Masgent for k-point convergence test with kppa = {kppa}.'
            write_comments(os.path.join(test_dir, 'INCAR'), 'incar', incar_comments)
            poscar_comments = f'# Generated by Masgent for k-point convergence test with kppa = {kppa}.'
            write_comments(os.path.join(test_dir, 'POSCAR'), 'poscar', poscar_comments)
            kpoints = Kpoints.automatic_density(structure, kppa=kppa)
            kpoints.write_file(os.path.join(test_dir, 'KPOINTS'))
            kpoint_comments = f'# Generated by Masgent for k-point convergence test with kppa = {kppa}.'
            write_comments(os.path.join(test_dir, 'KPOINTS'), 'kpoints', kpoint_comments)

        script_path = os.path.join(kpoint_tests_dir, 'masgent_submit.sh')
        batch_script = generate_batch_script()
        with open(script_path, 'w') as f:
            f.write(batch_script)

    def test_encut():
        for encut in encut_levels:
            vis = MPStaticSet(structure, user_incar_settings={'ENCUT': encut})
            os.makedirs(encut_tests_dir, exist_ok=True)
            test_dir = os.path.join(encut_tests_dir, f'encut_{encut}')
            os.makedirs(test_dir, exist_ok=True)
            vis.incar.write_file(os.path.join(test_dir, 'INCAR'))
            vis.poscar.write_file(os.path.join(test_dir, 'POSCAR'))
            vis.kpoints.write_file(os.path.join(test_dir, 'KPOINTS'))
            vis.potcar.write_file(os.path.join(test_dir, 'POTCAR'))
            incar_comments = f'# Generated by Masgent for energy cutoff convergence test with ENCUT = {encut}.'
            write_comments(os.path.join(test_dir, 'INCAR'), 'incar', incar_comments)
            poscar_comments = f'# Generated by Masgent for energy cutoff convergence test with ENCUT = {encut}.'
            write_comments(os.path.join(test_dir, 'POSCAR'), 'poscar', poscar_comments)
            kpoint_comments = f'# Generated by Masgent for energy cutoff convergence test with ENCUT = {encut}.'
            write_comments(os.path.join(test_dir, 'KPOINTS'), 'kpoints', kpoint_comments)

        script_path = os.path.join(encut_tests_dir, 'masgent_submit.sh')
        batch_script = generate_batch_script()
        with open(script_path, 'w') as f:
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
            'kpoint_tests_dir': kpoint_tests_dir,
            'encut_tests_dir': encut_tests_dir,
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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_workflow_of_eos with input: {input}', 'green')
    
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

        for scale in scale_factors:
            scaled_structure = structure.copy()
            scaled_structure.scale_lattice(structure.volume * scale)
            vis = MPStaticSet(scaled_structure)
            scale_dir = os.path.join(eos_dir, f'scale_{scale:.3f}')
            os.makedirs(scale_dir, exist_ok=True)
            vis.incar.write_file(os.path.join(scale_dir, 'INCAR'))
            vis.poscar.write_file(os.path.join(scale_dir, 'POSCAR'))
            vis.kpoints.write_file(os.path.join(scale_dir, 'KPOINTS'))
            vis.potcar.write_file(os.path.join(scale_dir, 'POTCAR'))
            incar_comments = f'# Generated by Masgent for EOS calculation with scale factor = {scale:.3f}.'
            write_comments(os.path.join(scale_dir, 'INCAR'), 'incar', incar_comments)
            poscar_comments = f'# Generated by Masgent for EOS calculation with scale factor = {scale:.3f}.'
            write_comments(os.path.join(scale_dir, 'POSCAR'), 'poscar', poscar_comments)
            kpoint_comments = f'# Generated by Masgent for EOS calculation with scale factor = {scale:.3f}.'
            write_comments(os.path.join(scale_dir, 'KPOINTS'), 'kpoints', kpoint_comments)

        script_path = os.path.join(eos_dir, 'masgent_submit.sh')
        batch_script = generate_batch_script()
        with open(script_path, 'w') as f:
            f.write(batch_script)
        
        eos_files = list_files_in_dir(eos_dir) if os.path.exists(eos_dir) else []

        return {
            'status': 'success',
            'message': f'Generated VASP workflow of EOS calculations in {eos_dir}.',
            'eos_dir': eos_dir,
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
    # color_print(f'\n[Debug: Function Calling] generate_vasp_workflow_of_elastic_constants with input: {input}', 'green')
    
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
        lattice_matrix = structure.lattice.matrix

        # Create deformation matrixes
        xx = [-0.010, 0.010]
        yy = [-0.010, 0.010]
        zz = [-0.010, 0.010]
        xy = [-0.005, 0.005]
        yz = [-0.005, 0.005]
        xz = [-0.005, 0.005]
        D_xyz = {f'00_strain_xyz': [[1.000, 0.000, 0.000], [0.000, 1.000, 0.000], [0.000, 0.000, 1.000]]}
        D_xx0 = {f'01_strain_xx_{float(xx[0]):.3f}': [[1.000+xx[0], 0.000, 0.000], [0.000, 1.000, 0.000], [0.000, 0.000, 1.000]]}
        D_yy0 = {f'03_strain_yy_{float(yy[0]):.3f}': [[1.000, 0.000, 0.000], [0.000, 1.000+yy[0], 0.000], [0.000, 0.000, 1.000]]}
        D_zz0 = {f'05_strain_zz_{float(zz[0]):.3f}': [[1.000, 0.000, 0.000], [0.000, 1.000, 0.000], [0.000, 0.000, 1.000+zz[0]]]}
        D_xy0 = {f'07_strain_xy_{float(xy[0]):.3f}': [[1.000, xy[0], 0.000], [xy[0], 1.000, 0.000], [0.000, 0.000, 1.000]]}
        D_yz0 = {f'09_strain_yz_{float(yz[0]):.3f}': [[1.000, 0.000, 0.000], [0.000, 1.000, yz[0]], [0.000, yz[0], 1.000]]}
        D_xz0 = {f'11_strain_xz_{float(xz[0]):.3f}': [[1.000, 0.000, xz[0]], [0.000, 1.000, 0.000], [xz[0], 0.000, 1.000]]}
        D_xx1 = {f'02_strain_xx_{float(xx[1]):.3f}': [[1.000+xx[1], 0.000, 0.000], [0.000, 1.000, 0.000], [0.000, 0.000, 1.000]]}
        D_yy1 = {f'04_strain_yy_{float(yy[1]):.3f}': [[1.000, 0.000, 0.000], [0.000, 1.000+yy[1], 0.000], [0.000, 0.000, 1.000]]}
        D_zz1 = {f'06_strain_zz_{float(zz[1]):.3f}': [[1.000, 0.000, 0.000], [0.000, 1.000, 0.000], [0.000, 0.000, 1.000+zz[1]]]}
        D_xy1 = {f'08_strain_xy_{float(xy[1]):.3f}': [[1.000, xy[1], 0.000], [xy[1], 1.000, 0.000], [0.000, 0.000, 1.000]]}
        D_yz1 = {f'10_strain_yz_{float(yz[1]):.3f}': [[1.000, 0.000, 0.000], [0.000, 1.000, yz[1]], [0.000, yz[1], 1.000]]}
        D_xz1 = {f'12_strain_xz_{float(xz[1]):.3f}': [[1.000, 0.000, xz[1]], [0.000, 1.000, 0.000], [xz[1], 0.000, 1.000]]}
        D_all = [D_xyz, D_xx0, D_yy0, D_zz0, D_xy0, D_yz0, D_xz0, D_xx1, D_yy1, D_zz1, D_xy1, D_yz1, D_xz1]

        for D in D_all:
            for key, value in D.items():
                deformation_matrix = np.array(value)
                lattice_matrix_deformed = np.dot(lattice_matrix, deformation_matrix)
                structure_deformed = structure.copy()
                structure_deformed = Structure(lattice=lattice_matrix_deformed, species=structure.species, coords=structure.frac_coords)

                vis = MVLElasticSet(structure_deformed)
                deform_dir = os.path.join(elastic_dir, key)
                os.makedirs(deform_dir, exist_ok=True)
                vis.incar.write_file(os.path.join(deform_dir, 'INCAR'))
                vis.poscar.write_file(os.path.join(deform_dir, 'POSCAR'))
                vis.kpoints.write_file(os.path.join(deform_dir, 'KPOINTS'))
                vis.potcar.write_file(os.path.join(deform_dir, 'POTCAR'))
                incar_comments = f'# Generated by Masgent for elastic constants calculation with deformation {key}.'
                write_comments(os.path.join(deform_dir, 'INCAR'), 'incar', incar_comments)
                poscar_comments = f'# Generated by Masgent for elastic constants calculation with deformation {key}.'
                write_comments(os.path.join(deform_dir, 'POSCAR'), 'poscar', poscar_comments)
                kpoint_comments = f'# Generated by Masgent for elastic constants calculation with deformation {key}.'
                write_comments(os.path.join(deform_dir, 'KPOINTS'), 'kpoints', kpoint_comments)
        
        script_path = os.path.join(elastic_dir, 'masgent_submit.sh')
        batch_script = generate_batch_script()
        with open(script_path, 'w') as f:
            f.write(batch_script)

        elastic_files = list_files_in_dir(elastic_dir) if os.path.exists(elastic_dir) else []

        return {
            'status': 'success',
            'message': f'Generated VASP workflow of elastic constants calculations in {elastic_dir}.',
            'elastic_dir': elastic_dir,
            'elastic_files': elastic_files,
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'VASP elastic constants workflow generation failed: {str(e)}'
        }

@with_metadata(schemas.ToolMetadata(
    name='Run simulation using machine learning potentials (MLPs)',
    description='Run simulation using machine learning potentials (MLPs) based on given POSCAR',
    requires=[],
    optional=['poscar_path', 'mlps_type', 'fmax', 'max_steps', 'task_type'],
    defaults={
        'poscar_path': f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
        'mlps_type': 'SevenNet',
        'task_type': 'single_point',
        'fmax': 0.1,
        'max_steps': 500,
        },
    prereqs=[],
))
def run_simulation_using_mlps(
    poscar_path: str = f'{os.environ.get("MASGENT_SESSION_RUNS_DIR")}/POSCAR',
    mlps_type: Literal['SevenNet', 'CHGNet'] = 'SevenNet',
    task_type: Literal['single_point', 'eos', 'md'] = 'single_point',
    fmax: float = 0.1,
    max_steps: int = 500,
    temperature: float = 1000.0,
    md_steps: int = 1000,
    md_timestep: float = 5.0,
) -> dict:
    '''
    Run simulation using machine learning potentials (MLPs) based on given POSCAR
    '''
    # color_print(f'\n[Debug: Function Calling] run_simulation_using_mlps with input: {input}', 'green')

    def fit_and_plot_eos(volumes, energies, mlps_type, task_dir):
        volumes_fit, energies_fit = fit_eos(volumes, energies)
        eos_fit_df = pd.DataFrame({'Volume[Å³]': volumes_fit, 'Energy[eV/atom]': energies_fit})
        eos_fit_df.to_csv(f'{task_dir}/eos_fit.csv', index=False, float_format='%.8f')
        sns.set_theme(font_scale=1.2, style='whitegrid')
        matplotlib.rcParams['xtick.direction'] = 'in'
        matplotlib.rcParams['ytick.direction'] = 'in'
        fig = plt.figure(figsize=(8, 6), constrained_layout=True)
        ax = plt.subplot()
        ax.scatter(volumes, energies, color='C3', label='Calculated')
        ax.plot(volumes_fit, energies_fit, color='C0', label='Fitted')
        ax.set_xlabel('Volume (Å³)', fontsize=14)
        ax.set_ylabel('Energy (eV/atom)', fontsize=14)
        ax.set_title(f'Masgent EOS using {mlps_type}')
        ax.legend(frameon=True, loc='upper right')
        plt.savefig(f'{task_dir}/eos_curve.png', dpi=330)

    def parse_and_plot_md_log(logfile, mlps_type, task_dir):
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

        scale_factors = [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06]

        if mlps_type == 'SevenNet':
            calc = SevenNetCalculator(model='7net-0')
        elif mlps_type == 'CHGNet':
            calc = CHGNetCalculator()
        else:
            return {
                'status': 'error',
                'message': f'Invalid MLPs type: {mlps_type}.'
            }
        
        if task_type == 'single_point':
            task_dir = os.path.join(mlps_simulation_dir, 'single')
            os.makedirs(task_dir, exist_ok=True)
            atoms = read(poscar_path, format='vasp')
            atoms.calc = calc
            opt = LBFGS(FrechetCellFilter(atoms), logfile=f'{task_dir}/masgent_mlps_single.log')
            opt.run(fmax=fmax, steps=max_steps)
            atoms.write(f'{task_dir}/CONTCAR', format='vasp', direct=True, sort=True)
            comments = f'# Generated by Masgent from fast simulation using {mlps_type} with fmax = {fmax} eV/Å.'
            write_comments(f'{task_dir}/CONTCAR', 'poscar', comments)
            total_energy = atoms.get_potential_energy()
            energy_per_atom = total_energy / len(atoms)
            return {
                'status': 'success',
                'message': f'Completed fast simulation using {mlps_type} in {mlps_simulation_dir}.',
                'mlps_simulation_dir': mlps_simulation_dir,
                'simulation_log_path': f'{task_dir}/masgent_mlps_single.log',
                'contcar_path': f'{task_dir}/CONTCAR',
                'total_energy (eV)': total_energy,
                'energy_per_atom (eV/atom)': energy_per_atom,
            }
        elif task_type == 'eos':
            task_dir = os.path.join(mlps_simulation_dir, 'eos')
            os.makedirs(task_dir, exist_ok=True)
            structure = Structure.from_file(poscar_path)
            volumes, energies = [], []
            for scale in scale_factors:
                # Create scaled structure
                scaled_structure = structure.copy()
                scaled_structure.scale_lattice(structure.volume * scale)
                scaled_structure_path = os.path.join(task_dir, f'POSCAR_{scale:.3f}')
                scaled_structure.to(fmt='poscar', filename=scaled_structure_path)
                comments = f'# Generated by Masgent for EOS calculation with scale factor = {scale:.3f} using {mlps_type}.'
                write_comments(scaled_structure_path, 'poscar', comments)
                # Load scaled structure and perform optimization
                atoms = read(scaled_structure_path, format='vasp')
                atoms.calc = calc
                # opt = LBFGS(FrechetCellFilter(atoms), logfile=f'{task_dir}/masgent_mlps_eos_{scale:.3f}.log')
                opt = LBFGS(atoms, logfile=f'{task_dir}/masgent_mlps_eos_{scale:.3f}.log')
                opt.run(fmax=fmax, steps=max_steps)
                atoms.write(f'{task_dir}/CONTCAR_{scale:.3f}', format='vasp', direct=True, sort=True)
                comments = f'# Generated by Masgent from fast simulation using {mlps_type} with fmax = {fmax} eV/Å.'
                write_comments(f'{task_dir}/CONTCAR_{scale:.3f}', 'poscar', comments)
                energy_per_atom = atoms.get_potential_energy() / len(atoms)
                volumes.append(atoms.get_volume())
                energies.append(energy_per_atom)
            # Save EOS results to CSV
            pd.DataFrame({'Scale Factor': scale_factors, 'Volume (Å³)': volumes, 'Energy (eV/atom)': energies}).to_csv(f'{task_dir}/eos_cal.csv', index=False, float_format='%.8f')
            # Fit and plot EOS
            fit_and_plot_eos(volumes, energies, mlps_type, task_dir)
            return {
                'status': 'success',
                'message': f'Completed EOS simulation using {mlps_type} in {mlps_simulation_dir}.',
                'mlps_simulation_dir': mlps_simulation_dir,
                'eos_cal_csv_path': f'{task_dir}/eos_cal.csv',
                'eos_curve_png_path': f'{task_dir}/eos_curve.png',
            }
        elif task_type == 'md':
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
            'message': f'Fast simulation using MLPs failed: {str(e)}'
        }
