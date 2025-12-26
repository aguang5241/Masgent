#!/usr/bin/env python3

import os, time
from bullet import Bullet, colors
from yaspin import yaspin
from yaspin.spinners import Spinners

from masgent.utils import tools, schemas
from masgent.utils.utils import (
    color_print, 
    color_input, 
    print_help, 
    global_commands, 
    start_new_session,
    clear_and_print_entry_message,
    exit_and_cleanup,
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
            clear_and_print_entry_message()
            choices = [
                'Yes  ->  Use POSCAR file in current runs directory',
                'No   ->  Provide a different POSCAR file path',
            ] + global_commands()

            prompt = f'\nUse POSCAR file in current runs directory: {runs_dir_name}/POSCAR ?\n'
            cli = Bullet(prompt=prompt, choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
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
                schemas.GenerateVaspPoscarSchema(formula=formula)
                break
            except Exception:
                color_print(f'[Error] Invalid formula: {formula}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    result = tools.generate_vasp_poscar(formula=formula)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.1.2', 'Convert POSCAR coordinates (Direct <-> Cartesian).')
def command_1_1_2():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                'Direct coordinates     —>  Cartesian coordinates',
                'Cartesian coordinates  —>  Direct coordinates',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
            elif user_input.startswith('Direct coordinates'):
                to_cartesian = True
                break
            elif user_input.startswith('Cartesian coordinates'):
                to_cartesian = False
                break
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    result = tools.convert_poscar_coordinates(poscar_path=poscar_path, to_cartesian=to_cartesian)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.1.3', 'Convert structure file formats (CIF, POSCAR, XYZ).')
def command_1_1_3():
    try:
        while True:
            clear_and_print_entry_message()
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
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
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
        exit_and_cleanup()

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
        time.sleep(1)
        return

    result = tools.convert_structure_format(input_path=input_path, input_format=input_format, output_format=output_format)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.1.4', 'Generate structure with defects (Vacancy, Interstitial, Substitution).')
def command_1_1_4():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                'Vacancy                 ->  Randomly remove atoms of a selected element',
                'Substitution            ->  Randomly substitute atoms of a selected element with defect element',
                'Interstitial (Voronoi)  ->  Add atom at interstitial sites using Voronoi method',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
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
        exit_and_cleanup()

@register('vacancy', 'Generate structure with vacancy defects.')
def command_vacancy():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
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
        time.sleep(1)
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
        time.sleep(1)
        return

    result = tools.generate_vasp_poscar_with_vacancy_defects(poscar_path=poscar_path, original_element=original_element, defect_amount=defect_amount)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('substitution', 'Generate structure with substitution defects.')
def command_substitution():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
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
        time.sleep(1)
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
        time.sleep(1)
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
        time.sleep(1)
        return

    result = tools.generate_vasp_poscar_with_substitution_defects(poscar_path=poscar_path, original_element=original_element, defect_element=defect_element, defect_amount=defect_amount)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('interstitial', 'Generate structure with interstitial (Voronoi) defects.')
def command_interstitial():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
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
        time.sleep(1)
        return

    print('')
    with yaspin(Spinners.dots, text='Generating interstitial defects... See details in the log file.', color='cyan') as sp:
        result = tools.generate_vasp_poscar_with_interstitial_defects(poscar_path=poscar_path, defect_element=defect_element)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.1.5', 'Generate supercell from POSCAR with specified scaling matrix.')
def command_1_1_5():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            scaling_matrix = color_input('\nEnter the scaling matrix for 2x2x2 supercell (e.g., 2 0 0; 0 2 0; 0 0 2): ', 'yellow').strip()

            if not scaling_matrix:
                continue
            
            try:
                schemas.GenerateSupercellFromPoscar(poscar_path=poscar_path, scaling_matrix=scaling_matrix)
                break

            except Exception:
                color_print(f'[Error] Invalid scaling matrix: {scaling_matrix}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    result = tools.generate_supercell_from_poscar(poscar_path=poscar_path, scaling_matrix=scaling_matrix)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.1.6', 'Generate special quasi-random structure (SQS) from POSCAR.')
def command_1_1_6():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            target_configurations_str = color_input('\nEnter target configurations (e.g., La: La=0.5,Y=0.5; Co: Al=0.75,Co=0.25): ', 'yellow').strip()
            
            if not target_configurations_str:
                continue

            try:
                # parse target configurations to {'La': {'La': 0.5, 'Y': 0.5}, 'Co': {'Al': 0.75, 'Co': 0.25}}
                target_configurations = {}
                for sublattice_str in target_configurations_str.split(';'):
                    sublattice_str = sublattice_str.strip()
                    if not sublattice_str:
                        continue
                    element, conc_str = sublattice_str.split(':')
                    element = element.strip()
                    conc_pairs = conc_str.split(',')
                    conc_dict = {}
                    for pair in conc_pairs:
                        species, conc = pair.split('=')
                        conc_dict[species.strip()] = float(conc.strip())
                    target_configurations[element] = conc_dict
                schemas.GenerateSqsFromPoscar(poscar_path=poscar_path, target_configurations=target_configurations)
                break
            except Exception as e:
                print(e)
                color_print(f'[Error] Invalid target configurations: {target_configurations_str}, please double check and try again.\n', 'red')
    
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            cutoffs_str = color_input('\nEnter cluster cutoffs in Å for pairs, triplets, and quadruplets (e.g., 8.0 4.0 4.0): ', 'yellow').strip()

            if not cutoffs_str:
                continue

            try:
                cutoffs = [float(x) for x in cutoffs_str.split()]
                schemas.GenerateSqsFromPoscar(poscar_path=poscar_path, target_configurations=target_configurations, cutoffs=cutoffs)
                break
            except Exception:
                color_print(f'[Error] Invalid cutoffs: {cutoffs_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            max_supercell_size_str = color_input('\nEnter maximum supercell size (e.g., 8): ', 'yellow').strip()

            if not max_supercell_size_str:
                continue

            try:
                max_supercell_size = int(max_supercell_size_str)
                schemas.GenerateSqsFromPoscar(poscar_path=poscar_path, target_configurations=target_configurations, cutoffs=cutoffs, max_supercell_size=max_supercell_size)
                break
            except Exception:
                color_print(f'[Error] Invalid maximum supercell size: {max_supercell_size_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            mc_steps_str = color_input('\nEnter number of Monte Carlo steps (e.g., >=1000): ', 'yellow').strip()

            if not mc_steps_str:
                continue

            try:
                mc_steps = int(mc_steps_str)
                schemas.GenerateSqsFromPoscar(poscar_path=poscar_path, target_configurations=target_configurations, cutoffs=cutoffs, max_supercell_size=max_supercell_size, mc_steps=mc_steps)
                break
            except Exception:
                color_print(f'[Error] Invalid number of Monte Carlo steps: {mc_steps_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    print('')
    with yaspin(Spinners.dots, text='Generating SQS... See details in the log file.', color='cyan') as sp:
        result = tools.generate_sqs_from_poscar(
            poscar_path=poscar_path, 
            target_configurations=target_configurations, 
            cutoffs=cutoffs, 
            max_supercell_size=max_supercell_size, 
            mc_steps=mc_steps
        )
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.1.7', 'Generate surface slab from POSCAR with specified Miller indices, vacuum thickness, and slab layers.')
def command_1_1_7():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            miller_indices_str = color_input('\nEnter the Miller indices (e.g., 1 1 1): ', 'yellow').strip()
            
            if not miller_indices_str:
                continue

            try:
                miller_indices = [int(x) for x in miller_indices_str.split()]
                schemas.GenerateSurfaceSlabFromPoscar(poscar_path=poscar_path, miller_indices=miller_indices)
                break
            except Exception:
                color_print(f'[Error] Invalid Miller indices: {miller_indices_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            vacuum_thickness_str = color_input('\nEnter the vacuum thickness in Å (e.g., 15.0): ', 'yellow').strip()

            if not vacuum_thickness_str:
                continue

            try:
                vacuum_thickness = float(vacuum_thickness_str)
                schemas.GenerateSurfaceSlabFromPoscar(poscar_path=poscar_path, miller_indices=miller_indices, vacuum_thickness=vacuum_thickness)
                break
            except Exception:
                color_print(f'[Error] Invalid vacuum thickness: {vacuum_thickness_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            slab_layers_str = color_input('\nEnter the number of slab layers (e.g., 4): ', 'yellow').strip()

            if not slab_layers_str:
                continue

            try:
                slab_layers = int(slab_layers_str)
                schemas.GenerateSurfaceSlabFromPoscar(poscar_path=poscar_path, miller_indices=miller_indices, vacuum_thickness=vacuum_thickness, slab_layers=slab_layers)
                break
            except Exception:
                color_print(f'[Error] Invalid slab layers: {slab_layers_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    result = tools.generate_surface_slab_from_poscar(poscar_path=poscar_path, miller_indices=miller_indices, vacuum_thickness=vacuum_thickness, slab_layers=slab_layers)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.1.8', 'Generate interface structure from two POSCAR files with specified parameters.')
def command_1_1_8():
    try:
        while True:
            lower_poscar_path = color_input('\nSelect the lower POSCAR file: ', 'yellow').strip()

            if not lower_poscar_path:
                continue

            try:
                schemas.CheckPoscar(poscar_path=lower_poscar_path)
                break
            except Exception:
                color_print(f'[Error] Invalid POSCAR: {lower_poscar_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            upper_poscar_path = color_input('\nSelect the upper POSCAR file: ', 'yellow').strip()

            if not upper_poscar_path:
                continue

            try:
                schemas.CheckPoscar(poscar_path=upper_poscar_path)
                break
            except Exception:
                color_print(f'[Error] Invalid POSCAR: {upper_poscar_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            hkl_str = color_input('\nEnter the Miller indices for the lower and upper surfaces (e.g., 1 0 0; 1 0 0): ', 'yellow').strip()

            if not hkl_str:
                continue

            try:
                lower_hkl = [int(x) for x in hkl_str.split(';')[0].strip().split()]
                upper_hkl = [int(x) for x in hkl_str.split(';')[1].strip().split()]
                schemas.GenerateInterfaceFromPoscars(lower_poscar_path=lower_poscar_path, upper_poscar_path=upper_poscar_path, lower_hkl=lower_hkl, upper_hkl=upper_hkl)
                break
            except Exception:
                color_print(f'[Error] Invalid Miller indices: {hkl_str}, please double check and try again.\n', 'red')
    
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            slab_layers_str = color_input('\nEnter the number of slab layers for the lower and upper slabs (e.g., 4 4): ', 'yellow').strip()

            if not slab_layers_str:
                continue

            try:
                lower_slab_layers = int(slab_layers_str.split()[0].strip())
                upper_slab_layers = int(slab_layers_str.split()[1].strip())
                schemas.GenerateInterfaceFromPoscars(lower_poscar_path=lower_poscar_path, upper_poscar_path=upper_poscar_path, lower_hkl=lower_hkl, upper_hkl=upper_hkl, lower_slab_layers=lower_slab_layers, upper_slab_layers=upper_slab_layers)
                break
            except Exception:
                color_print(f'[Error] Invalid slab layers: {slab_layers_str}, please double check and try again.\n', 'red')
    
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            slab_vacuum_str = color_input('\nEnter the vacuum thickness in Å (e.g., 15.0): ', 'yellow').strip()

            if not slab_vacuum_str:
                continue

            try:
                slab_vacuum = float(slab_vacuum_str)
                schemas.GenerateInterfaceFromPoscars(lower_poscar_path=lower_poscar_path, upper_poscar_path=upper_poscar_path, lower_hkl=lower_hkl, upper_hkl=upper_hkl, lower_slab_layers=lower_slab_layers, upper_slab_layers=upper_slab_layers, slab_vacuum=slab_vacuum)
                break
            except Exception:
                color_print(f'[Error] Invalid vacuum thickness: {slab_vacuum_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            area_str = color_input('\nEnter the minimum and maximum interface area to search in Å² (e.g., 50.0 500.0): ', 'yellow').strip()

            if not area_str:
                continue

            try:
                min_area = float(area_str.split()[0].strip())
                max_area = float(area_str.split()[1].strip())
                schemas.GenerateInterfaceFromPoscars(lower_poscar_path=lower_poscar_path, upper_poscar_path=upper_poscar_path, lower_hkl=lower_hkl, upper_hkl=upper_hkl, lower_slab_layers=lower_slab_layers, upper_slab_layers=upper_slab_layers, slab_vacuum=slab_vacuum, min_area=min_area, max_area=max_area)
                break
            except Exception:
                color_print(f'[Error] Invalid interface area: {area_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            interface_gap_str = color_input('\nEnter the interface gap in Å (e.g., 2.0): ', 'yellow').strip()

            if not interface_gap_str:
                continue

            try:
                interface_gap = float(interface_gap_str)
                schemas.GenerateInterfaceFromPoscars(lower_poscar_path=lower_poscar_path, upper_poscar_path=upper_poscar_path, lower_hkl=lower_hkl, upper_hkl=upper_hkl, lower_slab_layers=lower_slab_layers, upper_slab_layers=upper_slab_layers, slab_vacuum=slab_vacuum, min_area=min_area, max_area=max_area, interface_gap=interface_gap)
                break
            except Exception:
                color_print(f'[Error] Invalid interface gap: {interface_gap_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            tolerance_str = color_input('\nEnter the lattice vector tolerance (%) and angle tolerance (degrees) (e.g., 5.0 5.0): ', 'yellow').strip()

            if not tolerance_str:
                continue

            try:
                uv_tolerance = float(tolerance_str.split()[0].strip())
                angle_tolerance = float(tolerance_str.split()[1].strip())
                schemas.GenerateInterfaceFromPoscars(lower_poscar_path=lower_poscar_path, upper_poscar_path=upper_poscar_path, lower_hkl=lower_hkl, upper_hkl=upper_hkl, lower_slab_layers=lower_slab_layers, upper_slab_layers=upper_slab_layers, slab_vacuum=slab_vacuum, min_area=min_area, max_area=max_area, interface_gap=interface_gap, uv_tolerance=uv_tolerance, angle_tolerance=angle_tolerance)
                break
            except Exception:
                color_print(f'[Error] Invalid lattice vector tolerance: {tolerance_str}, please double check and try again.\n', 'red')
    
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            shape_filter_str = color_input('\nDo you want to apply shape filtering to only keep the most square-like interface? [y/n]: ', 'yellow').strip().lower()

            if not shape_filter_str:
                continue

            if shape_filter_str == 'y':
                shape_filter = True
                break
            elif shape_filter_str == 'n':
                shape_filter = False
                break
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    print('')
    with yaspin(Spinners.dots, text='Generating interface structure... See details in the log file.', color='cyan') as sp:
        result = tools.generate_interface_from_poscars(
            lower_poscar_path=lower_poscar_path, 
            upper_poscar_path=upper_poscar_path, 
            lower_hkl=lower_hkl, 
            upper_hkl=upper_hkl, 
            lower_slab_layers=lower_slab_layers, 
            upper_slab_layers=upper_slab_layers, 
            slab_vacuum=slab_vacuum, 
            min_area=min_area, 
            max_area=max_area, 
            interface_gap=interface_gap, 
            uv_tolerance=uv_tolerance, 
            angle_tolerance=angle_tolerance, 
            shape_filter=shape_filter
        )
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.1.9', 'Visualize structure from POSCAR file.')
def command_1_1_9():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    result = tools.visualize_structure_from_poscar(poscar_path=poscar_path)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.2.1', 'Prepare full VASP input files (INCAR, KPOINTS, POTCAR, POSCAR).')
def command_1_2_1():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                'MPMetalRelaxSet  ->   suggested for metallic structure relaxation',
                'MPRelaxSet       ->   suggested for structure relaxation',
                'MPStaticSet      ->   suggested for static calculations',
                'MPNonSCFBandSet  ->   suggested for non-self-consistent field calculations (Band structure)',
                'MPNonSCFDOSSet   ->   suggested for non-self-consistent field calculations (Density of States)',
                'MPMDSet          ->   suggested for molecular dynamics simulations',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
            elif user_input.startswith('MPMetalRelaxSet'):
                vasp_input_sets = 'MPMetalRelaxSet'
                break
            elif user_input.startswith('MPRelaxSet'):
                vasp_input_sets = 'MPRelaxSet'
                break
            elif user_input.startswith('MPStaticSet'):
                vasp_input_sets = 'MPStaticSet'
                break
            elif user_input.startswith('MPNonSCFBandSet'):
                vasp_input_sets = 'MPNonSCFBandSet'
                break
            elif user_input.startswith('MPNonSCFDOSSet'):
                vasp_input_sets = 'MPNonSCFDOSSet'
                break
            elif user_input.startswith('MPMDSet'):
                vasp_input_sets = 'MPMDSet'
                break
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()
    
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    result = tools.generate_vasp_inputs_from_poscar(poscar_path=poscar_path, vasp_input_sets=vasp_input_sets, only_incar=False)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.2.2', 'Generate INCAR templates (relaxation, static, etc.).')
def command_1_2_2():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                'MPMetalRelaxSet  ->   suggested for metallic structure relaxation',
                'MPRelaxSet       ->   suggested for structure relaxation',
                'MPStaticSet      ->   suggested for static calculations',
                'MPNonSCFBandSet  ->   suggested for non-self-consistent field calculations (Band structure)',
                'MPNonSCFDOSSet   ->   suggested for non-self-consistent field calculations (Density of States)',
                'MPMDSet          ->   suggested for molecular dynamics simulations',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
            elif user_input.startswith('MPMetalRelaxSet'):
                vasp_input_sets = 'MPMetalRelaxSet'
                break
            elif user_input.startswith('MPRelaxSet'):
                vasp_input_sets = 'MPRelaxSet'
                break
            elif user_input.startswith('MPStaticSet'):
                vasp_input_sets = 'MPStaticSet'
                break
            elif user_input.startswith('MPNonSCFBandSet'):
                vasp_input_sets = 'MPNonSCFBandSet'
                break
            elif user_input.startswith('MPNonSCFDOSSet'):
                vasp_input_sets = 'MPNonSCFDOSSet'
                break
            elif user_input.startswith('MPMDSet'):
                vasp_input_sets = 'MPMDSet'
                break
            elif user_input.startswith('NEBSet'):
                vasp_input_sets = 'NEBSet'
                break
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()
    
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    result = tools.generate_vasp_inputs_from_poscar(poscar_path=poscar_path, vasp_input_sets=vasp_input_sets, only_incar=True)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.2.3', 'Generate KPOINTS with specified accuracy.')
def command_1_2_3():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                'Gamma-centered  ->  Construct an automatic Gamma-centered Kpoint grid.',
                'Monkhorst-Pack  ->  Construct an automatic Monkhorst-Pack Kpoint grid.',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
            elif user_input.startswith('Gamma-centered'):
                gamma_centered = True
                break
            elif user_input.startswith('Monkhorst-Pack'):
                gamma_centered = False
                break
            else:
                continue
            
    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                'Low     ->  Suitable for preliminary calculations, grid density = 1000 / number of atoms',
                'Medium  ->  Balanced accuracy and computational cost, grid density = 3000 / number of atoms',
                'High    ->  High accuracy for production runs, grid density = 5000 / number of atoms',
                'Custom  ->  Specify custom grid density',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
            elif user_input.startswith('Low'):
                accuracy_level = 'Low'
                break
            elif user_input.startswith('Medium'):
                accuracy_level = 'Medium'
                break
            elif user_input.startswith('High'):
                accuracy_level = 'High'
                break
            elif user_input.startswith('Custom'):
                try:
                    while True:
                        custom_kppa_str = color_input('\nEnter custom k-points per atom (kppa) as a positive integer (e.g., 2000): ', 'yellow').strip()
                        
                        if not custom_kppa_str:
                            continue

                        try:
                            custom_kppa = int(custom_kppa_str)
                            if custom_kppa <= 0:
                                color_print(f'\n[Error] K-points per atom must be a positive integer. You entered: {custom_kppa_str}\n', 'red')
                                continue
                            break

                        except Exception:
                            color_print(f'\n[Error] Invalid k-points per atom: {custom_kppa_str}, please enter a positive integer and try again.\n', 'red')
                            continue

                
                except (KeyboardInterrupt, EOFError):
                    color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
                    time.sleep(1)
                    return
                
                accuracy_level = 'Custom'
                break
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    result = tools.customize_vasp_kpoints_with_accuracy(poscar_path=poscar_path, accuracy_level=accuracy_level, gamma_centered=gamma_centered, custom_kppa=custom_kppa if accuracy_level=='Custom' else None)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.2.4', 'Generate HPC Slurm job submission script for VASP calculations.')
def command_1_2_4():
    try:
        partition = color_input('\nEnter the HPC partition/queue name (default: normal): ', 'yellow').strip() or 'normal'
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    try:
        while True:
            nodes = color_input('\nEnter the number of nodes (default: 1): ', 'yellow').strip()
            try:
                if not nodes:
                    nodes = 1
                else:
                    nodes = int(nodes)
                schemas.GenerateVaspInputsHpcSlurmScript(nodes=nodes)
                break
            except ValueError:
                color_print(f"\n[Error] Invalid number of nodes: {nodes}. Please enter a positive integer.\n", 'red')
                continue
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            ntasks = color_input('\nEnter the number of tasks per node (default: 8): ', 'yellow').strip()
            try:
                if not ntasks:
                    ntasks = 8
                else:
                    ntasks = int(ntasks)
                schemas.GenerateVaspInputsHpcSlurmScript(ntasks=ntasks)
                break
            except ValueError:
                color_print(f"\n[Error] Invalid number of tasks: {ntasks}. Please enter a positive integer.\n", 'red')
                continue
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            walltime = color_input('\nEnter the job walltime in format HH:MM:SS (default: 01:00:00): ', 'yellow').strip()
            try:
                if not walltime:
                    walltime = '01:00:00'
                schemas.GenerateVaspInputsHpcSlurmScript(walltime=walltime)
                break
            except ValueError:
                color_print(f"\n[Error] Invalid walltime format: {walltime}. Please use 'HH:MM:SS' format.\n", 'red')
                continue
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    try:
        jobname = color_input('\nEnter the job name (default: masgent_job): ', 'yellow').strip()
        if not jobname:
            jobname = 'masgent_job'
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    result = tools.generate_vasp_inputs_hpc_slurm_script(
        partition=partition,
        nodes=nodes,
        ntasks=ntasks,
        walltime=walltime,
        jobname=jobname,
        command='srun vasp_std > vasp.out'
    )
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.3.1', 'Generate VASP workflow for convergence tests for k-points and energy cutoff based on given POSCAR.')
def command_1_3_1():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                'All      ->  Convergence tests for both energy cutoff and k-points',
                'ENCUT    ->  Convergence test for energy cutoff only',
                'KPOINTS  ->  Convergence test for k-points only',
            ] + global_commands()

            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()

            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
            elif user_input.startswith('All'):
                test_type = 'all'
                break
            elif user_input.startswith('ENCUT'):
                test_type = 'encut'
                break
            elif user_input.startswith('KPOINTS'):
                test_type = 'kpoints'
                break
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()
    
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    if test_type == 'encut':
        try:
            while True:
                encut_levels_str = color_input('\nEnter the energy cutoff levels you want to test (e.g., 300 400 500 600 700): ', 'yellow').strip()

                if not encut_levels_str:
                    continue

                try:
                    encut_levels = [int(x) for x in encut_levels_str.split()]
                    schemas.GenerateVaspWorkflowOfConvergenceTests(poscar_path=poscar_path, test_type=test_type, encut_levels=encut_levels)
                    break
                except Exception:
                    color_print(f'[Error] Invalid energy cutoff levels: {encut_levels_str}, please double check and try again.\n', 'red')
        
        except (KeyboardInterrupt, EOFError):
            color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
            time.sleep(1)
            return
        
    elif test_type == 'kpoints':
        try:
            while True:
                kpoint_levels_str = color_input('\nEnter the k-point grid density levels you want to test (e.g., 1000 2000 3000 4000 5000): ', 'yellow').strip()

                if not kpoint_levels_str:
                    continue

                try:
                    kpoint_levels = [int(x) for x in kpoint_levels_str.split()]
                    schemas.GenerateVaspWorkflowOfConvergenceTests(poscar_path=poscar_path, test_type=test_type, kpoint_levels=kpoint_levels)
                    break
                except Exception:
                    color_print(f'[Error] Invalid k-point levels: {kpoint_levels_str}, please double check and try again.\n', 'red')
        
        except (KeyboardInterrupt, EOFError):
            color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
            time.sleep(1)
            return
        
    else:
        try:
            while True:
                encut_levels_str = color_input('\nEnter the energy cutoff levels you want to test (e.g., 300 400 500 600 700): ', 'yellow').strip()

                if not encut_levels_str:
                    continue

                try:
                    encut_levels = [int(x) for x in encut_levels_str.split()]
                    schemas.GenerateVaspWorkflowOfConvergenceTests(poscar_path=poscar_path, test_type=test_type, encut_levels=encut_levels)
                    break
                except Exception:
                    color_print(f'[Error] Invalid energy cutoff levels: {encut_levels_str}, please double check and try again.\n', 'red')
        
        except (KeyboardInterrupt, EOFError):
            color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
            time.sleep(1)
            return
        
        try:
            while True:
                kpoint_levels_str = color_input('\nEnter the k-point grid density levels you want to test (e.g., 1000 2000 3000 4000 5000): ', 'yellow').strip()

                if not kpoint_levels_str:
                    continue

                try:
                    kpoint_levels = [int(x) for x in kpoint_levels_str.split()]
                    schemas.GenerateVaspWorkflowOfConvergenceTests(poscar_path=poscar_path, test_type=test_type, kpoint_levels=kpoint_levels)
                    break
                except Exception:
                    color_print(f'[Error] Invalid k-point levels: {kpoint_levels_str}, please double check and try again.\n', 'red')
        
        except (KeyboardInterrupt, EOFError):
            color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
            time.sleep(1)
            return
    
    print('')
    with yaspin(Spinners.dots, text='Generating VASP workflow for convergence tests...', color='cyan') as sp:
        if test_type == 'encut':
            result = tools.generate_vasp_workflow_of_convergence_tests(poscar_path=poscar_path, test_type=test_type, encut_levels=encut_levels)
        elif test_type == 'kpoints':
            result = tools.generate_vasp_workflow_of_convergence_tests(poscar_path=poscar_path, test_type=test_type, kpoint_levels=kpoint_levels)
        else:
            result = tools.generate_vasp_workflow_of_convergence_tests(poscar_path=poscar_path, test_type=test_type, encut_levels=encut_levels, kpoint_levels=kpoint_levels)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.3.2', 'Generate VASP workflow of equation of state (EOS) calculations based on given POSCAR.')
def command_1_3_2():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    try:
        while True:
            scale_factors_str = color_input('\nEnter the volume scale factors for EOS calculations (e.g., 0.94 0.96 0.98 1.00 1.02 1.04 1.06): ', 'yellow').strip()

            if not scale_factors_str:
                continue

            try:
                scale_factors = [float(x) for x in scale_factors_str.split()]
                schemas.GenerateVaspWorkflowOfEos(poscar_path=poscar_path, scale_factors=scale_factors)
                break
            except Exception:
                color_print(f'[Error] Invalid scale factors: {scale_factors_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    print('')
    with yaspin(Spinners.dots, text='Generating VASP workflow for EOS calculations...', color='cyan') as sp:
        result = tools.generate_vasp_workflow_of_eos(poscar_path=poscar_path, scale_factors=scale_factors)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.3.3', 'Generate VASP workflow for elastic constants calculations based on given POSCAR.')
def command_1_3_3():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    print('')
    with yaspin(Spinners.dots, text='Generating VASP workflow for elastic constants calculations...', color='cyan') as sp:
        result = tools.generate_vasp_workflow_of_elastic_constants(poscar_path=poscar_path)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.3.4', 'Generate VASP workflow for ab initio molecular dynamics (AIMD) simulations based on given POSCAR.')
def command_1_3_4():
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    try:
        while True:
            temperatures_str = color_input('\nEnter the simulation temperature(s) in K (e.g., 500 1000 1500 2000 2500): ', 'yellow').strip()

            if not temperatures_str:
                continue

            try:
                temperatures = [int(x) for x in temperatures_str.split()]
                schemas.GenerateVaspWorkflowOfAimd(poscar_path=poscar_path, temperatures=temperatures)
                break
            except Exception:
                color_print(f'[Error] Invalid temperature: {temperatures_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            md_steps_str = color_input('\nEnter the number of MD steps (e.g., 1000): ', 'yellow').strip()

            if not md_steps_str:
                continue

            try:
                md_steps = int(md_steps_str)
                schemas.GenerateVaspWorkflowOfAimd(poscar_path=poscar_path, temperatures=temperatures, md_steps=md_steps)
                break
            except Exception:
                color_print(f'[Error] Invalid MD steps: {md_steps_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            md_timestep_str = color_input('\nEnter the MD timestep in fs (e.g., 2.0): ', 'yellow').strip()

            if not md_timestep_str:
                continue

            try:
                md_timestep = float(md_timestep_str)
                schemas.GenerateVaspWorkflowOfAimd(poscar_path=poscar_path, temperatures=temperatures, md_steps=md_steps, md_timestep=md_timestep)
                break
            except Exception:
                color_print(f'[Error] Invalid MD timestep: {md_timestep_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    print('')
    with yaspin(Spinners.dots, text='Generating VASP workflow for AIMD simulations...', color='cyan') as sp:
        result = tools.generate_vasp_workflow_of_aimd(poscar_path=poscar_path, temperatures=temperatures, md_steps=md_steps, md_timestep=md_timestep)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.3.5', 'Generate VASP workflow for Nudged Elastic Band (NEB) calculations based on given initial and final POSCARs.')
def command_1_3_5():
    try:
        while True:
            initial_poscar_path = color_input('\nEnter the path to the initial POSCAR file: ', 'yellow').strip()
            
            if not initial_poscar_path:
                continue

            try:
                schemas.CheckPoscar(poscar_path=initial_poscar_path)
                break
            except Exception:
                color_print(f'[Error] Invalid POSCAR: {initial_poscar_path}, please double check and try again.\n', 'red')
    
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            final_poscar_path = color_input('\nEnter the path to the final POSCAR file: ', 'yellow').strip()
            
            if not final_poscar_path:
                continue

            try:
                schemas.CheckPoscar(poscar_path=final_poscar_path)
                break
            except Exception:
                color_print(f'[Error] Invalid POSCAR: {final_poscar_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            num_images_str = color_input('\nEnter the number of intermediate images (e.g., 5): ', 'yellow').strip()

            if not num_images_str:
                continue

            try:
                num_images = int(num_images_str)
                schemas.GenerateVaspWorkflowOfNeb(initial_poscar_path=initial_poscar_path, final_poscar_path=final_poscar_path, num_images=num_images)
                break
            except Exception:
                color_print(f'[Error] Invalid number of images: {num_images_str}, please double check and try again.\n', 'red')
    
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    print('')
    with yaspin(Spinners.dots, text='Generating VASP workflow for NEB calculations...', color='cyan') as sp:
        result = tools.generate_vasp_workflow_of_neb(initial_poscar_path=initial_poscar_path, final_poscar_path=final_poscar_path, num_images=num_images)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.4.1', 'Convergence test analysis')
def command_1_4_1():
    try:
        while True:
            convergence_tests_dir = color_input('\nEnter the convergence tests directory path that contains encut and kpoints subdirectories: ', 'yellow').strip()
            
            if not convergence_tests_dir:
                continue

            try:
                os.path.exists(convergence_tests_dir)
                break
            except Exception:
                color_print(f'[Error] Invalid directory: {convergence_tests_dir}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    print('')
    with yaspin(Spinners.dots, text='Analyzing VASP convergence tests...', color='cyan') as sp:
        result = tools.analyze_vasp_workflow_of_convergence_tests(convergence_tests_dir=convergence_tests_dir)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.4.2', 'Equation of State (EOS) analysis')
def command_1_4_2():
    try:
        while True:
            eos_dir = color_input('\nEnter the EOS calculations directory path that contains volume-scaled subdirectories: ', 'yellow').strip()
            
            if not eos_dir:
                continue

            try:
                os.path.exists(eos_dir)
                break
            except Exception:
                color_print(f'[Error] Invalid directory: {eos_dir}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    print('')
    with yaspin(Spinners.dots, text='Analyzing VASP EOS calculations...', color='cyan') as sp:
        result = tools.analyze_vasp_workflow_of_eos(eos_dir=eos_dir)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.4.3', 'Elastic constants analysis')
def command_1_4_3():
    try:
        while True:
            elastic_constants_dir = color_input('\nEnter the elastic constants calculations directory path that contains strain subdirectories: ', 'yellow').strip()

            if not elastic_constants_dir:
                continue

            try:
                os.path.exists(elastic_constants_dir)
                break
            except Exception:
                color_print(f'[Error] Invalid directory: {elastic_constants_dir}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    print('')
    with yaspin(Spinners.dots, text='Analyzing VASP elastic constants calculations...', color='cyan') as sp:
        result = tools.analyze_vasp_workflow_of_elastic_constants(elastic_constants_dir=elastic_constants_dir)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.4.4', 'Ab initio molecular dynamics (AIMD) analysis')
def command_1_4_4():
    try:
        while True:
            aimd_dir = color_input('\nEnter the AIMD simulations directory path that contains MD temperature subdirectories: ', 'yellow').strip()

            if not aimd_dir:
                continue

            try:
                os.path.exists(aimd_dir)
                break
            except Exception:
                color_print(f'[Error] Invalid directory: {aimd_dir}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            specie = color_input('\nEnter the atomic specie symbol for MSD calculation (e.g., Li): ', 'yellow').strip()

            if not specie:
                continue

            try:
                schemas.CheckElement(element_symbol=specie)
                for root, dirs, files in os.walk(aimd_dir):
                    if 'POSCAR' in files:
                        poscar_path = os.path.join(root, 'POSCAR')
                        schemas.CheckElementExistence(poscar_path=poscar_path, element_symbol=specie)
                break
            except Exception:
                color_print(f'[Error] Invalid atomic specie symbol: {specie}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    print('')
    with yaspin(Spinners.dots, text='Analyzing VASP AIMD simulations...', color='cyan') as sp:
        result = tools.analyze_vasp_workflow_of_aimd(aimd_dir=aimd_dir, specie=specie)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('1.4.5', 'Nudged Elastic Band (NEB) analysis')
def command_1_4_5():
    try:
        while True:
            neb_dir = color_input('\nEnter the NEB calculations directory path that contains image subdirectories: ', 'yellow').strip()

            if not neb_dir:
                continue

            try:
                os.path.exists(neb_dir)
                break
            except Exception:
                color_print(f'[Error] Invalid directory: {neb_dir}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    print('')
    with yaspin(Spinners.dots, text='Analyzing VASP NEB calculations...', color='cyan') as sp:
        result = tools.analyze_vasp_workflow_of_neb(neb_dir=neb_dir)
    color_print(result['message'], 'green')
    time.sleep(3)

def call_mlps(mlps_type: str):
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '1. Single Point Energy Calculation',
                '2. Equation of State (EOS) Calculation',
                '3. Elastic Constants Calculation',
                '4. Molecular Dynamics Simulation (NVT)',
            ] + global_commands()
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()
            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
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
                exit_and_cleanup()
            elif user_input.startswith('1'):
                task_type = 'single'
                break
            elif user_input.startswith('2'):
                task_type = 'eos'
                break
            elif user_input.startswith('3'):
                task_type = 'elastic'
                break
            elif user_input.startswith('4'):
                task_type = 'md'
                break
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()
    
    try:
        poscar_path = check_poscar()
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return

    if task_type in ['single', 'eos', 'elastic']:
        try:
            while True:
                fmax_str = color_input('\nEnter the maximum force convergence criterion in eV/Å (default: 0.1): ', 'yellow').strip()

                if not fmax_str:
                    fmax = 0.1
                    break

                try:
                    fmax = float(fmax_str)
                    schemas.RunSimulationUsingMlps(poscar_path=poscar_path, fmax=fmax)
                    break
                except Exception:
                    color_print(f'[Error] Invalid force criterion: {fmax_str}, please double check and try again.\n', 'red')
        
        except (KeyboardInterrupt, EOFError):
            color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
            time.sleep(1)
            return
        
        try:
            while True:
                max_steps_str = color_input('\nEnter the maximum number of optimization steps (default: 500): ', 'yellow').strip()

                if not max_steps_str:
                    max_steps = 500
                    break

                try:
                    max_steps = int(max_steps_str)
                    schemas.RunSimulationUsingMlps(poscar_path=poscar_path, max_steps=max_steps)
                    break
                except Exception:
                    color_print(f'[Error] Invalid maximum steps: {max_steps_str}, please double check and try again.\n', 'red')
        
        except (KeyboardInterrupt, EOFError):
            color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
            time.sleep(1)
            return
        
        if task_type == 'eos':
            try:
                while True:
                    scale_factors_str = color_input('\nEnter the volume scale factors for EOS calculations (e.g., 0.94 0.96 0.98 1.00 1.02 1.04 1.06): ', 'yellow').strip()

                    if not scale_factors_str:
                        continue

                    try:
                        scale_factors = [float(x) for x in scale_factors_str.split()]
                        schemas.RunSimulationUsingMlps(poscar_path=poscar_path, fmax=fmax, max_steps=max_steps, scale_factors=scale_factors)
                        break
                    except Exception:
                        color_print(f'[Error] Invalid scale factors: {scale_factors_str}, please double check and try again.\n', 'red')

            except (KeyboardInterrupt, EOFError):
                color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
                time.sleep(1)
                return

        print('')
        with yaspin(Spinners.dots, text=f'Running simulation using {mlps_type}... See details in the log file. ', color='cyan') as sp:
            result = tools.run_simulation_using_mlps(poscar_path=poscar_path, mlps_type=mlps_type, task_type=task_type, fmax=fmax, max_steps=max_steps, scale_factors=scale_factors if task_type=='eos' else [0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06])
        color_print(result['message'], 'green')
        time.sleep(3)
    
    elif task_type == 'md':
        try:
            while True:
                temperature_str = color_input('\nEnter the simulation temperature in K (default: 1000): ', 'yellow').strip()

                if not temperature_str:
                    temperature = 1000
                    break

                try:
                    temperature = int(temperature_str)
                    schemas.RunSimulationUsingMlps(poscar_path=poscar_path, temperature=temperature)
                    break
                except Exception:
                    color_print(f'[Error] Invalid temperature: {temperature_str}, please double check and try again.\n', 'red')
        
        except (KeyboardInterrupt, EOFError):
            color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
            time.sleep(1)
            return
        
        try:
            while True:
                md_steps_str = color_input('\nEnter the number of MD steps (default: 1000): ', 'yellow').strip()

                if not md_steps_str:
                    md_steps = 1000
                    break
                
                try:
                    md_steps = int(md_steps_str)
                    schemas.RunSimulationUsingMlps(poscar_path=poscar_path, md_steps=md_steps)
                    break
                except Exception:
                    color_print(f'[Error] Invalid MD steps: {md_steps_str}, please double check and try again.\n', 'red')

        except (KeyboardInterrupt, EOFError):
            color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
            time.sleep(1)
            return
        
        try:
            while True:
                md_timestep_str = color_input('\nEnter the MD timestep in fs (default: 5.0 fs): ', 'yellow').strip()

                if not md_timestep_str:
                    md_timestep = 5.0
                    break

                try:
                    md_timestep = float(md_timestep_str)
                    schemas.RunSimulationUsingMlps(poscar_path=poscar_path, md_timestep=md_timestep)
                    break
                except Exception:
                    color_print(f'[Error] Invalid MD timestep: {md_timestep_str}, please double check and try again.\n', 'red')
        
        except (KeyboardInterrupt, EOFError):
            color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
            time.sleep(1)
            return

        print('')
        with yaspin(Spinners.dots, text=f'Running simulation using {mlps_type}... See details in the log file. ', color='cyan') as sp:
            result = tools.run_simulation_using_mlps(poscar_path=poscar_path, mlps_type=mlps_type, task_type=task_type, temperature=temperature, md_steps=md_steps, md_timestep=md_timestep)
        color_print(result['message'], 'green')
        time.sleep(3)

@register('2.1', 'SevenNet')
def command_2_1():
    call_mlps(mlps_type='SevenNet')

@register('2.2', 'CHGNet')
def command_2_2():
    call_mlps(mlps_type='CHGNet')

@register('2.3', 'Orb-v3')
def command_2_3():
    call_mlps(mlps_type='Orb-v3')

@register('2.4', 'MatterSim')
def command_2_4():
    call_mlps(mlps_type='MatterSim')

@register('3.1.1', 'Feature analysis and visualization')
def command_3_1_1():
    try:
        while True:
            input_data_path = color_input('\nEnter the path to the input feature data file (CSV): ', 'yellow').strip()

            if not input_data_path:
                continue

            try:
                schemas.CheckCSVFile(file_path=input_data_path)
                break
            except Exception:
                color_print(f'[Error] Invalid CSV file: {input_data_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            output_data_path = color_input('\nEnter the path to the output feature data file (CSV): ', 'yellow').strip()

            if not output_data_path:
                continue

            try:
                schemas.CheckCSVFile(file_path=output_data_path)
                break
            except Exception:
                color_print(f'[Error] Invalid directory: {output_data_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    result = tools.analyze_features_for_machine_learning(input_data_path=input_data_path, output_data_path=output_data_path)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('3.1.2', 'Dimensionality reduction (if too many features)')
def command_3_1_2():
    try:
        while True:
            input_data_path = color_input('\nEnter the path to the input feature data file (CSV): ', 'yellow').strip()

            if not input_data_path:
                continue

            try:
                schemas.CheckCSVFile(file_path=input_data_path)
                break
            except Exception:
                color_print(f'[Error] Invalid CSV file: {input_data_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            n_components_str = color_input('\nEnter the number of principal components to reduce to (e.g., 2): ', 'yellow').strip()

            if not n_components_str:
                continue

            try:
                n_components = int(n_components_str)
                schemas.ReduceDimensionsForMachineLearning(input_data_path=input_data_path, n_components=n_components)
                break
            except Exception:
                color_print(f'[Error] Invalid number of components: {n_components_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    result = tools.reduce_dimensions_for_machine_learning(input_data_path=input_data_path, n_components=n_components)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('3.1.3', 'Data augmentation (if limited data)')
def command_3_1_3():
    try:
        while True:
            input_data_path = color_input('\nEnter the path to the input feature data file (CSV): ', 'yellow').strip()

            if not input_data_path:
                continue

            try:
                schemas.CheckCSVFile(file_path=input_data_path)
                break
            except Exception:
                color_print(f'[Error] Invalid CSV file: {input_data_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            output_data_path = color_input('\nEnter the path to the output feature data file (CSV): ', 'yellow').strip()

            if not output_data_path:
                continue

            try:
                schemas.CheckCSVFile(file_path=output_data_path)
                break
            except Exception:
                color_print(f'[Error] Invalid directory: {output_data_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):   
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            num_augmentations_str = color_input('\nEnter the number of augmentations to perform (e.g., 100): ', 'yellow').strip()

            if not num_augmentations_str:
                continue

            try:
                num_augmentations = int(num_augmentations_str)
                schemas.AugmentDataForMachineLearning(input_data_path=input_data_path, output_data_path=output_data_path, num_augmentations=num_augmentations)
                break
            except Exception:
                color_print(f'[Error] Invalid number of augmentations: {num_augmentations_str}, please double check and try again.\n', 'red')
    
    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    result = tools.augment_data_for_machine_learning(input_data_path=input_data_path, output_data_path=output_data_path, num_augmentations=num_augmentations)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('3.2', 'Model Design & Hyperparameter Tuning')
def command_3_2():
    try:
        while True:
            input_data_path = color_input('\nEnter the path to the input feature data file (CSV): ', 'yellow').strip()

            if not input_data_path:
                continue

            try:
                schemas.CheckCSVFile(file_path=input_data_path)
                break
            except Exception:
                color_print(f'[Error] Invalid CSV file: {input_data_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            output_data_path = color_input('\nEnter the path to the output feature data file (CSV): ', 'yellow').strip()

            if not output_data_path:
                continue

            try:
                schemas.CheckCSVFile(file_path=output_data_path)
                break
            except Exception:
                color_print(f'[Error] Invalid directory: {output_data_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            num_trials_str = color_input('\nEnter the number of hyperparameter tuning trials (e.g., 50): ', 'yellow').strip()

            if not num_trials_str:
                continue

            try:
                num_trials = int(num_trials_str)
                schemas.DesignModelForMachineLearning(input_data_path=input_data_path, output_data_path=output_data_path, n_trials=num_trials)
                break
            except Exception:
                color_print(f'[Error] Invalid number of trials: {num_trials_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    result = tools.design_model_for_machine_learning(input_data_path=input_data_path, output_data_path=output_data_path, n_trials=num_trials)
    color_print(result['message'], 'green')
    time.sleep(3)

@register('3.3', 'Model Training & Evaluation')
def command_3_3():
    try:
        while True:
            input_data_path = color_input('\nEnter the path to the input feature data file (CSV): ', 'yellow').strip()

            if not input_data_path:
                continue

            try:
                schemas.CheckCSVFile(file_path=input_data_path)
                break
            except Exception:
                color_print(f'[Error] Invalid CSV file: {input_data_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            output_data_path = color_input('\nEnter the path to the output feature data file (CSV): ', 'yellow').strip()

            if not output_data_path:
                continue

            try:
                schemas.CheckCSVFile(file_path=output_data_path)
                break
            except Exception:
                color_print(f'[Error] Invalid directory: {output_data_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            best_model_path = color_input('\nEnter the path to the best model file from model design (e.g., best_model.pkl): ', 'yellow').strip()

            if not best_model_path:
                continue

            try:
                schemas.CheckPklFile(file_path=best_model_path)
                break
            except Exception:
                color_print(f'[Error] Invalid model file: {best_model_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            best_model_params_path = color_input('\nEnter the path to the best model hyperparameters file from model design (e.g., best_model_params.log): ', 'yellow').strip()

            if not best_model_params_path:
                continue

            try:
                schemas.CheckLogFile(file_path=best_model_params_path)
                break
            except Exception:
                color_print(f'[Error] Invalid hyperparameters file: {best_model_params_path}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            max_epochs_str = color_input('\nEnter the maximum number of training epochs (e.g., 1000): ', 'yellow').strip()

            if not max_epochs_str:
                continue

            try:
                max_epochs = int(max_epochs_str)
                schemas.TrainModelForMachineLearning(
                    input_data_path=input_data_path, 
                    output_data_path=output_data_path, 
                    best_model_path=best_model_path, 
                    best_model_params_path=best_model_params_path, 
                    max_epochs=max_epochs
                    )
                break
            except Exception:
                color_print(f'[Error] Invalid maximum epochs: {max_epochs_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    try:
        while True:
            patience_str = color_input('\nEnter the early stopping patience (number of epochs with no improvement) (e.g., 50): ', 'yellow').strip()

            if not patience_str:
                continue

            try:
                patience = int(patience_str)
                schemas.TrainModelForMachineLearning(
                    input_data_path=input_data_path, 
                    output_data_path=output_data_path, 
                    best_model_path=best_model_path, 
                    best_model_params_path=best_model_params_path, 
                    max_epochs=max_epochs, 
                    patience=patience
                    )
                break
            except Exception:
                color_print(f'[Error] Invalid patience: {patience_str}, please double check and try again.\n', 'red')

    except (KeyboardInterrupt, EOFError):
        color_print('\n[Error] Input cancelled. Returning to previous menu...\n', 'red')
        time.sleep(1)
        return
    
    result = tools.train_model_for_machine_learning(
        input_data_path=input_data_path, 
        output_data_path=output_data_path, 
        best_model_path=best_model_path, 
        best_model_params_path=best_model_params_path, 
        max_epochs=max_epochs, 
        patience=patience
        )
    color_print(result['message'], 'green')
    time.sleep(3)