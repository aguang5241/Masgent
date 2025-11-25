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

## Progress Record
1. Density Functional Theory (DFT) Simulations
  - 1.1 Structure Preparation & Manipulation
    - 1.1.1 Generate POSCAR from chemical formula
    - 1.1.2 Convert POSCAR coordinates (Direct <-> Cartesian)
    - 1.1.3 Convert structure file formats (CIF, POSCAR, XYZ)
    - 1.1.4 Generate structures with defects (Vacancies, Substitutions, Interstitials with Voronoi)
    - 1.1.5 Generate supercells
    - 1.1.6 (Planned) Generate special quasirandom structures (SQS)
    - 1.1.7 (Planned) Generate surface slabs
    - 1.1.8 (Planned) Generate interface structures
  
  - 1.2 VASP Input File Preparation
    - 1.2.1 Prepare full VASP input files (INCAR, KPOINTS, POTCAR, POSCAR)
    - 1.2.2 Generate INCAR templates (relaxation, static, MD, etc.)
    - 1.2.3 Generate KPOINTS with specified accuracy
    - 1.2.4 (Planned) Generate HPC job submission script
    - 1.2.5 (Planned) Generate standard VASP calculation workflows
      - 1.2.5.1 (Planned) Convergence testing (ENCUT, KPOINTS)
      - 1.2.5.2 (Planned) Equation of State (EOS)
      - 1.2.5.3 (Planned) Elastic constants
  
  - 1.3 VASP Output Analysis

2. (Planned) Machine Learning Potentials (MLP)

3. (Planned) Machine Learning Model Training & Evaluation

## Local Debugging and Testing
```bash
# Local install the package
pip install -e .

# Run tests
masgent
```

## Publishing
To publish a new version of the Masgent package to TestPyPI, follow these steps:
1. **Update Version Number**: 
   - Open the `pyproject.toml` file.
   - Locate the `version` field and update it to the new version number (e.g., `0.2.0`).
2. **Build the Package**:
    - Open a terminal and navigate to the root directory of the project.
    - Remove any previous builds to avoid conflicts:
      ```bash
      rm -rf dist/ src/*.egg-info
      ```
    - Run the following command to build the package:
      ```bash
      python3 -m build
      ```
3. **Upload to TestPyPI**:
    - (Optional) Create `~/.pypirc` file with your TestPyPI credentials:
      ```
      [testpypi]
      repository: https://test.pypi.org/legacy/
      username: __token__
      password: your-testpypi-token

      [pypi]
      repository: https://upload.pypi.org/legacy/
      username: __token__
      password: your-pypi-token
      ```
    - Use the following command to upload the built package to TestPyPI:
      ```bash
      # To upload on TestPyPI
      twine upload --repository testpypi dist/*
      
      # To upload on the official PyPI
      twine upload dist/*
      ```
4. **Verify the Upload**:
    - Go to [TestPyPI](https://test.pypi.org/) and verify that the new version of the package is listed.
5. **Install from TestPyPI** (optional):
    - To test the installation of the newly published package, you can install it using pip:
      ```bash
      pip3 install --index-url https://test.pypi.org/simple/ masgent
      ```
6. **Testing in a New Environment**:
    - Create a new virtual environment and activate it:
      ```bash
      python3 -m venv test_env
      source test_env/bin/activate
      ```
    - Install the newly published version of Masgent from TestPyPI:
      ```bash
      pip install \
      --index-url https://test.pypi.org/simple \
      --extra-index-url https://pypi.org/simple \
      masgent==0.1.6
      ```
    - Reset the virtual environment by uninstalling all packages
      ```bash
      pip freeze | xargs pip uninstall -y
      ```
    - Deactivate the virtual environment:
      ```bash
      deactivate
      ```

