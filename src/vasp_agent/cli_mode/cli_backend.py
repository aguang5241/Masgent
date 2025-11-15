import sys
import vasp_agent.cli_mode.cli_tools as cli_tools

def print_help():
    print('\nVASP-Agent CLI usage:')
    print('  Type one of the following commands:\n')
    print('Available commands:')
    print('  hello              → Print a hello message')
    print('  goodbye            → Print a goodbye message\n')
    print('  ai                 → Switch to AI mode')
    print('  help               → Show this help message')
    print('  exit               → Exit the program\n')

def main():
    commands = {
        'hello': cli_tools.say_hello,
        'goodbye': cli_tools.say_goodbye,
    }

    try:
        while True:
            user_input = input('VASP-Agent CLI > ').strip().lower()

            if not user_input:
                continue

            if user_input in {'exit'}:
                return 'exit-mode'
            elif user_input in {'ai'}:
                return 'ai-mode'
            elif user_input in {'help'}:
                print_help()
            elif user_input in commands:
                commands[user_input]()
            else:
                print(f'Unknown command: {user_input}')
                print('Type "help" to see available commands.\n')

    except (KeyboardInterrupt, EOFError):
        print('\nExiting VASP-Agent. Goodbye!\n')
        sys.exit(0)

if __name__ == '__main__':
    main()