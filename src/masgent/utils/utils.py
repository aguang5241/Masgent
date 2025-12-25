# !/usr/bin/env python3

import os, sys, datetime, time
import numpy as np
from pathlib import Path
from colorama import Fore, Style
from importlib.metadata import version, PackageNotFoundError

def visualize_structure(poscar_path, save_path):
    from pymatgen.core import Structure
    import json

    structure = Structure.from_file(poscar_path)
    cif_str = structure.to(fmt='cif')

    # Default radii
    atom_radii_real = {
        'H': 0.46, 'He': 1.22, 'Li': 1.57, 'Be': 1.12, 'B': 0.81, 'C': 0.77, 'N': 0.74, 'O': 0.74, 'F': 0.72, 'Ne': 1.60,
        'Na': 1.91, 'Mg': 1.60, 'Al': 1.43, 'Si': 1.18, 'P': 1.10, 'S': 1.04, 'Cl': 0.99, 'Ar': 1.92, 'K': 2.35, 'Ca': 1.97,
        'Sc': 1.64, 'Ti': 1.47, 'V': 1.35, 'Cr': 1.29, 'Mn': 1.37, 'Fe': 1.26, 'Co': 1.25, 'Ni': 1.25, 'Cu': 1.28, 'Zn': 1.37,
        'Ga': 1.53, 'Ge': 1.22, 'As': 1.21, 'Se': 1.04, 'Br': 1.14, 'Kr': 1.98, 'Rb': 2.50, 'Sr': 2.15, 'Y': 1.82, 'Zr': 1.60,
        'Nb': 1.47, 'Mo': 1.40, 'Tc': 1.35, 'Ru': 1.34, 'Rh': 1.34, 'Pd': 1.37, 'Ag': 1.44, 'Cd': 1.52, 'In': 1.67, 'Sn': 1.58,
        'Sb': 1.41, 'Te': 1.37, 'I': 1.33, 'Xe': 2.18, 'Cs': 2.71, 'Ba': 2.24, 'La': 1.88, 'Ce': 1.82, 'Pr': 1.82, 'Nd': 1.82,
        'Pm': 1.81, 'Sm': 1.81, 'Eu': 2.06, 'Gd': 1.79, 'Tb': 1.77, 'Dy': 1.77, 'Ho': 1.76, 'Er': 1.75, 'Tm': 1.00, 'Yb': 1.94,
        'Lu': 1.72, 'Hf': 1.59, 'Ta': 1.47, 'W': 1.41, 'Re': 1.37, 'Os': 1.35, 'Ir': 1.36, 'Pt': 1.39, 'Au': 1.44, 'Hg': 1.55,
        'Tl': 1.71, 'Pb': 1.75, 'Bi': 1.82, 'Po': 1.77, 'At': 0.62, 'Rn': 0.80, 'Fr': 1.00, 'Ra': 2.35, 'Ac': 2.03, 'Th': 1.80,
        'Pa': 1.63, 'U': 1.56, 'Np': 1.56, 'Pu': 1.64, 'Am': 1.73, 'Cm': 0.80, 'Bk': 0.80, 'Cf': 0.80, 'Es': 0.80, 'Fm': 0.80,
        'Md': 0.80, 'No': 0.80, 'Lr': 0.80, 'Rf': 0.80, 'Db': 0.80, 'Sg': 0.80, 'Bh': 0.80, 'Hs': 0.80, 'Mt': 0.80, 'Ds': 0.80,
        'Rg': 0.80, 'Cn': 0.80, 'Nh': 0.80, 'Fl': 0.80, 'Mc': 0.80, 'Lv': 0.80, 'Ts': 0.80, 'Og': 0.80,
    }
    # Scale radii for better visualization
    atom_radii_scaled = {elem: radius * 0.3 for elem, radius in atom_radii_real.items()}
    atom_radii_js = json.dumps(atom_radii_scaled)

    # Create HTML content
    html = f'''
    <html>
    <head>
    <script src='https://3Dmol.org/build/3Dmol.js'></script>
    <style>
        body {{ 
            margin: 0; 
            overflow: hidden; 
        }}

        #viewer {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}

        .overlay {{
            position: absolute;
            background: rgba(255, 255, 255, 0.85);
            border-radius: 6px;
            padding: 8px 12px;
            font-family: Arial, sans-serif;
            font-size: 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }}

        #title {{ 
            top: 10px; 
            left: 10px;
            font-weight: bold;
            font-size: 20px;
        }}

        #legend {{ 
            top: 10px; 
            right: 10px; 
        }}

        #instructions {{ 
            bottom: 10px; 
            right: 10px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}

        .color-box {{
            width: 20px;
            height: 20px;
            margin-right: 6px;
            border: 1px solid #444;
            border-radius: 10px;
        }}

        #controls {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            display: flex;
            gap: 8px;
        }}

        .control-btn {{
            padding: 6px 12px;
            font-size: 14px;
            border-radius: 4px;
            border: 1px solid #444;
            background: white;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .control-btn:hover {{
            background: #f0f0f0;
        }}
    </style>
    </head>

    <body>
    <div id='viewer'></div>

    <div id="controls">
        <button class="control-btn" onclick="rotateX()">Rotate X</button>
        <button class="control-btn" onclick="rotateY()">Rotate Y</button>
        <button class="control-btn" onclick="rotateZ()">Rotate Z</button>
        <button class="control-btn" onclick="resetView()">Reset</button>
        <button class="control-btn" onclick="save()">Save</button>
    </div>

    <div id='title' class='overlay'>
        Masgent Structure Viewer (Powered by 3Dmol.js)
    </div>

    <div id='legend' class='overlay'>
        <strong>Elements</strong>
        <div id='legend-items'></div>
    </div>

    <div id='instructions' class='overlay'>
        <strong>Instructions:</strong><br>
        * Drag to rotate<br>
        * Scroll to zoom
    </div>

    <script>
        let viewer = $3Dmol.createViewer('viewer', {{ backgroundColor: 'white' }});
        viewer.setProjection('orthographic');
        viewer.addModel(`{cif_str}`, 'cif');

        const atomRadii = {atom_radii_js};

        // Apply custom radii
        Object.entries(atomRadii).forEach(([elem, radius]) => {{
            viewer.setStyle(
                {{ elem: elem }},
                {{ sphere: {{ scale: radius, colorscheme: 'Jmol' }} }}
            );
        }});

        viewer.addUnitCell();
        viewer.zoomTo();
        viewer.render();

        const baseView = viewer.getView();

        // View control functions
        function rotateX() {{
            viewer.rotate(15, 'x');
            viewer.render();
        }}

        function rotateY() {{
            viewer.rotate(15, 'y');
            viewer.render();
        }}

        function rotateZ() {{
            viewer.rotate(15, 'z');
            viewer.render();
        }}

        function resetView() {{
            viewer.setView(baseView);
            viewer.zoomTo();
            viewer.render();
        }}

        // Save function
        function save() {{
            const canvas = viewer.getCanvas();

            // Save original size
            const originalWidth = canvas.width;
            const originalHeight = canvas.height;

            // Increase resolution (2x for publication quality)
            const scale = window.devicePixelRatio || 2;
            canvas.width = originalWidth * scale;
            canvas.height = originalHeight * scale;

            viewer.render();

            // Export image
            const dataURL = canvas.toDataURL("image/png");
            const link = document.createElement('a');
            link.href = dataURL;
            link.download = 'structure.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Restore original size
            canvas.width = originalWidth;
            canvas.height = originalHeight;
            viewer.render();
        }}

        // Build legend from Jmol colors of displayed elements
        const atoms = viewer.getModel().selectedAtoms();
        const elements = [...new Set(atoms.map(a => a.elem))].sort();

        const legend = document.getElementById('legend-items');
        elements.forEach(el => {{
            const color = $3Dmol.elementColors.Jmol[el] || 0xAAAAAA;
            const hex = '#' + color.toString(16).padStart(6, '0');

            const item = document.createElement('div');
            item.className = 'legend-item';

            const box = document.createElement('div');
            box.className = 'color-box';
            box.style.background = hex;

            const label = document.createElement('span');
            label.textContent = el;

            item.appendChild(box);
            item.appendChild(label);
            legend.appendChild(item);
        }});
    </script>
    </body>
    </html>
    '''

    # Save HTML file
    with open(save_path, 'w') as f:
        f.write(html)

