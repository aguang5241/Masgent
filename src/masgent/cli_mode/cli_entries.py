# !/usr/bin/env python3

import sys
from bullet import Bullet, colors

from masgent.ai_mode import ai_backend
from masgent.utils import color_print, print_banner, print_help

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
            elif user_input.startswith('1'):
                run_command('1')
            elif user_input.startswith('2'):
                run_command('2')
            elif user_input.startswith('3'):
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
                '1.1 Structure Preparation & Manipulation',
                '1.2 VASP Input File Preparation',
                '1.3 VASP Output Analysis',
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
            elif user_input.startswith('1.1'):
                run_command('1.1')
            elif user_input.startswith('1.2'):
                run_command('1.2')
            elif user_input.startswith('1.3'):
                run_command('1.3')
            else:
                pass

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
                '1.1.4 Generate supercells',
                '1.1.5 Generate structures with defects (Vacancies, Interstitials, Substitutions)',
                '1.1.6 Generate special quasirandom structures (SQS)',
                '1.1.7 Generate surface slabs',
                '1.1.8 Generate interface structures',
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
                pass

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1.2', 'VASP Input File Preparation')
def command_1_2():
    try:
        while True:
            choices = [
                '1.2.1 Generate INCAR templates (relaxation, static, MD, etc.)',
                '1.2.2 Gernerate KPOINTS with specified accuracy',
                '1.2.3 Prepare full VASP input files (INCAR, KPOINTS, POTCAR, POSCAR)',
                '1.2.4 Generate HPC job submission script',
                '1.2.5 Generate standard VASP calculation workflows',
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
            elif user_input.startswith('1.2.1'):
                run_command('1.2.1')
            elif user_input.startswith('1.2.2'):
                run_command('1.2.2')
            elif user_input.startswith('1.2.3'):
                run_command('1.2.3')
            elif user_input.startswith('1.2.4'):
                run_command('1.2.4')
            elif user_input.startswith('1.2.5'):
                run_command('1.2.5')
            else:
                pass

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1.2.5', 'Generate standard VASP calculation workflows.')
def command_1_2_5():
    try:
        while True:
            choices = [
                '1.2.5.1 Convergence testing (ENCUT, KPOINTS)',
                '1.2.5.2 Equation of State (EOS)',
                '1.2.5.3 Elastic constants',
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
            elif user_input.startswith('1.2.5.1'):
                run_command('1.2.5.1')
            elif user_input.startswith('1.2.5.2'):
                run_command('1.2.5.2')
            elif user_input.startswith('1.2.5.3'):
                run_command('1.2.5.3')
            else:
                pass

    except (KeyboardInterrupt, EOFError):
        color_print('\nExiting Masgent... Goodbye!\n', 'green')
        sys.exit(0)

@register('1.3', 'VASP Output Analysis')
def command_1_3():
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