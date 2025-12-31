# !/usr/bin/env python3

from bullet import Bullet, colors

from masgent.cli_mode.cli_run import register, run_command
from masgent.utils.utils import (
    print_help, 
    global_commands, 
    start_new_session,
    clear_and_print_entry_message,
    clear_and_print_banner_and_entry_message,
    exit_and_cleanup,
    )


###############################################
#                                             #
# Below are wrappers for main command entries #
#                                             #
###############################################

@register('0', 'Entry point for Masgent CLI.')
def command_0():
    try:
        while True:
            clear_and_print_banner_and_entry_message()
            choices = [
                '1. Density Functional Theory (DFT) Simulations',
                '2. Fast simulations using machine learning potentials (MLPs)',
                '3. Simple Machine Learning for Materials Science',
                '',
                'AI    ->  Chat with the Masgent AI',
                'New   ->  Start a new session',
                'Help  ->  Show available functions',
                'Exit  ->  Quit the Masgent',
            ]
            cli = Bullet(prompt='\n', choices=choices, margin=1, bullet=' ●', word_color=colors.foreground['green'])
            user_input = cli.launch()
            
            if user_input.startswith('AI'):
                from masgent.ai_mode import ai_backend
                ai_backend.main()
            elif user_input.startswith('New'):
                start_new_session()
            elif user_input.startswith('Help'):
                print_help()
            elif user_input.startswith('Exit'):
                exit_and_cleanup()
            elif user_input.startswith('1'):
                run_command('1')
            elif user_input.startswith('2'):
                run_command('2')
            elif user_input.startswith('3'):
                run_command('3')
            else:
                continue
    
    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

@register('1', 'Density Functional Theory (DFT) Simulations.')
def command_1():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '1.1 Structure Preparation & Manipulation',
                '1.2 VASP Input File Preparation',
                '1.3 Standard VASP Workflow Preparation',
                '1.4 Standard VASP Workflow Output Analysis',
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
        exit_and_cleanup()


@register('1.1', 'Structure Preparation & Manipulation.')
def command_1_1():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '1.1.1 Generate POSCAR from chemical formula',
                '1.1.2 Convert POSCAR coordinates (Direct <-> Cartesian)',
                '1.1.3 Convert structure file formats (CIF, POSCAR, XYZ)',
                '1.1.4 Generate structures with defects (Vacancies, Substitutions, Interstitials)',
                '1.1.5 Generate supercells',
                '1.1.6 Generate Special Quasirandom Structures (SQS)',
                '1.1.7 Generate surface slabs',
                '1.1.8 Generate interface structures',
                '1.1.9 Visualize structure',
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
            elif user_input.startswith('1.1.9'):
                run_command('1.1.9')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

@register('1.2', 'VASP Input File Preparation')
def command_1_2():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '1.2.1 Prepare full VASP input files (INCAR, KPOINTS, POTCAR, POSCAR)',
                '1.2.2 Generate INCAR templates (relaxation, static, etc.)',
                '1.2.3 Gernerate KPOINTS with specified accuracy',
                '1.2.4 Generate HPC job submission script',
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
        exit_and_cleanup()

@register('1.3', 'Standard VASP Workflows.')
def command_1_3():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '1.3.1 Convergence testing (ENCUT, KPOINTS)',
                '1.3.2 Equation of State (EOS)',
                '1.3.3 Elastic constants calculations',
                '1.3.4 Ab-initio Molecular Dynamics (AIMD)',
                '1.3.5 Nudged Elastic Band (NEB) calculations',
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
            elif user_input.startswith('1.3.1'):
                run_command('1.3.1')
            elif user_input.startswith('1.3.2'):
                run_command('1.3.2')
            elif user_input.startswith('1.3.3'):
                run_command('1.3.3')
            elif user_input.startswith('1.3.4'):
                run_command('1.3.4')
            elif user_input.startswith('1.3.5'):
                run_command('1.3.5')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

@register('1.4', 'VASP Output Analysis')
def command_1_4():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '1.4.1 Convergence test analysis',
                '1.4.2 Equation of State (EOS) analysis',
                '1.4.3 Elastic constants analysis',
                '1.4.4 Ab-initio Molecular Dynamics (AIMD) analysis',
                '1.4.5 Nudged Elastic Band (NEB) analysis',
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
            elif user_input.startswith('1.4.1'):
                run_command('1.4.1')
            elif user_input.startswith('1.4.2'):
                run_command('1.4.2')
            elif user_input.startswith('1.4.3'):
                run_command('1.4.3')
            elif user_input.startswith('1.4.4'):
                run_command('1.4.4')
            elif user_input.startswith('1.4.5'):
                run_command('1.4.5')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

@register('2', 'Fast Simulations Using Machine Learning Potentials (MLPs).')
def command_2():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '2.1 SevenNet',
                '2.2 CHGNet',
                '2.3 Orb-v3',
                '2.4 MatterSim',
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
            elif user_input.startswith('2.1'):
                run_command('2.1')
            elif user_input.startswith('2.2'):
                run_command('2.2')
            elif user_input.startswith('2.3'):
                run_command('2.3')
            elif user_input.startswith('2.4'):
                run_command('2.4')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

@register('3', 'Simple Machine Learning for Materials Science.')
def command_3():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '3.1 Dataset Preparation & Visualization',
                '3.2 Model Design & Hyperparameter Tuning',
                '3.3 Model Training & Evaluation',
                '3.4 Pre-trained Model Applications',
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
            elif user_input.startswith('3.1'):
                run_command('3.1')
            elif user_input.startswith('3.2'):
                run_command('3.2')
            elif user_input.startswith('3.3'):
                run_command('3.3')
            elif user_input.startswith('3.4'):
                run_command('3.4')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

@register('3.1', 'Data Preparation & Feature Analysis')
def command_3_1():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '3.1.1 Feature analysis and visualization',
                '3.1.2 Dimensionality reduction (if too many features)',
                '3.1.3 Data augmentation (if limited data)'
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
            elif user_input.startswith('3.1.1'):
                run_command('3.1.1')
            elif user_input.startswith('3.1.2'):
                run_command('3.1.2')
            elif user_input.startswith('3.1.3'):
                run_command('3.1.3')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()

@register('3.4', 'Pre-trained Model Applications')
def command_3_4():
    try:
        while True:
            clear_and_print_entry_message()
            choices = [
                '3.4.1 Mechanical Properties Prediction in Sc-modified Al-Mg-Si Alloys',
                '3.4.2 Phase Stability & Elastic Properties Prediction in Al-Co-Cr-Fe-Ni High-Entropy Alloys',
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
            elif user_input.startswith('3.4.1'):
                run_command('3.4.1')
            elif user_input.startswith('3.4.2'):
                run_command('3.4.2')
            else:
                continue

    except (KeyboardInterrupt, EOFError):
        exit_and_cleanup()