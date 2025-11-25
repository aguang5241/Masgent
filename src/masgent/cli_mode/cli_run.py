#!/usr/bin/env python3

import sys, os
from bullet import Bullet, YesNo, colors

from masgent import tools, schemas
from masgent.ai_mode import ai_backend
from masgent.utils import (
    color_print, 
    color_input, 
    print_help, 
    global_commands, 
    start_new_session
    )

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
    while True:
        runs_dir = os.environ.get('MASGENT_SESSION_RUNS_DIR')

        if os.path.exists(os.path.join(runs_dir, 'POSCAR')):
            use_default = True
        else:
            use_default = False

        if use_default:
            runs_dir_name = os.path.basename(runs_dir)
            choices = [
                'Yes  ->  Use POSCAR file in current runs directory',
                'No   ->  Provide a different POSCAR file path',
            ] + global_commands()

            prompt = f'\nUse POSCAR file in current runs directory: {runs_dir_name}/POSCAR ?\n'
            cli = Bullet(prompt=prompt, choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                ai_backend.main()
            elif user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Back'):
                return
            elif user_input.startswith('Main'):
                run_command('0')
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('Yes'):
                poscar_path = os.path.join(runs_dir, 'POSCAR')
            elif user_input.startswith('No'):
                poscar_path = color_input('\nEnter path to POSCAR file: ', 'yellow').strip()
            else:
                continue
        else:
            poscar_path = color_input('\nEnter path to POSCAR file: ', 'yellow').strip()
        
        if not poscar_path:
            continue
        
        try:
            schemas.CheckPoscar(poscar_path=poscar_path)
            return poscar_path
        except Exception:
            color_print(f'[Error] Invalid POSCAR: {poscar_path}, please double check and try again.\n', 'red')

#############################################
#                                           #
# Below are implementations of sub-commands #
#                                           #
#############################################

@register('1.1.1', 'Generate POSCAR from chemical formula.')
def command_1_1_1():
    try: 
        while True:
            formula = color_input('\nEnter chemical formula (e.g., NaCl): ', 'yellow').strip()

            if not formula:
                continue

            try:
                schemas.GenerateVaspPoscarSchema(formula_list=[formula])
                break
            except Exception:
                color_print(f'[Error] Invalid formula: {formula}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.GenerateVaspPoscarSchema(formula_list=[formula])
    result = tools.generate_vasp_poscar(input=input)
    color_print(result['message'], 'green')

@register('1.1.2', 'Convert POSCAR coordinates (Direct <-> Cartesian).')
def command_1_1_2():
    try:
        while True:
            choices = [
                'Direct coordinates     —>  Cartesian coordinates',
                'Cartesian coordinates  —>  Direct coordinates',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                ai_backend.main()
            elif user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Back'):
                return
            elif user_input.startswith('Main'):
                run_command('0')
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('Direct coordinates'):
                to_cartesian = True
                break
            elif user_input.startswith('Cartesian coordinates'):
                to_cartesian = False
                break
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.ConvertPoscarCoordinatesSchema(poscar_path=poscar_path, to_cartesian=to_cartesian)
    result = tools.convert_poscar_coordinates(input=input)
    color_print(result['message'], 'green')

@register('1.1.3', 'Convert structure file formats (CIF, POSCAR, XYZ).')
def command_1_1_3():
    try:
        while True:
            choices = [
                'POSCAR  ->  CIF',
                'POSCAR  ->  XYZ',
                'CIF     ->  POSCAR',
                'CIF     ->  XYZ',
                'XYZ     ->  POSCAR',
                'XYZ     ->  CIF',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                ai_backend.main()
            elif user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Back'):
                return
            elif user_input.startswith('Main'):
                run_command('0')
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('POSCAR') and user_input.endswith('CIF'):
                input_format, output_format = 'POSCAR', 'CIF'
                break
            elif user_input.startswith('POSCAR') and user_input.endswith('XYZ'):
                input_format, output_format = 'POSCAR', 'XYZ'
                break
            elif user_input.startswith('CIF') and user_input.endswith('POSCAR'):
                input_format, output_format = 'CIF', 'POSCAR'
                break
            elif user_input.startswith('CIF') and user_input.endswith('XYZ'):
                input_format, output_format = 'CIF', 'XYZ'
                break
            elif user_input.startswith('XYZ') and user_input.endswith('POSCAR'):
                input_format, output_format = 'XYZ', 'POSCAR'
                break
            elif user_input.startswith('XYZ') and user_input.endswith('CIF'):
                input_format, output_format = 'XYZ', 'CIF'
                break
            else:
                continue
    
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
    color_print(result['message'], 'green')

@register('1.1.4', 'Generate structure with defects (Vacancy, Interstitial, Substitution).')
def command_1_1_4():
    try:
        while True:
            choices = [
                'Vacancy                 ->  Randomly remove atoms of a selected element',
                'Substitution            ->  Randomly substitute atoms of a selected element with defect element',
                'Interstitial (Voronoi)  ->  Add atom at interstitial sites using Voronoi method',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                ai_backend.main()
            elif user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Back'):
                return
            elif user_input.startswith('Main'):
                run_command('0')
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('Vacancy'):
                run_command('vacancy')
                break
            elif user_input.startswith('Interstitial (Voronoi)'):
                run_command('interstitial')
                break
            elif user_input.startswith('Substitution'):
                run_command('substitution')
                break
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('vacancy', 'Generate structure with vacancy defects.')
def command_vacancy():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    try:
        while True:
            original_element = color_input('\nEnter the element to remove (e.g., Na): ', 'yellow').strip()
            if not original_element:
                continue
            
            try:
                schemas.CheckElement(element_symbol=original_element)
                schemas.CheckElementExistence(poscar_path=poscar_path, element_symbol=original_element)
                break
            except Exception:
                color_print(f'[Error] Invalid element {original_element}, please double check and try again.\n', 'red')
                continue

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
                
                schemas.GenerateVaspPoscarWithVacancyDefects(poscar_path=poscar_path, original_element=original_element, defect_amount=defect_amount)
                break

            except Exception:
                color_print(f'[Error] Invalid defect amount: {defect_amount_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.GenerateVaspPoscarWithVacancyDefects(poscar_path=poscar_path, original_element=original_element, defect_amount=defect_amount)
    result = tools.generate_vasp_poscar_with_vacancy_defects(input=input)
    color_print(result['message'], 'green')

@register('substitution', 'Generate structure with substitution defects.')
def command_substitution():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return
    
    try:
        while True:
            original_element = color_input('\nEnter the target element to be substituted (e.g., Na): ', 'yellow').strip()
            if not original_element:
                continue
            
            try:
                schemas.CheckElement(element_symbol=original_element)
                schemas.CheckElementExistence(poscar_path=poscar_path, element_symbol=original_element)
                break
            
            except Exception:
                color_print(f'[Error] Invalid element {original_element}, please double check and try again.\n', 'red')
                
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return
    
    try:
        while True:
            defect_element = color_input('\nEnter the defect element to substitute in (e.g., K): ', 'yellow').strip()
            if not defect_element:
                continue

            try:
                schemas.CheckElement(element_symbol=defect_element)
                break
            except Exception:
                color_print(f'[Error] Invalid element {defect_element}, please double check and try again.\n', 'red')

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
                schemas.GenerateVaspPoscarWithSubstitutionDefects(poscar_path=poscar_path, original_element=original_element, defect_element=defect_element, defect_amount=defect_amount)
                break

            except Exception:
                color_print(f'[Error] Invalid defect amount: {defect_amount_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.GenerateVaspPoscarWithSubstitutionDefects(poscar_path=poscar_path, original_element=original_element, defect_element=defect_element, defect_amount=defect_amount)
    result = tools.generate_vasp_poscar_with_substitution_defects(input=input)
    color_print(result['message'], 'green')

@register('interstitial', 'Generate structure with interstitial (Voronoi) defects.')
def command_interstitial():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return
    
    try:
        while True:
            defect_element = color_input('\nEnter the defect element to add (e.g., Na): ', 'yellow').strip()
            if not defect_element:
                continue

            try:
                schemas.GenerateVaspPoscarWithInterstitialDefects(poscar_path=poscar_path, defect_element=defect_element)
                break
            except Exception:
                color_print(f'[Error] Invalid element {defect_element}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.GenerateVaspPoscarWithInterstitialDefects(poscar_path=poscar_path, defect_element=defect_element)
    result = tools.generate_vasp_poscar_with_interstitial_defects(input=input)
    color_print(result['message'], 'green')

@register('1.1.5', 'Generate supercell from POSCAR with specified scaling matrix.')
def command_1_1_5():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return
    
    try:
        while True:
            sm = color_input('\nEnter the scaling matrix (e.g., "2 0 0; 0 2 0; 0 0 2" for 2x2x2 supercell): ', 'yellow').strip()

            if not sm:
                continue
            
            try:
                schemas.GenerateSupercellFromPoscar(poscar_path=poscar_path, scaling_matrix=sm)
                break

            except Exception:
                color_print(f'[Error] Invalid scaling matrix: {sm}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return
    
    input = schemas.GenerateSupercellFromPoscar(poscar_path=poscar_path, scaling_matrix=sm)
    result = tools.generate_supercell_from_poscar(input=input)
    color_print(result['message'], 'green')

@register('1.2.1', 'Prepare full VASP input files (INCAR, KPOINTS, POTCAR, POSCAR).')
def command_1_2_1():
    try:
        while True:
            choices = [
                'MPRelaxSet       ->   suggested for structure relaxation',
                'MPStaticSet      ->   suggested for static calculations',
                'MPNonSCFSet      ->   suggested for non-self-consistent field calculations',
                'MPScanRelaxSet   ->   suggested for structure relaxation with r2SCAN functional',
                'MPScanStaticSet  ->   suggested for static calculations with r2SCAN functional',
                'MPMDSet          ->   suggested for molecular dynamics simulations',
                'NEBSet           ->   suggested for nudged elastic band calculations',
                'MVLElasticSet    ->   suggested for elastic constant calculations',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                ai_backend.main()
            elif user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Back'):
                return
            elif user_input.startswith('Main'):
                run_command('0')
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
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
            elif user_input.startswith('NEBSet'):
                vasp_input_sets = 'NEBSet'
                break
            elif user_input.startswith('MVLElasticSet'):
                vasp_input_sets = 'MVLElasticSet'
                break
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)
    
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.GenerateVaspInputsFromPoscar(poscar_path=poscar_path, vasp_input_sets=vasp_input_sets, only_incar=False)
    result = tools.generate_vasp_inputs_from_poscar(input=input)
    color_print(result['message'], 'green')

@register('1.2.2', 'Generate INCAR templates (relaxation, static, MD, etc.).')
def command_1_2_2():
    try:
        while True:
            choices = [
                'MPRelaxSet       ->   suggested for structure relaxation',
                'MPStaticSet      ->   suggested for static calculations',
                'MPNonSCFSet      ->   suggested for non-self-consistent field calculations',
                'MPScanRelaxSet   ->   suggested for structure relaxation with r2SCAN functional',
                'MPScanStaticSet  ->   suggested for static calculations with r2SCAN functional',
                'MPMDSet          ->   suggested for molecular dynamics simulations',
                'NEBSet           ->   suggested for nudged elastic band calculations',
                'MVLElasticSet    ->   suggested for elastic constant calculations',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                ai_backend.main()
            elif user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Back'):
                return
            elif user_input.startswith('Main'):
                run_command('0')
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
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
            elif user_input.startswith('NEBSet'):
                vasp_input_sets = 'NEBSet'
                break
            elif user_input.startswith('MVLElasticSet'):
                vasp_input_sets = 'MVLElasticSet'
                break
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)
    
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.GenerateVaspInputsFromPoscar(poscar_path=poscar_path, vasp_input_sets=vasp_input_sets, only_incar=True)
    result = tools.generate_vasp_inputs_from_poscar(input=input)
    color_print(result['message'], 'green')

@register('1.2.3', 'Generate KPOINTS with specified accuracy.')
def command_1_2_3():
    try:
        while True:
            choices = [
                'Low     ->  Suitable for preliminary calculations, grid density = 1000 / number of atoms',
                'Medium  ->  Balanced accuracy and computational cost, grid density = 3000 / number of atoms',
                'High    ->  High accuracy for production runs, grid density = 5000 / number of atoms',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                ai_backend.main()
            elif user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Back'):
                return
            elif user_input.startswith('Main'):
                run_command('0')
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
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
                continue
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        return

    input = schemas.CustomizeVaspKpointsWithAccuracy(poscar_path=poscar_path, accuracy_level=accuracy_level)
    result = tools.customize_vasp_kpoints_with_accuracy(input=input)
    color_print(result['message'], 'green')