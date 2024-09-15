#!/bin/bash

# Function to display a message with color
function echo_info {
    echo -e "\e[32m$1\e[0m"
}

# Function to display an error message
function echo_error {
    echo -e "\e[31mERROR: $1\e[0m"
}

# Function to check if an environment variable is set
function check_env_var {
    if [[ -z "${!1}" ]]; then
        echo_error "Environment variable $1 is not set."
        exit 1
    fi
}

# Function to show help information
function show_help {
    echo_info "This script installs the necessary dependencies for running the Telegram bot integrated with OpenAI GPT."
    echo_info "Required environment variables:"
    echo_info "  - OPENAI_API_KEY: Your OpenAI API key"
    echo_info "  - TELEGRAM_BOT_TOKEN: Your Telegram Bot API token"
    echo_info "Usage:"
    echo_info "  ./install_dependencies.sh [--help]"
    echo_info "Options:"
    echo_info "  --help: Show this help message and exit."
    echo_info ""
    echo_info "If you're in a managed Python environment, follow these steps to install dependencies:"
    echo_info "  1. Use a virtual environment:"
    echo_info "      python3 -m venv myenv"
    echo_info "      source myenv/bin/activate"
    echo_info "      pip install python-telegram-bot openai"
    echo_info "  2. If you can't install globally, try using '--user' flag for pip:"
    echo_info "      pip install --user python-telegram-bot openai"
    exit 0
}

# Function to install Python and Pip
function install_python {
    echo_info "Updating system and installing Python and pip..."
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y python3 python3-pip python3-venv
}

# Function to create and activate a virtual environment
function setup_virtualenv {
    echo_info "Do you want to set up a virtual environment to install dependencies? (y/n)"
    read use_venv
    if [ "$use_venv" = "y" ]; then
        echo_info "Setting up a virtual environment..."
        python3 -m venv chatai-env
        source chatai-env/bin/activate
        echo_info "Virtual environment 'chatai-env' activated. You can now install dependencies."
    else
        echo_info "Skipping virtual environment setup."
    fi
}

# Function to install required Python libraries
function install_python_libraries {
    echo_info "Installing required Python libraries..."
    pip install python-telegram-bot openai
    if [ $? -ne 0 ]; then
        echo_error "Error installing dependencies. If you're in a managed environment, consider using a virtual environment."
        echo_info "Instructions:"
        echo_info "  1. Create a virtual environment: python3 -m venv myenv"
        echo_info "  2. Activate it: source myenv/bin/activate"
        echo_info "  3. Install dependencies: pip install python-telegram-bot openai"
        exit 1
    fi
}

# Function to install tmux (optional for keeping bot running)
function install_tmux {
    echo_info "Do you want to install tmux (to keep bot running in the background)? (y/n)"
    read install_tmux
    if [ "$install_tmux" = "y" ]; then
        echo_info "Installing tmux..."
        sudo apt install -y tmux
        echo_info "tmux installed. You can now use tmux to run your bot."
    else
        echo_info "Skipping tmux installation."
    fi
}

# Function to validate environment variables
function validate_env_variables {
    echo_info "Validating environment variables..."
    check_env_var "OPENAI_API_KEY"
    check_env_var "TELEGRAM_BOT_TOKEN"
    echo_info "All required environment variables are set."
}

# Main function
function main {
    # Check for --help flag
    if [[ "$1" == "--help" ]]; then
        show_help
    fi

    # Validate environment variables
    validate_env_variables

    # Install Python, libraries, and optional components
    install_python
    setup_virtualenv
    install_python_libraries
    install_tmux

    echo_info "All dependencies have been installed successfully!"
    echo_info "You can now run your Telegram bot or any other scripts on this VM."
}

# Run the main function with arguments
main "$@"