def create_deformation_matrices():
    xx = [-0.010, 0.010]
    yy = [-0.010, 0.010]
    zz = [-0.010, 0.010]
    xy = [-0.005, 0.005]
    yz = [-0.005, 0.005]
    xz = [-0.005, 0.005]
    D_000 = {f'00_strain_0.000': [
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, 0.000]]}
    D_xx0 = {f'01_strain_xx_{float(xx[0]):.3f}': [
        [xx[0], 0.000, 0.000], 
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, 0.000]]}
    D_yy0 = {f'03_strain_yy_{float(yy[0]):.3f}': [
        [0.000, 0.000, 0.000], 
        [0.000, yy[0], 0.000], 
        [0.000, 0.000, 0.000]]}
    D_zz0 = {f'05_strain_zz_{float(zz[0]):.3f}': [
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, zz[0]]]}
    D_xy0 = {f'07_strain_xy_{float(xy[0]):.3f}': [
        [0.000, xy[0], 0.000], 
        [xy[0], 0.000, 0.000], 
        [0.000, 0.000, 0.000]]}
    D_yz0 = {f'09_strain_yz_{float(yz[0]):.3f}': [
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, yz[0]], 
        [0.000, yz[0], 0.000]]}
    D_xz0 = {f'11_strain_xz_{float(xz[0]):.3f}': [
        [0.000, 0.000, xz[0]], 
        [0.000, 0.000, 0.000], 
        [xz[0], 0.000, 0.000]]}
    D_xx1 = {f'02_strain_xx_{float(xx[1]):.3f}': [
        [xx[1], 0.000, 0.000], 
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, 0.000]]}
    D_yy1 = {f'04_strain_yy_{float(yy[1]):.3f}': [
        [0.000, 0.000, 0.000], 
        [0.000, yy[1], 0.000], 
        [0.000, 0.000, 0.000]]}
    D_zz1 = {f'06_strain_zz_{float(zz[1]):.3f}': [
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, zz[1]]]}
    D_xy1 = {f'08_strain_xy_{float(xy[1]):.3f}': [
        [0.000, xy[1], 0.000], 
        [xy[1], 0.000, 0.000], 
        [0.000, 0.000, 0.000]]}
    D_yz1 = {f'10_strain_yz_{float(yz[1]):.3f}': [
        [0.000, 0.000, 0.000], 
        [0.000, 0.000, yz[1]], 
        [0.000, yz[1], 0.000]]}
    D_xz1 = {f'12_strain_xz_{float(xz[1]):.3f}': [
        [0.000, 0.000, xz[1]], 
        [0.000, 0.000, 0.000], 
        [xz[1], 0.000, 0.000]]}
    D_all = [D_000, D_xx0, D_yy0, D_zz0, D_xy0, D_yz0, D_xz0, D_xx1, D_yy1, D_zz1, D_xy1, D_yz1, D_xz1]
    return D_all

