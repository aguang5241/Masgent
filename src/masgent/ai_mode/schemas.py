# masgent/ai_mode/schemas.py

import os, re
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, ClassVar, Dict

class GenerateSimplePOSCARSchema(BaseModel):
    '''
    Schema for generating a simple bulk POSCAR.

    AI must confirm missing parameters with the user.
    '''

    name: str = Field(..., description="Chemical formula, e.g., Cu, NaCl, MgO")

    crystalstructure: Literal[
        'sc', 'fcc', 'bcc',
        'tetragonal', 'bct',
        'hcp', 'rhombohedral',
        'orthorhombic', 'mcl',
        'diamond', 'zincblende',
        'rocksalt', 'cesiumchloride',
        'fluorite', 'wurtzite'
    ] = Field(
        ...,
        description="Crystal structure type."
    )

    a: Optional[float] = None
    b: Optional[float] = None
    c: Optional[float] = None
    alpha: Optional[float] = None

    ATOM_COUNT: ClassVar[Dict[str, int]] = {
        'sc': 1, 'fcc': 1, 'bcc': 1, 'hcp': 1, 'bct': 1, 'mcl': 1,
        'tetragonal': 1, 'rhombohedral': 1, 'orthorhombic': 1, 'diamond': 1,
        'zincblende': 2, 'rocksalt': 2, 'cesiumchloride': 2, 'wurtzite': 2, 
        'fluorite': 3,
    }

    @model_validator(mode="after")
    def validate_structure_params(self):
        # Validate that the provided parameters are sufficient for the given crystal structure.
        formula = self.name
        parsed = re.findall(r"([A-Z][a-z]*)(\d*)", formula)
        total_atoms = 0
        elements = set()
        for elem, num in parsed:
            elements.add(elem)
            total_atoms += int(num) if num else 1
        required_atoms = self.ATOM_COUNT[self.crystalstructure]
        if total_atoms != required_atoms:
            raise ValueError(
                f'The "{self.crystalstructure}" structure requires {required_atoms} atoms per primitive cell, '
                f'but "{self.name}" contains {total_atoms} atoms. '
                f'The function only support formulas with maximum 3 atoms for POSCAR generation.'
            )

        # Basic positivity checks
        for name in ['a', 'b', 'c']:
            val = getattr(self, name)
            if val is not None and val <= 0:
                raise ValueError(f"Lattice constant {name} must be > 0.")

        cs = self.crystalstructure

        # --- Cubic / simple cubic families ---
        cubic_structs = {
            'sc', 'fcc', 'bcc', 'diamond', 'zincblende',
            'rocksalt', 'cesiumchloride', 'fluorite'
        }
        if cs in cubic_structs:
            if self.a is None:
                raise ValueError(f'Cubic-like structure "{cs}" requires lattice constant a.')
            self.b = self.b or self.a
            self.c = self.c or self.a
            self.alpha = self.alpha or 90.0
            return self

        # --- HCP / Tetragonal / BCT---
        if cs in { 'hcp', 'tetragonal', 'bct' }:
            if self.a is None or self.c is None:
                raise ValueError('HCP/Tetragonal/BCT structures require both a and c.')
            self.b = self.b or self.a
            self.alpha = self.alpha or 90.0
            return self

        # --- Orthorhombic ---
        if cs == 'orthorhombic':
            if not (self.a and self.b and self.c):
                raise ValueError("Orthorhombic requires a, b, and c.")
            self.alpha = self.alpha or 90.0
            return self

        # --- Rhombohedral ---
        if cs == 'rhombohedral':
            if self.a is None or self.alpha is None:
                raise ValueError('Rhombohedral requires both a and alpha.')
            return self

        # --- mcl or others (if ASE supports them) ---
        self.alpha = self.alpha or 90.0

        return self
    
class GenerateIncarFromPoscar(BaseModel):
    '''
    Schema for generating VASP INCAR from POSCAR using pymatgen input sets.

    AI must confirm missing parameters with the user.
    '''
    poscar_path: str = Field(
        ...,
        description='Path to POSCAR/CONTCAR file. Must exist.'
    )

    vasp_input_sets: Literal[
        'MPRelaxSet', 'MPStaticSet', 'MPNonSCFSet',
        'MPScanRelaxSet', 'MPScanStaticSet', 'MPMDSet'
        ] = Field(
            ...,
            description='Type of Pymatgen VASP input set class to use. Must be one of the supported types.'
        )
    
    user_incar_settings: Optional[dict] = Field(
        None,
        description='Optional INCAR overrides to pass into the pymatgen input set.'
    )

    @model_validator(mode='after')
    def model_validator(self):
        # ensure POSCAR exists
        if not os.path.isfile(self.poscar_path):
            raise ValueError(f'POSCAR file not found: {self.poscar_path}')

        return self

