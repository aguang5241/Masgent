# !/usr/bin/env python3

import os, re

from ase.io import read, write
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
    prereqs: List[str] = Field([], description='List of prerequisite tools that must be run before this tool.')

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
    formula_list: List[str] = Field(
        ...,
        description='List of chemical formulas to generate POSCAR files for, e.g., ["Cu", "NaCl", "MgO"]'
    )

    @model_validator(mode="after")
    def validator(self):
        for formula in self.formula_list:
            # ensure formula is valid
            matches = re.findall(r'([A-Z][a-z]?)(\d*)', formula)
            
            # validate characters
            reconstructed = ''.join(elem + num for elem, num in matches)
            if reconstructed != formula:
                raise ValueError(f"Invalid characters in formula: {formula}")
            
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
    poscar_path: Optional[str] = Field(
        None,
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    to_cartesian: bool = Field(
        ...,
        description='If True, convert to cartesian coordinates; if False, convert to direct coordinates.'
    )

    @model_validator(mode='after')
    def validator(self):
        # set default POSCAR path if not provided
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        if self.poscar_path is None:
            self.poscar_path = os.path.join(runs_dir, 'POSCAR')

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
    Schema for generating VASP input files (INCAR, KPOINTS, POTCAR) from POSCAR using pymatgen input sets.
    '''
    poscar_path: Optional[str] = Field(
        None,
        description='Path to POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    vasp_input_sets: Literal[
        'MPRelaxSet', 'MPStaticSet', 'MPNonSCFSet',
        'MPScanRelaxSet', 'MPScanStaticSet', 'MPMDSet'
        ] = Field(
            ...,
            description='Type of Pymatgen VASP input set class to use. Must be one of the supported types.'
        )

    @model_validator(mode='after')
    def validator(self):
        # set default POSCAR path if not provided
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        if self.poscar_path is None:
            self.poscar_path = os.path.join(runs_dir, 'POSCAR')

        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')

        return self

class CustomizeVaspKpointsWithAccuracy(BaseModel):
    '''
    Schema for customizing VASP KPOINTS from POSCAR with specified accuracy level.
    '''
    poscar_path: Optional[str] = Field(
        None,
        description='Path to POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    accuracy_level: Literal[
        'Low', 'Medium', 'High'
        ] = Field(
            ...,
            description='Type of accuracy level for KPOINTS generation. Must be one of Low, Medium, or High.'
        )

    @model_validator(mode='after')
    def validator(self):
        # set default POSCAR path if not provided
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        if self.poscar_path is None:
            self.poscar_path = os.path.join(runs_dir, 'POSCAR')
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')
        
        # ensure the poscar file is valid POSCAR
        try:
            _ = Structure.from_file(self.poscar_path)
        except Exception as e:
            raise ValueError(f'Invalid POSCAR file: {self.poscar_path}')

        return self

class GenerateVaspPoscarWithVacancyDefects(BaseModel):
    '''
    Schema for generating VASP POSCAR with vacancy defects.
    '''
    poscar_path: Optional[str] = Field(
        None,
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
        # set default POSCAR path if not provided
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        if self.poscar_path is None:
            self.poscar_path = os.path.join(runs_dir, 'POSCAR')
        
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
    poscar_path: Optional[str] = Field(
        None,
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
        # set default POSCAR path if not provided
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        if self.poscar_path is None:
            self.poscar_path = os.path.join(runs_dir, 'POSCAR')
        
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
    poscar_path: Optional[str] = Field(
        None,
        description='Path to the original POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    defect_element: str = Field(
        ...,
        description='Element symbol of the defect atom.'
    )

    @model_validator(mode='after')
    def validator(self):
        # set default POSCAR path if not provided
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        if self.poscar_path is None:
            self.poscar_path = os.path.join(runs_dir, 'POSCAR')
        
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
    poscar_path: Optional[str] = Field(
        None,
        description='Path to the POSCAR file. Defaults to "POSCAR" in current directory if not provided.'
    )

    scaling_matrix: str = Field(
        ...,
        description='Scaling matrix as a string, e.g., "2 0 0; 0 2 0; 0 0 2" for a 2x2x2 supercell.'
    )

    @model_validator(mode='after')
    def validator(self):
        # set default POSCAR path if not provided
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
        if self.poscar_path is None:
            self.poscar_path = os.path.join(runs_dir, 'POSCAR')
        
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