def eos_func(volume, a, b, c, d):
    energy = a + b * volume**(-2/3) + c * volume**(-4/3) + d * volume**(-2)
    return energy

def fit_eos(volumes, energies):
    from scipy.optimize import curve_fit

    volumes_fit = np.linspace(min(volumes) * 0.99, max(volumes) * 1.01, 100)
    popt, pcov = curve_fit(eos_func, volumes, energies)
    energies_fit = eos_func(volumes_fit, *popt)
    return volumes_fit, energies_fit

def list_files_in_dir(dir):
    '''List all files in a directory and its subdirectories.'''
    base_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
    all_files = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            all_files.append(os.path.join(base_dir, file))
    return all_files

def start_new_session():
    '''Set up a new session runs directory.'''
    base_dir = os.getcwd()
    main_dir = os.path.join(base_dir, 'masgent_projects')
    os.makedirs(main_dir, exist_ok=True)
    
    # Create a new runs directory with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    runs_dir = os.path.join(main_dir, f'runs_{timestamp}')
    if not os.path.exists(runs_dir):
        os.makedirs(runs_dir, exist_ok=True)
    else:
        # Rare collision case, wait a second and try again
        time.sleep(1)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        runs_dir = os.path.join(main_dir, f'runs_{timestamp}')
        os.makedirs(runs_dir, exist_ok=True)

    os.environ['MASGENT_SESSION_RUNS_DIR'] = runs_dir

