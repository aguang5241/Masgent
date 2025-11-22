# !/usr/bin/env python3

from masgent import tools, schemas
from masgent.utils import color_print, color_input

COMMANDS = {}

def global_commands(user_input):
    if user_input in {'ai'}:
        return 'ai-mode'
    elif user_input in {'back'}:
        return 'cli-mode'
    elif user_input in {'exit'}:
        return 'exit-mode'

def register(code, func):
    def decorator(func):
        COMMANDS[code] = {
            'function': func,
            'description': func.__doc__ or ''
        }
        return func
    return decorator

@register('0', 'Entry point for Density Functional Theory (DFT) Simulations.')
def command_0():
    msg = '''
Density Functional Theory (DFT) Simulations.
--------------------------------------------
Please select a mode code to proceed:
  00  —>  Prepare VASP input files
  01  —>  Analyze VASP output files

Global commands:
  ai    —>  Chat with the AI assistant
  back  —>  Switch back to main menu
  help  —>  List all available functions
  exit  —>  Quit the program
    '''
    color_print(msg, 'green')

@register('00', 'Prepare VASP input files')
def command_00():
    msg = '''
Prepare VASP Input Files.
-------------------------
Please select a function code to proceed:
  000  —>  Generate VASP POSCAR file from chemical formula
  001  —>  Generate VASP KPOINTS with specified accuracy
  002  —>  Prepare VASP input files (INCAR, KPOINTS, POTCAR)
  003  —>  Convert POSCAR coordinates (direct <-> cartesian)
  004  —>  Convert structure file formats (CIF, POSCAR, XYZ)
  005  —>  Generate VASP POSCAR with defects (vacancies, interstitials, substitutions)

Global commands:
  ai    —>  Chat with the AI assistant
  back  —>  Switch back to main menu
  help  —>  List all available functions
  exit  —>  Quit the program
    '''
    color_print(msg, 'green')

@register('01', 'Analyze VASP output files')
def command_01():
    msg = '''
Analyze VASP Output Files.
--------------------------
Please select a function code to proceed:
  (To be implemented)
    '''
    color_print(msg, 'green')

@register('000', 'Generate VASP POSCAR file from user inputs or from Materials Project database.')
def command_000():
    while True:
        formula = color_input('\nEnter chemical formula (e.g., NaCl): ', 'yellow').strip()

        if not formula:
            continue

        if formula.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return

        try:
            schemas.GenerateVaspPoscarSchema(formula=formula)
            break
        except Exception:
            color_print(f'[Error] Invalid input formula: {formula}, please try again.\n', 'green')

    input = schemas.GenerateVaspPoscarSchema(formula=formula)
    result = tools.generate_vasp_poscar(input=input)
    color_print(result, 'green')

@register('001', 'Generate VASP KPOINTS with specified accuracy.')
def command_001():
    while True:
        msg = '''
Available accuracy levels for KPOINTS generation:
-------------------------------------------------
  0. Low     —>  Suitable for preliminary calculations, grid density = 1000 / number of atoms
  1. Medium  —>  Balanced accuracy and computational cost, grid density = 3000 / number of atoms
  2. High    —>  High accuracy for production runs, grid density = 5000 / number of atoms
    '''
        color_print(msg, 'green')
        
        code = color_input('\nEnter the code for accuracy level (0/1/2): ', 'yellow').strip()
        
        if not code:
            continue

        if code.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return
        
        if code not in {'0', '1', '2'}:
            color_print(f'[Error] Invalid accuracy level code: {code}, please try again.\n', 'green')
            continue

        accuracy_level = {'0': 'Low', '1': 'Medium', '2': 'High'}[code]
        break

    while True:
        poscar_path = color_input('\nEnter path to POSCAR file: ', 'yellow').strip()

        if not poscar_path:
            continue

        if poscar_path.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return
        
        try:
            schemas.CustomizeVaspKpointsWithAccuracy(poscar_path=poscar_path, accuracy_level=accuracy_level)
            break
        except Exception:
            color_print(f'[Error] Invalid POSCAR path: {poscar_path}, please try again.\n', 'green')

    input = schemas.CustomizeVaspKpointsWithAccuracy(poscar_path=poscar_path, accuracy_level=accuracy_level)
    result = tools.customize_vasp_kpoints_with_accuracy(input=input)
    color_print(result, 'green')

