# Masgent
Masgent: Materials Simulation Agent

```bash
╔═════════════════════════════════════════════════════════════════════════╗
║                                                                         ║
║  ███╗   ███╗  █████╗  ███████╗  ██████╗  ███████╗ ███╗   ██╗ ████████╗  ║
║  ████╗ ████║ ██╔══██╗ ██╔════╝ ██╔════╝  ██╔════╝ ████╗  ██║ ╚══██╔══╝  ║
║  ██╔████╔██║ ███████║ ███████╗ ██║  ███╗ █████╗   ██╔██╗ ██║    ██║     ║
║  ██║╚██╔╝██║ ██╔══██║ ╚════██║ ██║   ██║ ██╔══╝   ██║╚██╗██║    ██║     ║
║  ██║ ╚═╝ ██║ ██║  ██║ ███████║ ╚██████╔╝ ███████╗ ██║ ╚████║    ██║     ║
║  ╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚══════╝  ╚═════╝  ╚══════╝ ╚═╝  ╚═══╝    ╚═╝     ║
║                                                                         ║
║                                   MASGENT: Materials Simulation Agent   ║
║                                      Copyright (c) 2025 Guangchen Liu   ║
║                                                                         ║
║  Licensed:        MIT License                                           ║
║  Repository:      https://github.com/aguang5241/masgent                 ║
║  Citation:        Liu, G. et al. (2025), DOI:XX.XXXX/XXXXX              ║
║  Contact:         gliu4@wpi.edu                                         ║
║                                                                         ║
╚═════════════════════════════════════════════════════════════════════════╝
```

## 🚀 Overview
Masgent is a materials simulation AI agent that streamlines **DFT workflows and analysis**, **fast machine-learning-potential (MLP) simulations**, and **lightweight ML modeling** for materials science. With automated tools for structure handling, VASP input generation, workflow preparation & analysis, and rapid property prediction, Masgent simplifies complex simulation tasks and boosts productivity for both researchers and students.

## ⭐️ Why Masgent?
Most materials-simulation tools—pymatgen, ASE, VASPkit, etc.—require manual scripting, multi-step workflows, and deep HPC expertise to run full DFT or ML-based simulations.
Masgent removes that barrier by providing a unified, AI-driven interface for structure generation, workflow preparation, fast simulations, and analysis.

**Masgent offers:**
- An AI-native simulation assistant that prepares VASP workflows, analyzes results, and answers technical questions through natural language.
- Turn-key VASP workflow templates (Convergence Test, EOS, Elastic, AIMD, NEB) with built-in analysis tools.
- Automatic generation of all VASP inputs — INCAR, KPOINTS, POTCAR, POSCAR, and HPC job scripts — with sensible defaults.
- One-command structure operations, including defect creation, supercells, slabs, interfaces, and SQS generation.
- Visualization of structures through interactive web-based viewers.
- Fast machine-learning-potential simulations using SevenNet, CHGNet, Orb-v3, and MatSim for rapid EOS, elasticity, and MD.
- Lightweight ML utilities for feature preparation, dimensionality reduction, data augmentation, hyperparameter tuning, and model training.

