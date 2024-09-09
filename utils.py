#!/usr/bin/env python3
import os


def get_current_module_path():
    """Get the path of the current module."""
    # pylint: disable=C0415
    try:
        import __main__ as current_module

        path = os.path.dirname(current_module.__file__)
        del current_module
        return path
    except AttributeError:
        # If the current module is __main__ then the attribute
        #    __file__ does not exist.
        return os.getcwd()
