import argparse
import sys


from chatai.prompt.prompt import Prompt


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Boogeyman developer CLI"
    )

    # Define the main command parameter
    subparsers = parser.add_subparsers(dest="commands", help="Available commands")

    # Mode 1: 'process'
    process_parser = subparsers.add_parser(
        "show_prompt", help="Show current prompt"
    )
    process_parser.add_argument(
        "--config-path",
        type=str,
        help="Input file or data for processing",
        default="/home/bsharchilev/chatai/chatai/prompt.yaml",
    )
    return parser.parse_args()

def show_prompt(args: argparse.Namespace):
    prompt = Prompt(args.config_path)
    print(prompt.print())

def main():
    args = parse_arguments()

    # Execute the appropriate function based on the command
    if args.command == "show_prompt":
        show_prompt(args)
    else:
        print("Error: No valid command provided.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()