
from importlib.metadata import version, PackageNotFoundError

def print_title():
    '''Print the VASP-Agent ASCII banner and metadata inside a box.'''

    # Retrieve installed version
    try:
        pkg_version = version('vasp-agent')
    except PackageNotFoundError:
        pkg_version = 'dev'

    # ASCII banner
    ascii_banner = rf'''
+-------------------------------------------------------------------------------------+
|                                                                                     |
|  ██╗   ██╗ █████╗ ███████╗██████╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗  |
|  ██║   ██║██╔══██╗██╔════╝██╔══██╗    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝  |
|  ██║   ██║███████║███████╗██████╔╝    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║     |
|  ╚██╗ ██╔╝██╔══██║╚════██║██╔═══╝     ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║     |
|   ╚████╔╝ ██║  ██║███████║██║         ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║     |
|    ╚═══╝  ╚═╝  ╚═╝╚══════╝╚═╝         ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝     |
|                                                          (c) 2025 Guangchen Liu     |
|  Version:         {pkg_version:<64}  |
|  Licensed:        MIT License                                                       |
|  Repository:      https://github.com/aguang5241/VASP-Agent                          |
|  Citation:        Liu, G. et al. (2025), DOI:10.XXXX/XXXXX'                         |
|  Contact:         gliu4@wpi.edu                                                     |
|                                                                                     |
+-------------------------------------------------------------------------------------+
    '''
    print(ascii_banner)