@register('002', 'Generate VASP input files (INCAR, KPOINTS, POTCAR) using pymatgen input sets.')
def command_002():
    while True:
        sets_map = {
            '0': 'MPRelaxSet',
            '1': 'MPStaticSet',
            '2': 'MPNonSCFSet',
            '3': 'MPScanRelaxSet',
            '4': 'MPScanStaticSet',
            '5': 'MPMDSet'
        }
        descriptions_map = {
            '0': 'MPRelaxSet: suggested for structure relaxation',
            '1': 'MPStaticSet: suggested for static calculations',
            '2': 'MPNonSCFSet: suggested for non-self-consistent field calculations',
            '3': 'MPScanRelaxSet: suggested for structure relaxation with r2SCAN functional',
            '4': 'MPScanStaticSet: suggested for static calculations with r2SCAN functional',
            '5': 'MPMDSet: suggested for molecular dynamics simulations'
        }

        msg = '''
Available VASP input set types:
-------------------------------
'''
        for key, val in descriptions_map.items():
            msg += f'  {key}. {val}\n'
        color_print(msg, 'green')
        
        code = color_input('\nEnter the code for VASP input set type: ', 'yellow').strip()

        if not code:
            continue

        if code.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return

        if code not in sets_map:
            color_print(f'[Error] Invalid VASP input set code: {code}, please try again.\n', 'green')
            continue

        vasp_input_sets = sets_map[code]
        break

    while True:
        poscar_path = color_input('\nEnter path to POSCAR file: ', 'yellow').strip()

        if not poscar_path:
            continue

        if poscar_path.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return

        try:
            schemas.GenerateVaspInputsFromPoscar(poscar_path=poscar_path, vasp_input_sets=vasp_input_sets)
            break
        except Exception:
            color_print(f'[Error] Invalid POSCAR path: {poscar_path}, please try again.\n', 'green')

    input = schemas.GenerateVaspInputsFromPoscar(poscar_path=poscar_path, vasp_input_sets=vasp_input_sets)
    result = tools.generate_vasp_inputs_from_poscar(input=input)
    color_print(result, 'green')

@register('003', 'Convert POSCAR between direct and cartesian coordinates.')
def command_003():
    while True:
        msg = '''
Conversion options:
-------------------
  0  —>  Convert to Cartesian coordinates
  1  —>  Convert to Direct coordinates
    '''
        color_print(msg, 'green')

        code = color_input('\nEnter the code for conversion option (0/1): ', 'yellow').strip()

        if not code:
            continue

        if code.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return
        
        if code not in {'0', '1'}:
            color_print(f'[Error] Invalid conversion option code: {code}, please try again.\n', 'green')
            continue

        to_cartesian = True if code == '0' else False
        break

    while True:
        poscar_path = color_input('\nEnter path to POSCAR file: ', 'yellow').strip()

        if not poscar_path:
            continue

        if poscar_path.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return

        try:
            schemas.ConvertPoscarCoordinatesSchema(poscar_path=poscar_path, to_cartesian=to_cartesian)
            break
        except Exception:
            color_print(f'[Error] Invalid POSCAR path: {poscar_path}, please try again.\n', 'green')

    input = schemas.ConvertPoscarCoordinatesSchema(poscar_path=poscar_path, to_cartesian=to_cartesian)
    result = tools.convert_poscar_coordinates(input=input)
    color_print(result, 'green')

@register('004', 'Convert structure file formats (CIF, POSCAR, XYZ).')
def command_004():
    while True:
        msg = '''
Available format conversions:
-----------------------------
  0. POSCAR  ->  CIF
  1. POSCAR  ->  XYZ
  2. CIF     ->  POSCAR
  3. CIF     ->  XYZ
  4. XYZ     ->  POSCAR
  5. XYZ     ->  CIF
    '''
        color_print(msg, 'green')

        code = color_input('\nEnter the code for structure conversion: ', 'yellow').strip()

        if not code:
            continue

        if code.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return
        
        conversions_map = {
            '0': ('POSCAR', 'CIF'),
            '1': ('POSCAR', 'XYZ'),
            '2': ('CIF', 'POSCAR'),
            '3': ('CIF', 'XYZ'),
            '4': ('XYZ', 'POSCAR'),
            '5': ('XYZ', 'CIF')
        }

        if code not in conversions_map:
            color_print(f'[Error] Invalid structure conversion code: {code}, please try again.\n', 'green')
            continue

        input_format, output_format = conversions_map[code]
        break

    while True:
        input_path = color_input('\nEnter path to input structure file: ', 'yellow').strip()

        if not input_path:
            continue

        if input_path.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return

        try:
            schemas.ConvertStructureFormatSchema(input_path=input_path, input_format=input_format, output_format=output_format)
            break
        except Exception:
            color_print(f'[Error] Invalid input structure file path or formats, please try again.\n', 'green')

    input = schemas.ConvertStructureFormatSchema(input_path=input_path, input_format=input_format, output_format=output_format)
    result = tools.convert_structure_format(input=input)
    color_print(result, 'green')

