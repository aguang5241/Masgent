# Masgent
Masgent: Materials Simulation Agent

## Features
- AI agent (Pydantic AI + OpenAI)
- Materials Project access
- Distributed as a Python package
- Robust system prompts to guide AI behavior
- Strict input validation (Pydantic schemas)
- API key management and validation
- Interactive command selection menu (Bullet)
- Color-coded terminal interface (Colorama)
- AI standby for instant assistance
- Smart memory management
- Detailed user guidance
- Spinner for AI response waiting time (Yaspin)
- Automated file handling and management

## Progress Record
1. Density Functional Theory (DFT) Simulations
  - 1.1 Structure Preparation & Manipulation
    - 1.1.1 Generate POSCAR from chemical formula
    - 1.1.2 Convert POSCAR coordinates (Direct <-> Cartesian)
    - 1.1.3 Convert structure file formats (CIF, POSCAR, XYZ)
    - 1.1.4 Generate structures with defects (Vacancies, Substitutions, Interstitials with Voronoi)
    - 1.1.5 Generate supercells
    - 1.1.6 Generate Special Quasirandom Structures (SQS)
    - 1.1.7 Generate surface slabs
    - 1.1.8 Generate interface structures
  
  - 1.2 VASP Input File Preparation
    - 1.2.1 Prepare full VASP input files (INCAR, KPOINTS, POTCAR, POSCAR)
    - 1.2.2 Generate INCAR templates (relaxation, static, etc.)
    - 1.2.3 Generate KPOINTS with specified accuracy
    - 1.2.4 Generate HPC job submission script
  
  - 1.3 Standard VASP Workflows
      - 1.3.1 Convergence testing (ENCUT, KPOINTS)
      - 1.3.2 Equation of State (EOS)
      - 1.3.3 Elastic constants calculations
  
  - 1.4 (Planned) VASP Output Analysis

2. Fast Simulations Using Machine Learning Potentials (MLPs)
  - Supported MLPs:
    - 2.1 SevenNet
    - 2.2 CHGNet
    - 2.3 Orb-v3
  - Implemented Simulations for all MLPs:
    - Single Point Energy Calculation
    - Equation of State (EOS) Calculation
    - Elastic Constants Calculation
    - Molecular Dynamics Simulation (NVT)

3. (Planned) Machine Learning Model Training & Evaluation

## Installation
1. Requirements:
   - Python >= 3.11, < 3.14
2. Install via pip:
  ```bash
  pip install masgent
  ```

## Usage
1. After installation, run the following command to start the Masgent:
  ```bash
  masgent
  ```
2. Optional preparation:
- For AI functionalities, obtain your OpenAI API key from [platform.openai.com](https://platform.openai.com/account/api-keys).
- For Materials Project access, obtain your API key from [materialsproject.org](https://next-gen.materialsproject.org/api).