def exit_and_cleanup():
    '''Exit Masgent and clean up empty runs directory.'''
    runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')
    if runs_dir and os.path.exists(runs_dir) and not os.listdir(runs_dir):
        os.rmdir(runs_dir)
    color_print('\nExiting Masgent... Goodbye!\n', 'green')
    sys.exit(0)

def global_commands():
    return [
        '',
        'AI    ->  Chat with the Masgent AI',
        'New   ->  Start a new session',
        'Back  ->  Return to previous menu',
        'Main  ->  Return to main menu',
        'Help  ->  Show available functions',
        'Exit  ->  Quit the Masgent',
    ]

def write_comments(file, file_type, comments):
    with open(file, 'r') as f:
        lines = f.readlines()

    if file_type.lower() in {'poscar', 'kpoints'}:
        lines[0] = comments + '\n'
    
    elif file_type.lower() in {'incar'}:
        lines.insert(0, f'{comments}\n')
    
    with open(file, 'w') as f:
        f.writelines(lines)

def generate_submit_script():
    '''
    Generate a basic Slurm submission script for VASP jobs.
    '''
    scripts = '''#!/bin/bash
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --time=01:00:00
#SBATCH --job-name=masgent_job
#SBATCH --output=masgent_job.out
#SBATCH --error=masgent_job.err

# This Slurm script was generated by Masgent, customize as needed.

time srun vasp_std > vasp.out
'''
    return scripts

def generate_batch_script(update_incar=True, update_kpoints=True):
    '''
    Generate batch script for HPC job submission.
    '''
    script_lines = []
    script_lines.append('''#!/bin/bash

# This script was generated by Masgent to update VASP input files and submit jobs.
# After modifying the template files (INCAR_temp, KPOINTS_temp, POTCAR_temp,
# and submit_temp.sh, if present), run:
#   bash ./RUN_ME.sh

# Update VASP inputs in each folder
for d in */; do
    cp POTCAR_temp  "$d/POTCAR"
''')
    if update_incar:
        script_lines.append('''
    cp INCAR_temp  "$d/INCAR"
''')
    if update_kpoints:
        script_lines.append('''
    cp KPOINTS_temp  "$d/KPOINTS"
''')
    script_lines.append('''
done

# Update submit script and submit jobs in each folder
for d in */; do
    cp submit_temp.sh  "$d/submit.sh"
    chmod +x "$d/submit.sh"
    cd "$d"
    sbatch submit.sh
    cd ..
done
''')
    scripts = ''.join(script_lines)
    return scripts

def get_color_map():
    return {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'blue': Fore.BLUE,
        'magenta': Fore.MAGENTA,
        'cyan': Fore.CYAN,
        'white': Fore.WHITE,
    }

def color_print(text, color='cyan'):
    '''Print text in specified color.'''
    color_map = get_color_map()
    chosen_color = color_map.get(color.lower(), Fore.CYAN)
    print(chosen_color + text + Style.RESET_ALL)

def color_input(text, color='cyan'):
    '''Input prompt in specified color.'''
    color_map = get_color_map()
    chosen_color = color_map.get(color.lower(), Fore.CYAN)
    return input(chosen_color + text + Style.RESET_ALL)

def load_system_prompts():
    # src/masgent/ai_mode/system_prompt.txt
    prompts_path = Path(__file__).resolve().parent.parent / 'ai_mode' / 'system_prompt.txt'
    try:
        return prompts_path.read_text(encoding='utf-8')
    except Exception as e:
        return f'Error loading system prompts: {str(e)}'

