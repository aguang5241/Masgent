# !/usr/bin/env python3

import sys
from bullet import Bullet, colors

from masgent.ai_mode import ai_backend
from masgent.cli_mode.cli_run import register, run_command
from masgent.utils import (
    color_print, 
    print_banner, 
    print_help, 
    global_commands, 
    start_new_session
    )


###############################################
#                                             #
# Below are wrappers for main command entries #
#                                             #
###############################################

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
                'AI    ->  Chat with the Masgent AI',
                'New   ->  Start a new session',
                'Help  ->  Show available functions',
                'Exit  ->  Quit the Masgent',
            ]
            cli = Bullet(prompt=prompt, choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()
            
            if user_input.startswith('AI'):
                ai_backend.main()
            elif user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
                color_print('\nExiting Masgent... Goodbye!\n', 'green')
                sys.exit(0)
            elif user_input.startswith('1'):
                run_command('1')
            elif user_input.startswith('2'):
                run_command('2')
            elif user_input.startswith('3'):
                run_command('3')
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1', 'Entry point for Density Functional Theory (DFT) Simulations.')
def command_1():
    try:
        while True:
            choices = [
                '1.1 Structure Preparation & Manipulation',
                '1.2 VASP Input File Preparation',
                '1.3 Standard VASP Workflows',
                '1.4 VASP Output Analysis',
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
            elif user_input.startswith('1.1'):
                run_command('1.1')
            elif user_input.startswith('1.2'):
                run_command('1.2')
            elif user_input.startswith('1.3'):
                run_command('1.3')
            elif user_input.startswith('1.4'):
                run_command('1.4')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)


@register('1.1', 'Structure Preparation & Manipulation.')
def command_1_1():
    try:
        while True:
            choices = [
                '1.1.1 Generate POSCAR from chemical formula',
                '1.1.2 Convert POSCAR coordinates (Direct <-> Cartesian)',
                '1.1.3 Convert structure file formats (CIF, POSCAR, XYZ)',
                '1.1.4 Generate structures with defects (Vacancies, Substitutions, Interstitials with Voronoi)',
                '1.1.5 Generate supercells',
                '1.1.6 Generate special quasirandom structures (SQS)',
                '1.1.7 Generate surface slabs',
                '1.1.8 Generate interface structures',
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
            elif user_input.startswith('1.1.1'):
                run_command('1.1.1')
            elif user_input.startswith('1.1.2'):
                run_command('1.1.2')
            elif user_input.startswith('1.1.3'):
                run_command('1.1.3')
            elif user_input.startswith('1.1.4'):
                run_command('1.1.4')
            elif user_input.startswith('1.1.5'):
                run_command('1.1.5')
            elif user_input.startswith('1.1.6'):
                run_command('1.1.6')
            elif user_input.startswith('1.1.7'):
                run_command('1.1.7')
            elif user_input.startswith('1.1.8'):
                run_command('1.1.8')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1.2', 'VASP Input File Preparation')
def command_1_2():
    try:
        while True:
            choices = [
                '1.2.1 Prepare full VASP input files (INCAR, KPOINTS, POTCAR, POSCAR)',
                '1.2.2 Generate INCAR templates (relaxation, static, etc.)',
                '1.2.3 Gernerate KPOINTS with specified accuracy',
                '1.2.4 Generate HPC job submission script',
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
            elif user_input.startswith('1.2.1'):
                run_command('1.2.1')
            elif user_input.startswith('1.2.2'):
                run_command('1.2.2')
            elif user_input.startswith('1.2.3'):
                run_command('1.2.3')
            elif user_input.startswith('1.2.4'):
                run_command('1.2.4')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1.3', 'Standard VASP Workflows.')
def command_1_3():
    try:
        while True:
            choices = [
                '1.3.1 Convergence testing (ENCUT, KPOINTS)',
                '1.3.2 Equation of State (EOS)',
                '1.3.3 Elastic constants calculations',
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
            elif user_input.startswith('1.3.1'):
                run_command('1.3.1')
            elif user_input.startswith('1.3.2'):
                run_command('1.3.2')
            elif user_input.startswith('1.3.3'):
                run_command('1.3.3')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1.4', 'VASP Output Analysis')
def command_1_4():
    try:
        while True:
            choices = [
                '(To be implemented)',
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
            elif user_input == '(To be implemented)':
                print('This feature is under development. Stay tuned!')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)