# masgent/ai_mode/schemas.py

import re
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal

Generate_Simple_POSCAR_ATOM_COUNT = {
    'sc': 1, 'fcc': 1, 'bcc': 1,
    'tetragonal': 1,
    'bct': 1,
    'hcp': 1,
    'rhombohedral': 1,
    'orthorhombic': 1,
    'mcl': 1,
    'diamond': 1,
    'zincblende': 2,
    'rocksalt': 2,
    'cesiumchloride': 2,
    'fluorite': 3,
    'wurtzite': 2,
}

class GenerateSimplePOSCARSchema(BaseModel):
    '''
    Schema for generating a simple bulk POSCAR.

    AI must confirm missing parameters with the user.
    '''

    name: str = Field(..., description="Chemical formula, e.g., Cu, NaCl, Al2O3.")

    crystalstructure: Literal[
        'sc', 'fcc', 'bcc',
        'tetragonal', 'bct',
        'hcp', 'rhombohedral',
        'orthorhombic', 'mcl',
        'diamond', 'zincblende',
        'rocksalt', 'cesiumchloride',
        'fluorite', 'wurtzite'
    ]

    a: Optional[float] = None
    b: Optional[float] = None
    c: Optional[float] = None
    alpha: Optional[float] = None

    generate_vasp_inputs: bool = Field(
        ...,
        description='Whether to generate INCAR/KPOINTS/POTCAR (must be explicitly provided by the user).'
    )

    ATOM_COUNT = {
        'sc': 1, 'fcc': 1, 'bcc': 1,
        'tetragonal': 1,
        'bct': 1,
        'hcp': 1,
        'rhombohedral': 1,
        'orthorhombic': 1,
        'mcl': 1,
        'diamond': 1,
        'zincblende': 2,
        'rocksalt': 2,
        'cesiumchloride': 2,
        'fluorite': 3,
        'wurtzite': 2,
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

        # Print debug info
        print(f"[Debug] Structure '{cs}' with parameters: a={self.a}, b={self.b}, c={self.c}, alpha={self.alpha}")

        return self