@register('005', 'Generate VASP POSCAR with defects (vacancies, interstitials, substitutions).')
def command_005():
    while True:
        msg = '''
Available defect types:
-----------------------
  0. vacancy       —>  Remove atoms of a specified element
  1. interstitial  —>  Add atoms of a specified element
  2. substitution  —>  Replace atoms of one element with another element
    '''
        color_print(msg, 'green')

        code = color_input('\nEnter the code for defect type (0/1/2): ', 'yellow').strip()

        if not code:
            continue

        if code.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return
        
        defect_types_map = {
            '0': 'vacancy',
            '1': 'interstitial',
            '2': 'substitution'
        }

        if code not in defect_types_map:
            color_print(f'[Error] Invalid defect type code: {code}, please try again.\n', 'green')
            continue

        defect_type = defect_types_map[code]
        break
    
    while True:
        poscar_path = color_input('\nEnter path to POSCAR file: ', 'yellow').strip()

        if not poscar_path:
            continue

        if poscar_path.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return
        break
    
    while True:
        if defect_type == 'vacancy':
            original_element = color_input('\nEnter the element to remove (e.g., Na): ', 'yellow').strip()
            defect_element = None

            if not original_element:
                continue

            if original_element.lower() in {'ai', 'back', 'help','exit'}:
                color_print('[Info] Input cancelled...\n', 'green')
                return
            
        elif defect_type == 'interstitial':
            original_element = None
            defect_element = color_input('\nEnter the defect element to add (e.g., Na): ', 'yellow').strip()

            if not defect_element:
                continue

            if defect_element.lower() in {'ai', 'back', 'help','exit'}:
                color_print('[Info] Input cancelled...\n', 'green')
                return
        else:
            original_element = color_input('\nEnter the target element to be substituted (e.g., Na): ', 'yellow').strip()

            if not original_element:
                continue

            if original_element.lower() in {'ai', 'back', 'help','exit'}:
                color_print('[Info] Input cancelled...\n', 'green')
                return
            
            defect_element = color_input('\nEnter the defect element to substitute in (e.g., K): ', 'yellow').strip()

            if not defect_element:
                continue

            if defect_element.lower() in {'ai', 'back', 'help','exit'}:
                color_print('[Info] Input cancelled...\n', 'green')
                return
        try:
            schemas.GenerateVaspPoscarWithDefects(
                poscar_path=poscar_path,
                defect_type=defect_type,
                original_element=original_element,
                defect_amount=1,
                defect_element=defect_element,
            )
            break
        
        except Exception:
            color_print(f'[Error] Invalid element(s), please try again.\n', 'green')

    while True:
        defect_amount_str = color_input('\nEnter the defect amount (fraction between 0 and 1, or atom count >=1): ', 'yellow').strip()

        if not defect_amount_str:
            continue

        if defect_amount_str.lower() in {'ai', 'back', 'help','exit'}:
            color_print('[Info] Input cancelled...\n', 'green')
            return
        
        try:
            if '.' in defect_amount_str:
                defect_amount = float(defect_amount_str)
            else:
                defect_amount = int(defect_amount_str)
            
            schemas.GenerateVaspPoscarWithDefects(
                poscar_path=poscar_path,
                defect_type=defect_type,
                original_element=original_element,
                defect_amount=defect_amount,
                defect_element=defect_element,
            )
            break

        except Exception:
            color_print(f'[Error] Invalid defect amount: {defect_amount_str}, please try again.\n', 'green')

    input = schemas.GenerateVaspPoscarWithDefects(
        poscar_path=poscar_path, 
        defect_type=defect_type, 
        original_element=original_element, 
        defect_amount=defect_amount, 
        defect_element=defect_element
        )
    result = tools.generate_vasp_poscar_with_defects(input=input)
    color_print(result, 'green')