def validate_openai_api_key(key):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        client.models.list()
        # color_print('[Info] OpenAI API key validated successfully.\n', 'green')
    except Exception as e:
        color_print('[Error] Invalid OpenAI API key. Exiting...\n', 'green')
        sys.exit(1)

def ask_for_openai_api_key():
    key = color_input('Enter your OpenAI API key: ', 'yellow').strip()
    if not key:
        color_print('[Error] OpenAI API key cannot be empty. Exiting...\n', 'green')
        sys.exit(1)
    
    validate_openai_api_key(key)

    os.environ['OPENAI_API_KEY'] = key

    save = color_input('Save this key to .env file for future? (y/n): ', 'yellow').strip().lower()
    base_dir = os.getcwd()
    env_path = os.path.join(base_dir, '.env')
    if save == 'y':
        with open(env_path, 'w') as f:
            f.write(f'OPENAI_API_KEY={key}\n')
        color_print(f'[Info] OpenAI API key saved to {env_path} file.\n', 'green')
    
def validate_mp_api_key(key):
    try:
        from mp_api.client import MPRester
        with MPRester(key, mute_progress_bars=True) as mpr:
            _ = mpr.materials.search(
                formula='Si',
                fields=['material_id']
            )
        # color_print('[Info] Materials Project API key validated successfully.\n', 'green')
    except Exception as e:
        color_print('[Error] Invalid Materials Project API key. Exiting...\n', 'green')
        sys.exit(1)
    
def ask_for_mp_api_key():
    key = color_input('Enter your Materials Project API key: ', 'yellow').strip()
    if not key:
        color_print('[Error] Materials Project API key cannot be empty. Exiting...\n', 'green')
        sys.exit(1)

    validate_mp_api_key(key)

    os.environ['MP_API_KEY'] = key

    save = color_input('Save this key to .env file for future? (y/n): ', 'yellow').strip().lower()
    base_dir = os.getcwd()
    env_path = os.path.join(base_dir, '.env')
    if save == 'y':
        with open(env_path, 'a') as f:
            f.write(f'MP_API_KEY={key}\n')
        color_print(f'[Info] Materials Project API key saved to {env_path} file.\n', 'green')

def print_banner():
    try:
        pkg_version = version('masgent')
    except PackageNotFoundError:
        pkg_version = 'dev'
    
    ascii_banner = rf'''
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
║  Version:         {pkg_version:<52}  ║
║  Licensed:        MIT License                                           ║
║  Repository:      https://github.com/aguang5241/masgent                 ║
║  Citation:        Liu, G. et al. (2025), DOI:XX.XXXX/XXXXX              ║
║  Contact:         gliu4@wpi.edu                                         ║
║                                                                         ║
╚═════════════════════════════════════════════════════════════════════════╝
    '''
    color_print(ascii_banner, 'yellow')

def clear_and_print_entry_message():
    os.system('cls' if os.name == 'nt' else 'clear')
    msg = f'''
Welcome to Masgent AI — Your Materials Simulations Agent.
---------------------------------------------------------
Current Session Runs Directory: {os.environ["MASGENT_SESSION_RUNS_DIR"]}

Please select from the following options:
'''
    color_print(msg, 'white')

def clear_and_print_banner_and_entry_message():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    msg = f'''
Welcome to Masgent — Your Materials Simulation Agent.
---------------------------------------------------------
Current Session Runs Directory: {os.environ["MASGENT_SESSION_RUNS_DIR"]}

Please select from the following options:
'''
    color_print(msg, 'white')

def print_help():
    os.system('cls' if os.name == 'nt' else 'clear')

    content = '''
Masgent - Available Commands and Functions: 
-------------------------------------------
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
'''
    color_print(content, "green")

    try:
        while True:
            input = color_input('Type "back" to return: ', 'yellow').strip().lower()
            if input == 'back':
                return
    except KeyboardInterrupt:
        return

