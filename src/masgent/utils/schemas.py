# !/usr/bin/env python3

import os, re
import pandas as pd
from ase.io import read
from pymatgen.core import Structure
from pymatgen.core.periodic_table import Element

from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional, List, Dict, Any

class ToolMetadata(BaseModel):
    '''
    Schema for tool metadata information.
    '''
    name: str = Field(..., description='Name of the tool.')
    description: Optional[str] = Field(None, description='Description of the tool.')
    requires: List[str] = Field(..., description='List of required input parameters for the tool.')
    optional: List[str] = Field([], description='List of optional input parameters for the tool.')
    defaults: Dict[str, Any] = Field({}, description='Dictionary of default values for optional parameters.')
    prereqs: List[str] = Field(..., description='Prerequisite condition that must be satisfied before running the tool.')

class CheckPklFile(BaseModel):
    '''
    Schema for checking validity of a machine learning model file.
    '''
    file_path: str = Field(
        ...,
        description='Path to the machine learning model file. Must exist.'
    )
    @model_validator(mode='after')
    def validator(self):
        # ensure file exists
        if not os.path.isfile(self.file_path):
            raise ValueError(f'Model file not found: {self.file_path}')
        
        # ensure the file is a valid pkl model file
        if not self.file_path.endswith('.pkl'):
            raise ValueError(f'Invalid model file format (must be .pkl): {self.file_path}')

        return self

