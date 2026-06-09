from app.cli import parse_args


def test_parse_args_consumes_no_tray_and_keeps_qt_args():
    args, qt_argv = parse_args(["flowchem-qt", "--no-tray", "-platform", "offscreen"])

    assert args.no_tray is True
    assert qt_argv == ["flowchem-qt", "-platform", "offscreen"]


def test_parse_args_keeps_qt_args_by_default():
    args, qt_argv = parse_args(["flowchem-qt", "-style", "Fusion"])

    assert args.no_tray is False
    assert qt_argv == ["flowchem-qt", "-style", "Fusion"]