## 🧩 Features
1. Density Functional Theory (DFT) Simulations
  - 1.1 Structure Preparation & Manipulation
    - 1.1.1 Generate POSCAR from chemical formula
    - 1.1.2 Convert POSCAR coordinates (Direct <-> Cartesian)
    - 1.1.3 Convert structure file formats (CIF, POSCAR, XYZ)
    - 1.1.4 Generate structures with defects (Vacancies, Substitutions, Interstitials)
    - 1.1.5 Generate supercells
    - 1.1.6 Generate Special Quasirandom Structures (SQS)
    - 1.1.7 Generate surface slabs
    - 1.1.8 Generate interface structures
    - 1.1.9 Visualize structures
  
  - 1.2 VASP Input File Preparation
    - 1.2.1 Prepare full VASP input files (INCAR, KPOINTS, POTCAR, POSCAR)
    - 1.2.2 Generate INCAR templates
      - MPMetalRelaxSet: suggested for metallic structure relaxation
      - MPRelaxSet: suggested for structure relaxation
      - MPStaticSet: suggested for static calculations
      - MPNonSCFBandSet: suggested for non-self-consistent field calculations (Band structure)
      - MPNonSCFDOSSet: suggested for non-self-consistent field calculations (Density of States)
      - MPMDSet: suggested for molecular dynamics simulations
    - 1.2.3 Generate KPOINTS with specified accuracy
    - 1.2.4 Generate HPC job submission script
  
  - 1.3 Standard VASP Workflow Preparation
    - 1.3.1 Convergence test (ENCUT, KPOINTS)
    - 1.3.2 Equation of State (EOS)
    - 1.3.3 Elastic constants calculations
    - 1.3.4 Ab-initio Molecular Dynamics (AIMD)
    - 1.3.5 Nudged Elastic Band (NEB) calculations
  
  - 1.4 Standard VASP Workflow Output Analysis
    - 1.4.1 Convergence test analysis
    - 1.4.2 Equation of State (EOS) analysis
    - 1.4.3 Elastic constants analysis 
    - 1.4.4 Ab-initio Molecular Dynamics (AIMD) analysis
    - 1.4.5 Nudged Elastic Band (NEB) analysis

2. Fast Simulations Using Machine Learning Potentials (MLPs)
  - Supported MLPs:
    - 2.1 SevenNet
    - 2.2 CHGNet
    - 2.3 Orb-v3
    - 2.4 MatSim
  - Implemented Simulations for all MLPs:
    - Single Point Energy Calculation
    - Equation of State (EOS) Calculation
    - Elastic Constants Calculation
    - Molecular Dynamics Simulation (NVT)

3. Simple Machine Learning for Materials Science
  - 3.1 Data Preparation & Feature Analysis
    - 3.1.1 Feature analysis and visualization
    - 3.1.2 Dimensionality reduction (if too many features)
    - 3.1.3 Data augmentation (if limited data)
  - 3.2 Model Design & Hyperparameter Tuning
  - 3.3 Model Training & Evaluation

## 🔧 Installation
1. Requirements:
   - Python >= 3.11, < 3.14
2. Optional:
   - OpenAI API key for AI agent features: [platform.openai.com](https://platform.openai.com/account/api-keys)
   - Materials Project API key for MP structure access: [materialsproject.org](https://next-gen.materialsproject.org/api)
3. Install Masgent:
    ```bash
    pip install -U masgent
    ```
4. Setup POTCAR path for Pymatgen, see instructions: [https://pymatgen.org/installation.html#potcar-setup](https://pymatgen.org/installation.html#potcar-setup)
    

## ▶️ Usage
- After installation, simply run:
    ```bash
    masgent
    ```
- You'll guided by an interactive menu and can invoke the AI agent anytime. Ask anything in AI chat, for example:
    ```bash
    > Generate a POSCAR file for NaCl.
    > Prepare VASP input files for a graphene structure.
    > Add defects to a silicon crystal POSCAR.
    > ...
    ```

## 🐞 Issues and Suggestions
Found a bug? Have a feature request?  
Please open an issue here: [https://github.com/aguang5241/masgent/issues](https://github.com/aguang5241/masgent/issues)

## 📚 Cite Us
If you use Masgent in your research, please cite the following reference:
  ```
  @article{
    title={Masgent: A Materials Simulation Agent},
    journal={},
    volume={},
    pages={},
    year={},
    issn={},
    doi={},
  }
  ```

## 🙏 Acknowledgements
Masgent builds on the open-source materials ecosystem, including **ASE**, **Pymatgen**, **Icet**, and modern **Machine Learning Potentials**. We thank the developers of these tools for making advanced materials simulation possible.