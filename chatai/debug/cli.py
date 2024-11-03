import argparse
import sys
import paramiko
from scp import SCPClient


from chatai.prompt.prompt import Prompt


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Boogeyman developer CLI"
    )

    # Define the main command parameter
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    process_parser = subparsers.add_parser(
        "show_prompt", help="Show current prompt"
    )
    process_parser.add_argument(
        "--config-path",
        type=str,
        help="Input file or data for processing",
        default="/home/bsharchilev/chatai/chatai/prompt.yaml",
    )

    copy_prompt_parser = subparsers.add_parser(
        "copy_prompt", help="Copy prompt config to/from local machine or server"
    )
    copy_prompt_parser.add_argument(
        "--local-path",
        type=str,
        help="local path for prompt",
        default="/Users/sharch/code/chatai/chatai/prompt.yaml",
    )
    copy_prompt_parser.add_argument(
        "--remote-path",
        type=str,
        help="remote path for prompt",
        default="/home/bsharchilev/chatai/chatai/prompt.yaml",
    )
    copy_prompt_parser.add_argument(
        "--upload",
        action="store_true",
        help="By default, download file from server; if this is set to true, upload file to server",
    )
    copy_prompt_parser.add_argument(
        "--ip",
        type=str,
        help="Server ip",
        default="35.214.126.200",
    )

    return parser.parse_args()

def show_prompt(args: argparse.Namespace):
    prompt = Prompt(args.config_path)
    print(prompt.print())

def copy_prompt(args: argparse.Namespace):
    ssh = _create_ssh_client(args.ip, 22)
    with SCPClient(ssh.get_transport()) as scp:
        if args.upload:
            scp.put(args.local_path, args.remote_path)
        else:
            scp.get(args.remote_path, args.local_path)
    ssh.close()

def _create_ssh_client(hostname: str, port: int) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port=port, username="bsharchilev", key_filename="/Users/sharch/.ssh/work_mac_key")
    return ssh

def main():
    args = parse_arguments()

    # Execute the appropriate function based on the command
    if args.command == "show_prompt":
        show_prompt(args)
    if args.command == "copy_prompt":
        copy_prompt(args)
    else:
        print("Error: No valid command provided.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()