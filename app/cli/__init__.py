import click


@click.group()
def main():
    """
    Entrypoint for CLI
    """


@main.command
def hello():
    click.echo("Hello, World!")


# Add the hello command as a subcommand of main
main.add_command(hello)

if __name__ == "__main__":
    main()
