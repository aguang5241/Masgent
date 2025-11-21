# Masgent
Masgent: Materials Simulation Agent

## Progress Record
### Features Implemented
- Developed using pydantic-ai for AI agent framework
- Implemented AI backend with OpenAI chat model
- Integrated MPRester for Materials Project database access
- Distributed as a Python package via TestPyPI
- Robust system prompts to guide AI behavior
- Strict input validation for all functions using Pydantic schemas
- Comprehensive error handling and user prompts
- API key management and validation for OpenAI and Materials Project
- Color-coded terminal outputs for better user experience
- Implemented logical workflow to switch between console and AI modes
- Call AI assistant anytime during console mode for help or suggestions
- Message history management to keep recent interactions to optimize performance

### Features Planned
- Expand toolset for more materials science tasks
- Console mode functions for direct user interaction

### Functions Implemented
- Generate VASP POSCAR file from chemical formula
  - Validate chemical formula input
  - Support fetching structures from Materials Project database

- Generate suggested VASP input files (INCAR, KPOINTS, POTCAR)
  - Support calculations:
    - `MPRelaxSet`: for relaxation calculations
    - `MPStaticSet`: for static calculations
    - `MPNonSCFSet`: for non-self-consistent field calculations
    - `MPScanRelaxSet`: for r2scan relaxation calculations
    - `MPScanStaticSet`: for r2scan static calculations
    - `MPMDSet`: for molecular dynamics simulations

- Customize KPOINTS file for provided POSCAR with specified accuracy level
  - Support accuracy levels:
    - `Low`
    - `Medium`
    - `High`

- Convert structures between different formats (CIF, POSCAR, XYZ, etc.)
  - Support conversions:
    - `POSCAR` <-> `CIF`
    - `POSCAR` <-> `XYZ`
    - `CIF` <-> `XYZ`

- Convert POSCAR between direct and cartesian coordinates
  - Support conversions:
    - `Direct` <-> `Cartesian`

- Generate defects in crystal structures
  - Support defect types:
    - `Vacancies`: remove specified fraction or number of atoms of a given element
    - `Interstitials`: add specified fraction or number of atoms of a given element
    - `Substitutions`: replace specified fraction or number of atoms of a given element with another element

### Functions Planned
- Generate script for HPC job submission
  - Support job schedulers:
    - SLURM

- Generate SQS structures using icet
  - Support input parameters:
    - Supercell size
    - Correlation functions
    - Number of iterations

- Generate surface slabs from bulk structures
  - Support input parameters:
    - Miller indices
    - Slab thickness
    - Vacuum size

- Generate interfaces between two materials
  - Support input parameters:
    - Lattice matching criteria
    - Interface orientation
    - Separation distance

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
    - It is recommended to test the installation in a new virtual environment to ensure that all dependencies are correctly specified and installed.
      ```
      python3 -m venv test_env
      source test_env/bin/activate
      pip install \
      --index-url https://test.pypi.org/simple \
      --extra-index-url https://pypi.org/simple \
      masgent==0.1.6

      ```
    - Reset the virtual environment by uninstalling all packages
      ```bash
      pip freeze | xargs pip uninstall -y
      ```

