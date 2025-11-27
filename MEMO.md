# Masgent
Masgent: Materials Simulation Agent

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
      python3 -m venv testing_venv
      source testing_venv/bin/activate
      ```
    - Install the newly published version of Masgent from TestPyPI:
      ```bash
      pip install \
      --index-url https://test.pypi.org/simple \
      --extra-index-url https://pypi.org/simple \
      masgent==0.2.7
      ```
    - Reset the virtual environment by uninstalling all packages
      ```bash
      pip freeze | xargs pip uninstall -y
      # Or
      pip freeze --exclude-editable | xargs pip uninstall -y
      # Or
      pip freeze | cut -d "@" -f1 | xargs pip uninstall -y
      ```

    - Deactivate the virtual environment:
      ```bash
      deactivate
      ```

