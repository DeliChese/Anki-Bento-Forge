"""Keyboard-focus and accessible-name helpers for the factory dialog."""


def configure_keyboard_navigation(dialog, controls, *, description, focus_policy=None):
    """Apply a deterministic Tab order without requiring a Qt import.

    ``controls`` is an ordered iterable of ``(widget, accessible_name)``.  The
    helper is deliberately tolerant of older Anki/Qt widgets that may not
    expose every accessibility method.
    """
    previous = None
    for widget, accessible_name in controls:
        if widget is None:
            continue
        try:
            widget.setAccessibleName(accessible_name)
            widget.setAccessibleDescription(description)
            if focus_policy is not None:
                widget.setFocusPolicy(focus_policy)
        except Exception:
            pass
        if previous is not None:
            try:
                dialog.setTabOrder(previous, widget)
            except Exception:
                pass
        previous = widget
