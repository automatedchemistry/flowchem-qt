import argparse


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Disable the system tray; closing the window exits the application.",
    )
    args, qt_args = parser.parse_known_args(argv[1:])
    return args, [argv[0], *qt_args]