class CheckLogFile(BaseModel):
    '''
    Schema for checking validity of a log file.
    '''
    file_path: str = Field(
        ...,
        description='Path to the log file. Must exist.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure file exists
        if not os.path.isfile(self.file_path):
            raise ValueError(f'Log file not found: {self.file_path}')
        
        # ensure the file is a valid log file
        if not self.file_path.endswith('.log'):
            raise ValueError(f'Invalid log file format (must be .log): {self.file_path}')

        return self

class CheckCSVFile(BaseModel):
    '''
    Schema for checking validity of a CSV file.
    '''
    file_path: str = Field(
        ...,
        description='Path to the CSV file. Must exist.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure file exists
        if not os.path.isfile(self.file_path):
            raise ValueError(f'CSV file not found: {self.file_path}')
        
        # ensure the file is a valid CSV
        try:
            _ = pd.read_csv(self.file_path)
        except Exception as e:
            raise ValueError(f'Invalid CSV file: {self.file_path}')
        
        # ensure the CSV is not empty
        df = pd.read_csv(self.file_path)
        if df.empty:
            raise ValueError(f'CSV file is empty: {self.file_path}')

        return self

class CheckPoscar(BaseModel):
    '''
    Schema for checking validity of a VASP POSCAR file.
    '''
    poscar_path: str = Field(
        ...,
        description='Path to the POSCAR file. Must exist.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')

        return self
    
class CheckElement(BaseModel):
    '''
    Schema for checking validity of a chemical element symbol.
    '''
    element_symbol: str = Field(
        ...,
        description='Chemical element symbol, e.g., H, He, Li, Be, B, C, N, O, F, Ne'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure element symbol is valid
        try:
            Element(self.element_symbol)
        except:
            raise ValueError(f'Invalid chemical element symbol: {self.element_symbol}')

        return self
    
class CheckElementExistence(BaseModel):
    '''
    Schema for checking existence of a chemical element symbol in the POSCAR file.
    '''
    poscar_path: str = Field(
        ...,
        description='Path to the POSCAR file. Must exist.'
    )

    element_symbol: str = Field(
        ...,
        description='Chemical element symbol to check for existence in the POSCAR file.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            structure = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # ensure element symbol is valid
        try:
            Element(self.element_symbol)
        except:
            raise ValueError(f'Invalid chemical element symbol: {self.element_symbol}')
        
        # check existence of element in structure
        elements_in_structure = {str(site.specie) for site in structure.sites}
        if self.element_symbol not in elements_in_structure:
            raise ValueError(f'Element {self.element_symbol} does not exist in POSCAR structure.')

        return self

class GenerateVaspPoscarSchema(BaseModel):
    '''
    Schema for generating VASP POSCAR file from user inputs or from Materials Project database.
    '''
    formula: str = Field(
        ...,
        description='Chemical formula to generate POSCAR file for, e.g., "Cu", "NaCl", "MgO"'
    )

    @model_validator(mode="after")
    def validator(self):
        # ensure formula is valid
        matches = re.findall(r'([A-Z][a-z]?)(\d*)', self.formula)
        
        # validate characters
        reconstructed = ''.join(elem + num for elem, num in matches)
        if reconstructed != self.formula:
            raise ValueError(f"Invalid characters in formula: {self.formula}")
        
        # validate elements
        valid = True
        for elem, num in matches:
            try:
                Element(elem)  # will fail for invalid elements
            except:
                valid = False
                break

        if not valid:
            raise ValueError(f'Invalid chemical formula: {self.formula}')

        return self
    
class ConvertStructureFormatSchema(BaseModel):
    '''
    Schema for converting structure files between different formats (CIF, POSCAR, XYZ).
    '''
    input_path: str = Field(
        ...,
        description='Path to the input structure file. Must exist.'
    )

    input_format: Literal[
        'POSCAR', 'CIF', 'XYZ'
        ] = Field(
            ...,
            description='Format of the input structure file. Must be one of POSCAR, CIF, or XYZ.'
        )
    
    output_format: Literal[
        'POSCAR', 'CIF', 'XYZ'
        ] = Field(
            ...,
            description='Desired format of the output structure file. Must be one of POSCAR, CIF, or XYZ.'
        )

    @model_validator(mode='after')
    def validator(self):
        # ensure input file exists
        if not os.path.isfile(self.input_path):
            raise ValueError(f'Input structure file not found: {self.input_path}')
        
        # ensure the input file is valid structure file
        try:
            _ = read(self.input_path)
        except Exception as e:
            raise ValueError(f'Invalid structure file: {self.input_path}')
        
        # ensure input_format and output_format are not the same
        if self.input_format == self.output_format:
            raise ValueError('Input format and output format must be different.')

        return self
    
class ConvertPoscarCoordinatesSchema(BaseModel):
    '''
    Schema for converting POSCAR between direct and cartesian coordinates.
    '''
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    to_cartesian: bool = Field(
        ...,
        description='If True, convert to cartesian coordinates; if False, convert to direct coordinates.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')

        return self
    
class GenerateVaspInputsFromPoscar(BaseModel):
    '''
    Schema for generating VASP input files (INCAR, KPOINTS, POTCAR, POSCAR) from a given POSCAR file using pymatgen input sets.
    '''
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    vasp_input_sets: Literal[
        'MPMetalRelaxSet', 'MPRelaxSet', 'MPStaticSet',
        'MPNonSCFBandSet', 'MPNonSCFDOSSet', 'MPMDSet'
        ] = Field(
            ...,
            description='Type of Pymatgen VASP input set class to use. Must be one of the supported types.'
        )

    only_incar: bool = Field(
        False,
        description='If True, only generate the INCAR file.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')

        return self

class GenerateVaspInputsHpcSlurmScript(BaseModel):
    '''
    Schema for generating HPC Slurm job submission script for VASP calculations.
    '''
    partition: str = Field(
        'normal',
        description='Slurm partition/queue name. Defaults to "normal" if not provided.'
    )

    nodes: int = Field(
        1,
        description='Number of nodes to request. Defaults to 1 if not provided.'
    )

    ntasks: int = Field(
        8,
        description='Number of tasks (cores) to request. Defaults to 8 if not provided.'
    )

    walltime: str = Field(
        '00:10:00',
        description='Walltime limit in format HH:MM:SS. Defaults to "00:10:00" if not provided.'
    )

    jobname: str = Field(
        'masgent_job',
        description='Name of the job. Defaults to "masgent_job" if not provided.'
    )

    command: str = Field(
        'srun vasp_std > vasp.out',
        description='Command to execute the job. Defaults to "srun vasp_std > vasp.out" if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # validate nodes
        if self.nodes < 1:
            raise ValueError('Number of nodes must be at least 1.')
        
        # validate ntasks
        if self.ntasks < 1:
            raise ValueError('Number of tasks must be at least 1.')
        
        # validate walltime format HH:MM:SS
        if not re.match(r'^\d{1,2}:\d{2}:\d{2}$', self.walltime):
            raise ValueError('Walltime must be in format HH:MM:SS.')

        return self

class CustomizeVaspKpointsWithAccuracy(BaseModel):
    '''
    Schema for customizing VASP KPOINTS from POSCAR with specified accuracy level.
    '''
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    accuracy_level: Literal[
        'Low', 'Medium', 'High', 'Custom'
        ] = Field(
            ...,
            description='Type of accuracy level for KPOINTS generation. Must be one of Low, Medium, High, or Custom.'
        )
    
    gamma_centered: bool = Field(
        True,
        description='Whether to use gamma-centered k-points. Defaults to True.'
    )

    custom_kppa: Optional[int] = Field(
        None,
        description='Custom k-points per atom (kppa) value. If provided, overrides the accuracy level setting.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # validate custom_kppa if provided
        if self.custom_kppa is not None:
            if self.custom_kppa < 1:
                raise ValueError('Custom k-points per atom (kppa) must be positive integer.')

        return self

class GenerateVaspPoscarWithVacancyDefects(BaseModel):
    '''
    Schema for generating VASP POSCAR with vacancy defects.
    '''
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the original POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )
    
    original_element: str = Field(
        ...,
        description='Element symbol of the atom to be operated on.'
    )

    defect_amount: float | int = Field(
        ...,
        description='Amount of defect to introduce. Either a fraction (0 < x < 1) of the total number of original_element atoms, or an integer count (>= 1).'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            structure = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # ensure defect_amount is valid
        df = self.defect_amount
        if isinstance(df, float):
            if not (0 < df < 1):
                raise ValueError('Defect amount as a fraction must be between 0 and 1.')
        elif isinstance(df, int):
            if not (df >= 1):
                raise ValueError('Defect amount as an integer must be at least 1.')
        else:
            raise ValueError('Defect amount must be either a float (fraction) or an integer (count).')
        
        # ensure there are enough original_element atoms to remove
        total_original_atoms = sum(1 for site in structure.sites if str(site.specie) == self.original_element)
        if isinstance(df, float):
            num_defects = max(1, int(self.defect_amount * total_original_atoms))
        else:
            num_defects = self.defect_amount
        if num_defects > total_original_atoms:
            raise ValueError(f'Defect amount {num_defects} exceeds total number of {self.original_element} atoms ({total_original_atoms}).')
        
        # validate original_element
        if self.original_element:
            try:
                Element(self.original_element)
            except:
                raise ValueError(f'Invalid original element symbol: {self.original_element}')
            
            # ensure original_element exists in the POSCAR structure
            if self.original_element not in {str(site.specie) for site in structure.sites}:
                raise ValueError(f'Original element {self.original_element} does not exist in POSCAR structure.')

        return self
    
class GenerateVaspPoscarWithSubstitutionDefects(BaseModel):
    '''
    Schema for generating VASP POSCAR with substitution defects.
    '''
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the original POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )
    
    original_element: str = Field(
        ...,
        description='Element symbol of the atom to be operated on.'
    )

    defect_element: str = Field(
        ...,
        description='Element symbol of the defect atom.'
    )

    defect_amount: float | int = Field(
        ...,
        description='Amount of defect to introduce. Either a fraction (0 < x < 1) of the total number of original_element atoms, or an integer count (>= 1).'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            structure = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # ensure defect_amount is valid
        df = self.defect_amount
        if isinstance(df, float):
            if not (0 < df < 1):
                raise ValueError('Defect amount as a fraction must be between 0 and 1.')
        elif isinstance(df, int):
            if not (df >= 1):
                raise ValueError('Defect amount as an integer must be at least 1.')
        else:
            raise ValueError('Defect amount must be either a float (fraction) or an integer (count).')
        
        # ensure there are enough original_element atoms to substitute
        total_original_atoms = sum(1 for site in structure.sites if str(site.specie) == self.original_element)
        if isinstance(df, float):
            num_defects = max(1, int(self.defect_amount * total_original_atoms))
        else:
            num_defects = self.defect_amount
        if num_defects > total_original_atoms:
            raise ValueError(f'Defect amount {num_defects} exceeds total number of {self.original_element} atoms ({total_original_atoms}).')
        
        # validate original_element
        if self.original_element:
            try:
                Element(self.original_element)
            except:
                raise ValueError(f'Invalid original element symbol: {self.original_element}')
            
            # ensure original_element exists in the POSCAR structure
            if self.original_element not in {str(site.specie) for site in structure.sites}:
                raise ValueError(f'Original element {self.original_element} does not exist in POSCAR structure.')

        # validate defect_element
        if self.defect_element:
            try:
                Element(self.defect_element)
            except:
                raise ValueError(f'Invalid defect element symbol: {self.defect_element}')

        return self
    
class GenerateVaspPoscarWithInterstitialDefects(BaseModel):
    '''
    Schema for generating VASP POSCAR with interstitial (Voronoi) defects.
    '''
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the original POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    defect_element: str = Field(
        ...,
        description='Element symbol of the defect atom.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')

        # validate defect_element
        if self.defect_element:
            try:
                Element(self.defect_element)
            except:
                raise ValueError(f'Invalid defect element symbol: {self.defect_element}')

        return self

class GenerateSupercellFromPoscar(BaseModel):
    '''
    Schema for generating supercell from POSCAR file.
    '''
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    scaling_matrix: str = Field(
        ...,
        description='Scaling matrix as a string, e.g., "2 0 0; 0 2 0; 0 0 2" for a 2x2x2 supercell.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # ensure scaling_matrix is 3x3 with integer entries
        sm = self.scaling_matrix
        try:
            scaling_matrix = [
                [int(num) for num in line.strip().split()] 
                for line in sm.split(';')
                ]
            if len(scaling_matrix) != 3 or any(len(row) != 3 for row in scaling_matrix):
                raise ValueError('Scaling matrix must be 3x3.')
            
        except Exception:
            raise ValueError('Scaling matrix must be a 3x3 matrix with integer entries.')

        return self

class GenerateSqsFromPoscar(BaseModel):
    '''
    Schema for generating Special Quasirandom Structures (SQS) from a given POSCAR file.
    '''
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    target_configurations: Dict[str, Dict[str, float]] = Field(
        ...,
        description='Dictionary specifying target configurations for each sublattice. E.g., {"La": {"La": 0.5, "Y": 0.5}, "Co": {"Al": 0.75, "Co": 0.25}}'
    )

    cutoffs: List[float] = Field(
        [8.0, 4.0],
        description='List of cutoff distances (in Angstroms) for cluster expansion. Defaults to [8.0, 4.0] if not provided.'
    )

    max_supercell_size: int = Field(
        8,
        description='Maximum size of the supercell (number of primitive cells). Defaults to 8 if not provided.'
    )

    mc_steps: int = Field(
        10000,
        description='Number of Monte Carlo steps for SQS generation. Defaults to 10000 if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # validate cutoffs
        if not all(isinstance(cutoff, (float, int)) and cutoff > 0 for cutoff in self.cutoffs):
            raise ValueError('All cutoff distances must be positive numbers.')
        
        # validate target_configurations
        for sublattice, conc_dict in self.target_configurations.items():
            # validate sublattice element is valid
            try:
                Element(sublattice)
            except:
                raise ValueError(f'Invalid sublattice element symbol: {sublattice}')
            # validate sublattice element exists in the POSCAR structure
            structure = Structure.from_file(self.poscar_path)
            if sublattice not in {str(site.specie) for site in structure.sites}:
                raise ValueError(f'Sublattice element {sublattice} does not exist in POSCAR structure.')
            # validate concentration dictionary
            if not isinstance(conc_dict, dict) or not conc_dict:
                raise ValueError(f'Target configurations for sublattice {sublattice} must be a non-empty dictionary.')
            total_conc = sum(conc_dict.values())
            if abs(total_conc - 1.0) > 1e-5:
                raise ValueError(f'Target concentrations for sublattice {sublattice} must sum to 1.0. Current sum: {total_conc}')
        
        # validate max_supercell_size
        if self.max_supercell_size < 1:
            raise ValueError('Maximum supercell size must be at least 1.')
        
        # validate mc_steps
        if self.mc_steps < 1000:
            raise ValueError('Number of Monte Carlo steps must be at least 1000 for meaningful SQS generation.')

        return self
    
class GenerateSurfaceSlabFromPoscar(BaseModel):
    '''
    Schema for generating surface slab from bulk POSCAR.
    '''
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the bulk POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    miller_indices: List[int] = Field(
        ...,
        description='Miller indices [h, k, l] for the surface slab, e.g., [1, 0, 0].'
    )

    vacuum_thickness: float = Field(
        15.0,
        description='Vacuum thickness in Angstroms. Defaults to 15.0 Å if not provided.'
    )

    slab_layers: int = Field(
        4,
        description='Number of atomic layers in the slab. Defaults to 4 if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # validate miller_indices
        if len(self.miller_indices) != 3 or not all(isinstance(i, int) for i in self.miller_indices):
            raise ValueError('Miller indices must be a list of three integers [h, k, l].')
        
        # validate vacuum_thickness
        if self.vacuum_thickness <= 0:
            raise ValueError('Vacuum thickness must be a positive number.')
        
        # validate slab_layers
        if self.slab_layers < 1:
            raise ValueError('Number of slab layers must be integer at least 1.')

        return self
    
class GenerateInterfaceFromPoscars(BaseModel):
    '''
    Schema for generating interface structure from two given POSCAR files.
    '''
    
    lower_poscar_path: str = Field(
        ...,
        description='Path to the lower POSCAR file. Must exist.'
    )

    upper_poscar_path: str = Field(
        ...,
        description='Path to the upper POSCAR file. Must exist.'
    )

    lower_hkl: List[int] = Field(
        ...,
        description='Miller indices [h, k, l] for the lower structure surface.'
    )

    upper_hkl: List[int] = Field(
        ...,
        description='Miller indices [h, k, l] for the upper structure surface.'
    )

    lower_slab_layers: int = Field(
        4,
        description='Number of atomic layers in the lower slab. Defaults to 4 if not provided.'
    )

    upper_slab_layers: int = Field(
        4,
        description='Number of atomic layers in the upper slab. Defaults to 4 if not provided.'
    )

    slab_vacuum: float = Field(
        15.0,
        description='Vacuum thickness in Angstroms. Defaults to 15.0 Å if not provided.'
    )

    min_area: float = Field(
        50.0,
        description='Minimum interface area in square Angstroms. Defaults to 50.0 Å² if not provided.'
    )

    max_area: float = Field(
        500.0,
        description='Maximum interface area in square Angstroms. Defaults to 500.0 Å² if not provided.'
    )

    interface_gap: float = Field(
        2.0,
        description='Gap distance between the two slabs in Angstroms. Defaults to 2.0 Å if not provided.'
    )

    uv_tolerance: float = Field(
        5.0,
        description='Tolerance for matching in-plane lattice vectors in percentage. Defaults to 5.0% if not provided.'
    )

    angle_tolerance: float = Field(
        5.0,
        description='Tolerance for angle matching between in-plane lattice vectors in degrees. Defaults to 5.0° if not provided.'
    )

    shape_filter: bool = Field(
        False,
        description='If True, apply shape filtering to keep only the most square-like interfaces. If False, keep all matching interfaces. Defaults to False if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure lower POSCAR exists
        if not os.path.isfile(self.lower_poscar_path):
            raise ValueError(f'Lower POSCAR file not found: {self.lower_poscar_path}')
        
        # ensure the lower poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.lower_poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid lower POSCAR file: {self.lower_poscar_path}')
        
        # ensure upper POSCAR exists
        if not os.path.isfile(self.upper_poscar_path):
            raise ValueError(f'Upper POSCAR file not found: {self.upper_poscar_path}')
        
        # ensure the upper poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.upper_poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid upper POSCAR file: {self.upper_poscar_path}')
        
        # validate lower_hkl
        if len(self.lower_hkl) != 3 or not all(isinstance(i, int) for i in self.lower_hkl):
            raise ValueError('Lower Miller indices must be a list of three integers [h, k, l].')
        
        # validate upper_hkl
        if len(self.upper_hkl) != 3 or not all(isinstance(i, int) for i in self.upper_hkl):
            raise ValueError('Upper Miller indices must be a list of three integers [h, k, l].')

        # validate lower_slab_layers
        if self.lower_slab_layers < 1:
            raise ValueError('Number of lower slab layers must be integer at least 1.')
        
        # validate upper_slab_layers
        if self.upper_slab_layers < 1:
            raise ValueError('Number of upper slab layers must be integer at least 1.')
        
        # validate slab_vacuum
        if self.slab_vacuum <= 0:
            raise ValueError('Slab vacuum thickness must be a positive number.')
        
        # validate min_area and max_area
        if self.min_area <= 0 or self.max_area <= 0:
            raise ValueError('Minimum and maximum interface area must be positive numbers.')
        if self.min_area >= self.max_area:
            raise ValueError('Minimum interface area must be less than maximum interface area.')
        
        # validate interface_gap
        if self.interface_gap <= 0:
            raise ValueError('Interface gap distance must be a positive number.')
        
        # validate uv_tolerance
        if self.uv_tolerance < 0:
            raise ValueError('UV tolerance must be a non-negative number.')
        
        # validate angle_tolerance
        if self.angle_tolerance < 0:
            raise ValueError('Angle tolerance must be a non-negative number.')
        
    
class GenerateVaspWorkflowOfConvergenceTests(BaseModel):
    '''
    Schema for generating VASP input files and submit bash script for workflow of convergence tests for k-points and energy cutoff based on given POSCAR
    '''

    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    test_type: Literal['kpoints', 'encut', 'all'] = Field(
        'all',
        description='Type of convergence test to perform: "kpoints", "encut", or "all". Defaults to "all" if not provided.'
    )

    kpoint_levels: List[int] = Field(
        [1000, 2000, 3000, 4000, 5000],
        description='List of k-point density levels to test. Defaults to [1000, 2000, 3000, 4000, 5000] if not provided.'
    )

    encut_levels: List[int] = Field(
        [300, 400, 500, 600, 700],
        description='List of energy cutoff levels (in eV) to test. Defaults to [300, 400, 500, 600, 700] if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # validate kpoint_levels
        if not all(isinstance(k, int) and k > 0 for k in self.kpoint_levels):
            raise ValueError('All k-point levels must be positive integers.')
        
        # validate encut_levels
        if not all(isinstance(ec, int) and ec > 0 for ec in self.encut_levels):
            raise ValueError('All energy cutoff levels must be positive integers.')

        return self
    
class GenerateVaspWorkflowOfEos(BaseModel):
    '''
    Schema for generating VASP input files and submit bash script for workflow of equation of state (EOS) calculations based on given POSCAR
    '''
    
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    scale_factors: List[float] = Field(
        [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06],
        description='List of scale factors to apply to the lattice vectors for EOS calculations. Defaults to [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06] if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # validate scale_factors
        if not all(isinstance(sf, float) and sf > 0 for sf in self.scale_factors):
            raise ValueError('All scale factors must be positive floats.')

        return self

class GenerateVaspWorkflowOfElasticConstants(BaseModel):
    '''
    Schema for generating VASP input files and submit bash script for workflow of elastic constants calculations based on given POSCAR
    '''
    
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')

        return self
    
class GenerateVaspWorkflowOfAimd(BaseModel):
    '''
    Generate VASP input files and submit bash script for workflow of ab initio molecular dynamics (AIMD) simulations based on given POSCAR
    '''

    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    temperatures: List[int] = Field(
        [500, 1000, 1500, 2000, 2500],
        description='List of temperatures in Kelvin for AIMD simulations. Defaults to [500, 1000, 1500, 2000, 2500] K if not provided.'
    )

    md_steps: int = Field(
        1000,
        description='Number of molecular dynamics steps. Defaults to 1000 if not provided.'
    )

    md_timestep: float = Field(
        2.0,
        description='Time step in femtoseconds for AIMD simulations. Defaults to 2.0 fs if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # validate temperatures
        if not all(isinstance(temp, int) and temp > 0 for temp in self.temperatures):
            raise ValueError('All temperatures must be positive integers.')
        
        # validate md_steps
        if self.md_steps < 1:
            raise ValueError('Number of molecular dynamics steps (md_steps) must be at least 1.')
        
        # validate md_timestep
        if self.md_timestep <= 0:
            raise ValueError('Molecular dynamics time step (md_timestep) must be a positive number.')

        return self
    
class GenerateVaspWorkflowOfNeb(BaseModel):
    '''
    Schema for generating VASP input files and submit bash script for workflow of nudged elastic band (NEB) calculations based on given initial and final POSCAR files.
    '''
    
    initial_poscar_path: str = Field(
        ...,
        description='Path to the initial POSCAR file. Must exist.'
    )

    final_poscar_path: str = Field(
        ...,
        description='Path to the final POSCAR file. Must exist.'
    )

    num_images: int = Field(
        5,
        description='Number of intermediate images for NEB calculation. Defaults to 5 if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure initial POSCAR exists
        if not os.path.isfile(self.initial_poscar_path):
            raise ValueError(f'Initial POSCAR file not found: {self.initial_poscar_path}')
        
        # ensure the initial poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.initial_poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid initial POSCAR file: {self.initial_poscar_path}')
        
        # ensure final POSCAR exists
        if not os.path.isfile(self.final_poscar_path):
            raise ValueError(f'Final POSCAR file not found: {self.final_poscar_path}')
        
        # ensure the final poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.final_poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid final POSCAR file: {self.final_poscar_path}')
        
        # validate num_images
        if self.num_images < 1:
            raise ValueError('Number of intermediate images (num_images) must be at least 1.')

        return self
    
class RunSimulationUsingMlps(BaseModel):
    '''
    Schema for performing fast simulation using machine learning potentials (MLPs) based on given POSCAR.
    Supported tasks include: single point calculation, equation of state (EOS), elastic constants, and molecular dynamics (MD) simulations.
    '''
    
    poscar_path: str = Field(
        os.path.join(os.environ.get('MASGENT_SESSION_RUNS_DIR', ''), 'POSCAR'),
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    mlps_type: Literal['SevenNet', 'CHGNet', 'Orb-v3', 'MatterSim'] = Field(
        'CHGNet',
        description='Type of machine learning potentials (MLPs) to use. Defaults to "CHGNet" if not provided.'
    )

    task_type: Literal['single', 'eos', 'elastic', 'md'] = Field(
        'single',
        description='Type of simulation task to perform. Defaults to "single" if not provided.'
    )

    fmax: float = Field(
        0.1,
        description='Maximum force convergence criterion in eV/Å. Defaults to 0.1 eV/Å if not provided.'
    )

    max_steps: int = Field(
        500,
        description='Maximum number of simulation steps. Defaults to 500 if not provided.'
    )

    scale_factors: List[float] = Field(
        [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06],
        description='List of scale factors to apply to the lattice vectors for EOS calculations. Defaults to [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06] if not provided.'
    )

    temperature: int = Field(
        1000,
        description='Temperature in Kelvin for molecular dynamics simulations. Defaults to 1000 K if not provided.'
    )

    md_steps: int = Field(
        1000,
        description='Number of molecular dynamics steps. Defaults to 1000 if not provided.'
    )

    md_timestep: float = Field(
        5.0,
        description='Time step in femtoseconds for molecular dynamics simulations. Defaults to 5.0 fs if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')
        
        # validate fmax
        if self.fmax <= 0:
            raise ValueError('Maximum force convergence criterion (fmax) must be a positive number.')
        
        # validate max_steps
        if self.max_steps < 1:
            raise ValueError('Maximum number of simulation steps (max_steps) must be at least 1.')
        
        # validate scale_factors for eos task
        if self.task_type == 'eos':
            if not all(isinstance(sf, float) and sf > 0 for sf in self.scale_factors):
                raise ValueError('All scale factors must be positive floats.')
        
        # validate temperature
        if self.temperature < 0:
            raise ValueError('Temperature must be a non-negative number.')
        
        # validate md_steps
        if self.md_steps < 1:
            raise ValueError('Number of molecular dynamics steps (md_steps) must be at least 1.')
        
        # validate md_timestep
        if self.md_timestep <= 0:
            raise ValueError('Molecular dynamics time step (md_timestep) must be a positive number.')

        return self


class AnalyzeFeaturesForMachineLearning(BaseModel):
    '''
    Schema for analyzing features (correlation matrix) for machine learning based on given input and output datasets.
    '''
    input_data_path: str = Field(
        ...,
        description='Path to the input dataset file (CSV format). Must exist.'
    )

    output_data_path: str = Field(
        ...,
        description='Path to the output dataset file (CSV format). Must exist.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure input dataset exists
        if not os.path.isfile(self.input_data_path):
            raise ValueError(f'Input dataset file not found: {self.input_data_path}')
        
        # ensure output dataset exists
        if not os.path.isfile(self.output_data_path):
            raise ValueError(f'Output dataset file not found: {self.output_data_path}')
        
        # validate that both files are in CSV format
        if not self.input_data_path.lower().endswith('.csv'):
            raise ValueError('Input dataset file must be in CSV format.')
        
        if not self.output_data_path.lower().endswith('.csv'):
            raise ValueError('Output dataset file must be in CSV format.')
        
        # ensure that both files have the same number of rows
        input_df = pd.read_csv(self.input_data_path)
        output_df = pd.read_csv(self.output_data_path)
        if len(input_df) != len(output_df):
            raise ValueError('Input and output dataset files must have the same number of rows.')

        return self
    
class ReduceDimensionsForMachineLearning(BaseModel):
    '''
    Schema for reducing dimensions of features for machine learning based on given input dataset using PCA method
    '''
    input_data_path: str = Field(
        ...,
        description='Path to the input dataset file (CSV format). Must exist.'
    )

    n_components: int = Field(
        2,
        description='Number of principal components to keep. Defaults to 2 if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure input dataset exists
        if not os.path.isfile(self.input_data_path):
            raise ValueError(f'Input dataset file not found: {self.input_data_path}')
        
        # validate that the file is in CSV format
        if not self.input_data_path.lower().endswith('.csv'):
            raise ValueError('Input dataset file must be in CSV format.')
        
        # ensure n_components is valid
        if self.n_components < 1:
            raise ValueError('Number of principal components (n_components) must be at least 1.')
        
        # ensure that n_components does not exceed number of features
        input_df = pd.read_csv(self.input_data_path)
        num_features = input_df.shape[1]
        if self.n_components > num_features:
            raise ValueError(f'Number of principal components (n_components) cannot exceed number of features ({num_features}).')
        
        return self
    
class AugmentDataForMachineLearning(BaseModel):
    '''
    Schema for augmenting data for machine learning based on given input dataset using VAE-based method.
    '''
    input_data_path: str = Field(
        ...,
        description='Path to the input dataset file (CSV format). Must exist.'
    )

    output_data_path: str = Field(
        ...,
        description='Path to the output dataset file (CSV format). Must exist.'
    )

    num_augmentations: int = Field(
        100,
        description='Number of augmented data points to generate. Defaults to 100 if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure input dataset exists
        if not os.path.isfile(self.input_data_path):
            raise ValueError(f'Input dataset file not found: {self.input_data_path}')
        
        # ensure output dataset exists
        if not os.path.isfile(self.output_data_path):
            raise ValueError(f'Output dataset file not found: {self.output_data_path}')
        
        # validate that the input file is in CSV format
        if not self.input_data_path.lower().endswith('.csv'):
            raise ValueError('Input dataset file must be in CSV format.')
        
        # validate that the output file is in CSV format
        if not self.output_data_path.lower().endswith('.csv'):
            raise ValueError('Output dataset file must be in CSV format.')
        
        # ensure num_augmentations is valid
        if self.num_augmentations < 1:
            raise ValueError('Number of augmented data points (num_augmentations) must be at least 1.')

        return self
    
class DesignModelForMachineLearning(BaseModel):
    '''
    Schema for designing machine learning model using Optuna based on given input and output datasets.
    '''
    input_data_path: str = Field(
        ...,
        description='Path to the input dataset file (CSV format). Must exist.'
    )

    output_data_path: str = Field(
        ...,
        description='Path to the output dataset file (CSV format). Must exist.'
    )

    n_trials: int = Field(
        100,
        description='Number of Optuna trials for hyperparameter optimization. Defaults to 100 if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure input dataset exists
        if not os.path.isfile(self.input_data_path):
            raise ValueError(f'Input dataset file not found: {self.input_data_path}')
        
        # ensure output dataset exists
        if not os.path.isfile(self.output_data_path):
            raise ValueError(f'Output dataset file not found: {self.output_data_path}')
        
        # validate that both files are in CSV format
        if not self.input_data_path.lower().endswith('.csv'):
            raise ValueError('Input dataset file must be in CSV format.')
        
        if not self.output_data_path.lower().endswith('.csv'):
            raise ValueError('Output dataset file must be in CSV format.')
        
        # ensure that both files have the same number of rows
        input_df = pd.read_csv(self.input_data_path)
        output_df = pd.read_csv(self.output_data_path)
        if len(input_df) != len(output_df):
            raise ValueError('Input and output dataset files must have the same number of rows.')
        
        # ensure n_trials is valid
        if self.n_trials < 1:
            raise ValueError('Number of Optuna trials (n_trials) must be at least 1.')

        return self
    
class TrainModelForMachineLearning(BaseModel):
    '''
    Schema for training & evaluating machine learning model based on given input and output datasets and model hyperparameters.
    '''
    input_data_path: str = Field(
        ...,
        description='Path to the input dataset file (CSV format). Must exist.'
    )

    output_data_path: str = Field(
        ...,
        description='Path to the output dataset file (CSV format). Must exist.'
    )

    best_model_path: str = Field(
        ...,
        description='Path to the best designed model file (pickle format). Must exist.'
    )

    best_model_params_path: str = Field(
        ...,
        description='Path to the best model hyperparameters file (log format). Must exist.'
    )

    max_epochs: int = Field(
        1000,
        description='Maximum number of training epochs. Defaults to 1000 if not provided.'
    )

    patience: int = Field(
        50,
        description='Number of epochs with no improvement after which training will be stopped. Defaults to 50 if not provided.'
    )

    @model_validator(mode='after')
    def validator(self):
        # ensure input dataset exists
        if not os.path.isfile(self.input_data_path):
            raise ValueError(f'Input dataset file not found: {self.input_data_path}')
        
        # ensure output dataset exists
        if not os.path.isfile(self.output_data_path):
            raise ValueError(f'Output dataset file not found: {self.output_data_path}')
        
        # validate that both files are in CSV format
        if not self.input_data_path.lower().endswith('.csv'):
            raise ValueError('Input dataset file must be in CSV format.')
        
        if not self.output_data_path.lower().endswith('.csv'):
            raise ValueError('Output dataset file must be in CSV format.')
        
        # ensure that both files have the same number of rows
        input_df = pd.read_csv(self.input_data_path)
        output_df = pd.read_csv(self.output_data_path)
        if len(input_df) != len(output_df):
            raise ValueError('Input and output dataset files must have the same number of rows.')
        
        # ensure best model file exists
        if not os.path.isfile(self.best_model_path):
            raise ValueError(f'Best model file not found: {self.best_model_path}')
        
        # ensure best model params file exists
        if not os.path.isfile(self.best_model_params_path):
            raise ValueError(f'Best model hyperparameters file not found: {self.best_model_params_path}')
        
        # validate that best model file is in pickle format
        if not self.best_model_path.lower().endswith('.pkl'):
            raise ValueError('Best model file must be in pickle (.pkl) format.')
        
        # validate that best model params file is in log format
        if not self.best_model_params_path.lower().endswith('.log'):
            raise ValueError('Best model hyperparameters file must be in log (.log) format.')
        
        # ensure max_epochs is valid
        if self.max_epochs < 1:
            raise ValueError('Maximum number of training epochs (max_epochs) must be at least 1.')
        
        # ensure patience is valid
        if self.patience < 1:
            raise ValueError('Patience must be at least 1.')

        return self