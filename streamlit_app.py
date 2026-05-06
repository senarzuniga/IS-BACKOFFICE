"""IS-BACKOFFICE Streamlit entrypoint."""

from __future__ import annotations


def _resolve_main():
    """Resolve a callable UI entrypoint with safe fallbacks."""
    try:
        from backoffice.ui import command_center

        if hasattr(command_center, "main") and callable(command_center.main):
            return command_center.main

        if hasattr(command_center, "CommandCenter"):
            return lambda: command_center.CommandCenter().run()
    except Exception:
        pass

    # Fallback to legacy dashboard if the command center import fails.
    from backoffice.ui.app import main as legacy_main

    return legacy_main


if __name__ == "__main__":
    _resolve_main()()
