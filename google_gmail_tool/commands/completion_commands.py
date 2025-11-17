"""Shell completion commands for google-gmail-tool.

This module provides shell completion generation commands following the
industry-standard pattern (e.g., kubectl completion, helm completion).

Supports:
- Bash (≥4.4)
- Zsh
- Fish

Design:
- User-friendly `google-gmail-tool completion <shell>` interface
- Self-documenting help with installation instructions
- Uses Click's internal ShellComplete classes for proper integration

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import click
from click.shell_completion import BashComplete, FishComplete, ZshComplete


@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell: str) -> None:
    """Generate shell completion script.

    Install shell completion to enable tab completion for all commands,
    options, and arguments in google-gmail-tool.

    SHELL: The shell type (bash, zsh, fish)

    Examples:

    \b
        # Show this help
        google-gmail-tool completion --help

    \b
        # Generate bash completion script
        google-gmail-tool completion bash

    \b
        # Generate zsh completion script
        google-gmail-tool completion zsh

    \b
        # Generate fish completion script
        google-gmail-tool completion fish

    \b
    Installation Instructions:

    \b
    Bash (add to ~/.bashrc or ~/.bash_profile):
        eval "$(google-gmail-tool completion bash)"

    \b
    Zsh (add to ~/.zshrc):
        eval "$(google-gmail-tool completion zsh)"

    \b
    Fish (save to completions directory):
        google-gmail-tool completion fish > ~/.config/fish/completions/google-gmail-tool.fish

    \b
    For better performance, save to a file instead of running on every shell start:

    \b
        # Bash - generate once, source from file
        google-gmail-tool completion bash > ~/.google-gmail-tool-complete.bash
        echo 'source ~/.google-gmail-tool-complete.bash' >> ~/.bashrc

    \b
        # Zsh - generate once, source from file
        google-gmail-tool completion zsh > ~/.google-gmail-tool-complete.zsh
        echo 'source ~/.google-gmail-tool-complete.zsh' >> ~/.zshrc

    \b
        # Fish - automatically loads from completions directory
        google-gmail-tool completion fish > ~/.config/fish/completions/google-gmail-tool.fish

    \b
    After installation, restart your shell or source your shell configuration:
        source ~/.bashrc    # Bash
        source ~/.zshrc     # Zsh
        # Fish loads automatically
    """
    ctx = click.get_current_context()

    # Get the appropriate completion class for the specified shell
    completion_classes = {
        "bash": BashComplete,
        "zsh": ZshComplete,
        "fish": FishComplete,
    }

    completion_class = completion_classes.get(shell)
    if completion_class:
        completer = completion_class(
            cli=ctx.find_root().command,
            ctx_args={},
            prog_name="google-gmail-tool",
            complete_var="_GOOGLE_GMAIL_TOOL_COMPLETE",
        )
        click.echo(completer.source())
    else:
        raise click.BadParameter(f"Unsupported shell: {shell}")
