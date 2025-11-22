# !/usr/bin/env python3
import sys
from bullet import Bullet, Input, colors

from masgent import tools, schemas
from masgent.ai_mode import ai_backend
from masgent.utils import color_print, color_input, print_banner, print_help

COMMANDS = {}

def register(code, func):
    def decorator(func):
        COMMANDS[code] = {
            'function': func,
            'description': func.__doc__ or ''
        }
        return func
    return decorator

def run_command(code):
    cmd = COMMANDS.get(code)
    if cmd:
        cmd['function']()
    else:
        color_print(f'[Error] Invalid command code: {code}\n', 'red')

def check_poscar():
    try:
        while True:
            poscar_path = color_input('\nEnter path to input structure file: ', 'yellow').strip()

            if not poscar_path:
                continue
            
            try:
                schemas.CheckPoscar(poscar_path=poscar_path)
                return poscar_path
            except Exception:
                color_print(f'[Error] Invalid POSCAR: {poscar_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

@register('0', 'Entry point for Masgent CLI.')
def command_0():
    print_banner()
    
    try:
        while True:
            prompt = '''
Welcome to Masgent — Your Materials Simulation Agent.
-----------------------------------------------------
Please select from the following options:
'''
            choices = [
                '1. Density Functional Theory (DFT) Simulations',
                '2. Machine Learning Potentials (MLP)',
                '3. Machine Learning Model Training & Evaluation',
                '',
                '--- Global Commands ---',
                'AI',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt=prompt, choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue
            
            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input == '1. Density Functional Theory (DFT) Simulations':
                run_command('1')
            elif user_input == '2. Machine Learning Potentials (MLP)':
                run_command('2')
            elif user_input == '3. Machine Learning Model Training & Evaluation':
                run_command('3')
            else:
                pass
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1', 'Entry point for Density Functional Theory (DFT) Simulations.')
def command_1():
    try:
        while True:
            choices = [
                '1.1 Prepare VASP input files',
                '1.2 Analyze VASP output files',
                '',
                '--- Global Commands ---',
                'AI',
                'Back',
                'Main',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue

            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Back':
                return
            elif user_input == 'Main':
                run_command('0')
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input == '1.1 Prepare VASP input files':
                run_command('1.1')
            elif user_input == '1.2 Analyze VASP output files':
                run_command('1.2')
            else:
                pass

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)


@register('1.1', 'Prepare VASP input files')
def command_1_1():
    try:
        while True:
            choices = [
                '1.1.1 Generate VASP POSCAR file from chemical formula',
                '1.1.2 Generate VASP KPOINTS with specified accuracy',
                '1.1.3 Prepare VASP input files (INCAR, KPOINTS, POTCAR)',
                '1.1.4 Convert POSCAR coordinates (Direct <-> Cartesian)',
                '1.1.5 Convert structure file formats (CIF, POSCAR, XYZ)',
                '1.1.6 Generate VASP POSCAR with defects (Vacancies, Interstitials, Substitutions)',
                '',
                '--- Global Commands ---',
                'AI',
                'Back',
                'Main',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue

            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Back':
                return
            elif user_input == 'Main':
                run_command('0')
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input == '1.1.1 Generate VASP POSCAR file from chemical formula':
                run_command('1.1.1')
            elif user_input == '1.1.2 Generate VASP KPOINTS with specified accuracy':
                run_command('1.1.2')
            elif user_input == '1.1.3 Prepare VASP input files (INCAR, KPOINTS, POTCAR)':
                run_command('1.1.3')
            elif user_input == '1.1.4 Convert POSCAR coordinates (Direct <-> Cartesian)':
                run_command('1.1.4')
            elif user_input == '1.1.5 Convert structure file formats (CIF, POSCAR, XYZ)':
                run_command('1.1.5')
            elif user_input == '1.1.6 Generate VASP POSCAR with defects (Vacancies, Interstitials, Substitutions)':
                run_command('1.1.6')
            else:
                pass

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1.2', 'Analyze VASP output files')
def command_1_2():
    try:
        while True:
            choices = [
                '(To be implemented)',
                '',
                '--- Global Commands ---',
                'AI',
                'Back',
                'Main',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue

            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Back':
                return
            elif user_input == 'Main':
                run_command('0')
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input == '(To be implemented)':
                print('This feature is under development. Stay tuned!')
            else:
                pass

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1.1.1', 'Generate VASP POSCAR file from user inputs or from Materials Project database.')
def command_1_1_1():
    try: 
        while True:
            formula = color_input('\nEnter chemical formula (e.g., NaCl): ', 'yellow').strip()

            if not formula:
                continue

            try:
                schemas.GenerateVaspPoscarSchema(formula=formula)
                break
            except Exception:
                color_print(f'[Error] Invalid formula: {formula}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.GenerateVaspPoscarSchema(formula=formula)
    result = tools.generate_vasp_poscar(input=input)
    color_print(result, 'green')


@register('1.1.2', 'Generate VASP KPOINTS with specified accuracy.')
def command_001():
    try:
        while True:
            choices = [
                'Low     ->  Suitable for preliminary calculations, grid density = 1000 / number of atoms',
                'Medium  ->  Balanced accuracy and computational cost, grid density = 3000 / number of atoms',
                'High    ->  High accuracy for production runs, grid density = 5000 / number of atoms',
                '',
                '--- Global Commands ---',
                'AI',
                'Back',
                'Main',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue

            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Back':
                return
            elif user_input == 'Main':
                run_command('0')
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('Low'):
                accuracy_level = 'Low'
                break
            elif user_input.startswith('Medium'):
                accuracy_level = 'Medium'
                break
            elif user_input.startswith('High'):
                accuracy_level = 'High'
                break
            else:
                pass
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

    poscar_path = check_poscar()

    input = schemas.CustomizeVaspKpointsWithAccuracy(poscar_path=poscar_path, accuracy_level=accuracy_level)
    result = tools.customize_vasp_kpoints_with_accuracy(input=input)
    color_print(result, 'green')

@register('1.1.3', 'Generate VASP input files (INCAR, KPOINTS, POTCAR) using pymatgen input sets.')
def command_1_1_3():
    try:
        while True:
            choices = [
                'MPRelaxSet       ->   suggested for structure relaxation',
                'MPStaticSet      ->   suggested for static calculations',
                'MPNonSCFSet      ->   suggested for non-self-consistent field calculations',
                'MPScanRelaxSet   ->   suggested for structure relaxation with r2SCAN functional',
                'MPScanStaticSet  ->   suggested for static calculations with r2SCAN functional',
                'MPMDSet          ->   suggested for molecular dynamics simulations',
                '',
                '--- Global Commands ---',
                'AI',
                'Back',
                'Main',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue

            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Back':
                return
            elif user_input == 'Main':
                run_command('0')
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('MPRelaxSet'):
                vasp_input_sets = 'MPRelaxSet'
                break
            elif user_input.startswith('MPStaticSet'):
                vasp_input_sets = 'MPStaticSet'
                break
            elif user_input.startswith('MPNonSCFSet'):
                vasp_input_sets = 'MPNonSCFSet'
                break
            elif user_input.startswith('MPScanRelaxSet'):
                vasp_input_sets = 'MPScanRelaxSet'
                break
            elif user_input.startswith('MPScanStaticSet'):
                vasp_input_sets = 'MPScanStaticSet'
                break
            elif user_input.startswith('MPMDSet'):
                vasp_input_sets = 'MPMDSet'
                break
            else:
                pass
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)
    
    poscar_path = check_poscar()

    input = schemas.GenerateVaspInputsFromPoscar(poscar_path=poscar_path, vasp_input_sets=vasp_input_sets)
    result = tools.generate_vasp_inputs_from_poscar(input=input)
    color_print(result, 'green')

@register('1.1.4', 'Convert POSCAR between direct and cartesian coordinates.')
def command_1_1_4():
    try:
        while True:
            choices = [
                'Direct coordinates     —>  Cartesian coordinates',
                'Cartesian coordinates  —>  Direct coordinates',
                '',
                '--- Global Commands ---',
                'AI',
                'Back',
                'Main',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue

            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Back':
                return
            elif user_input == 'Main':
                run_command('0')
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('Direct coordinates'):
                to_cartesian = True
                break
            elif user_input.startswith('Cartesian coordinates'):
                to_cartesian = False
                break
            else:
                pass
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

    poscar_path = check_poscar()

    input = schemas.ConvertPoscarCoordinatesSchema(poscar_path=poscar_path, to_cartesian=to_cartesian)
    result = tools.convert_poscar_coordinates(input=input)
    color_print(result, 'green')

@register('1.1.5', 'Convert structure file formats (CIF, POSCAR, XYZ).')
def command_1_1_5():
    try:
        while True:
            choices = [
                'POSCAR  ->  CIF',
                'POSCAR  ->  XYZ',
                'CIF     ->  POSCAR',
                'CIF     ->  XYZ',
                'XYZ     ->  POSCAR',
                'XYZ     ->  CIF',
                '',
                '--- Global Commands ---',
                'AI',
                'Back',
                'Main',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue

            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Back':
                return
            elif user_input == 'Main':
                run_command('0')
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('POSCAR') and input_path.endswith('CIF'):
                input_format, output_format = 'POSCAR', 'CIF'
                break
            elif user_input.startswith('POSCAR') and input_path.endswith('XYZ'):
                input_format, output_format = 'POSCAR', 'XYZ'
                break
            elif user_input.startswith('CIF') and input_path.endswith('POSCAR'):
                input_format, output_format = 'CIF', 'POSCAR'
                break
            elif user_input.startswith('CIF') and input_path.endswith('XYZ'):
                input_format, output_format = 'CIF', 'XYZ'
                break
            elif user_input.startswith('XYZ') and input_path.endswith('POSCAR'):
                input_format, output_format = 'XYZ', 'POSCAR'
                break
            elif user_input.startswith('XYZ') and input_path.endswith('CIF'):
                input_format, output_format = 'XYZ', 'CIF'
                break
            else:
                pass
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

    try:
        while True:
            input_path = color_input('\nEnter path to input structure file: ', 'yellow').strip()

            if not input_path:
                continue
            
            try:
                schemas.ConvertStructureFormatSchema(input_path=input_path, input_format=input_format, output_format=output_format)
                break
            except Exception:
                color_print(f'[Error] Invalid input: {input_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.ConvertStructureFormatSchema(input_path=input_path, input_format=input_format, output_format=output_format)
    result = tools.convert_structure_format(input=input)
    color_print(result, 'green')

@register('1.1.6', 'Generate VASP POSCAR with defects (vacancies, interstitials, substitutions).')
def command_1_1_6():
    try:
        while True:
            choices = [
                'Vacancy       ->  Remove atoms of a selected element',
                'Interstitial  ->  Add atoms to interstitial positions',
                'Substitution  ->  Replace atoms with another element',
                '',
                '--- Global Commands ---',
                'AI',
                'Back',
                'Main',
                'Help',
                'Exit',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.strip() == '' or user_input.startswith('---'):
                continue

            if user_input == 'AI':
                ai_backend.main()
            elif user_input == 'Back':
                return
            elif user_input == 'Main':
                run_command('0')
            elif user_input == 'Help':
                print_help()
            elif user_input == 'Exit':
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('Vacancy'):
                defect_type = 'vacancy'
                break
            elif user_input.startswith('Interstitial'):
                defect_type = 'interstitial'
                break
            elif user_input.startswith('Substitution'):
                defect_type = 'substitution'
                break
            else:
                pass
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)
    
    poscar_path = check_poscar()
    
    try:
        while True:
            if defect_type == 'vacancy':
                original_element = color_input('\nEnter the element to remove (e.g., Na): ', 'yellow').strip()
                defect_element = None
                if not original_element:
                    continue
            elif defect_type == 'interstitial':
                original_element = None
                defect_element = color_input('\nEnter the defect element to add (e.g., Na): ', 'yellow').strip()
                if not defect_element:
                    continue
            else:
                original_element = color_input('\nEnter the target element to be substituted (e.g., Na): ', 'yellow').strip()
                if not original_element:
                    continue
                defect_element = color_input('\nEnter the defect element to substitute in (e.g., K): ', 'yellow').strip()
                if not defect_element:
                    continue

            try:
                if original_element:
                    schemas.CheckElement(element_symbol=original_element)
                    schemas.CheckElementExistence(poscar_path=poscar_path, element_symbol=original_element)
                if defect_element:
                    schemas.CheckElement(element_symbol=defect_element)
                break
            except Exception:
                color_print(f'[Error] Invalid element {original_element or defect_element}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    try:
        while True:
            defect_amount_str = color_input('\nEnter the defect amount (fraction between 0 and 1, or atom count >=1): ', 'yellow').strip()

            if not defect_amount_str:
                continue
            
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
                color_print(f'[Error] Invalid defect amount: {defect_amount_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.GenerateVaspPoscarWithDefects(
        poscar_path=poscar_path, 
        defect_type=defect_type, 
        original_element=original_element, 
        defect_amount=defect_amount, 
        defect_element=defect_element
        )
    result = tools.generate_vasp_poscar_with_defects(input=input)
    color_print(result, 'green')