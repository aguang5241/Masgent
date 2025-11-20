# Masgent
Masgent: A Materials Simulation AI Agent Framework

## Local Debugging and Testing
```bash
pip install -e .
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


## Progress
- Generate simple POSCAR files
  - Support crystal structures:
    - `sc`: Simple Cubic
    - `fcc`: Face-Centered Cubic
    - `bcc`: Body-Centered Cubic
    - `hcp`: Hexagonal Close-Packed
    - `bct`: Body-Centered Tetragonal
    - `mcl`: Monoclinic
    - `tetragonal`: Tetragonal
    - `rhombohedral`: Rhombohedral
    - `orthorhombic`: Orthorhombic
    - `diamond`: Diamond Structure
    - `zincblende`: Zinc Blende Structure
    - `rocksalt`: Rock Salt Structure
    - `cesiumchloride`: Cesium Chloride Structure
    - `wurtzite`: Wurtzite Structure
    - `fluorite`: Fluorite Structure

- Generate VASP input files for provided POSCAR
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