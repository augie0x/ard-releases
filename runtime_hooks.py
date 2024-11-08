# runtime_hooks.py
import sys
import os

# This hook script is executed during the startup of the frozen application.
def setup_environment():
    """Setup environment paths for PyQt5 and resources"""
    if getattr(sys, 'frozen', False):
        # Running in a bundle
        bundle_dir = sys._MEIPASS

        # Set the RESOURCEPATH environment variable to the resources directory in the bundle
        resource_path = os.path.join(bundle_dir, 'resources')
        if os.path.exists(resource_path):
            os.environ['RESOURCEPATH'] = resource_path
            print(f"RESOURCEPATH set to: {resource_path}")
        else:
            print(f"Warning: RESOURCEPATH not found at {resource_path}")

        # Set the QT_PLUGIN_PATH environment variable to the PyQt5 plugins directory in the bundle
        qt_plugin_path = os.path.join(bundle_dir, 'PyQt5', 'Qt5', 'plugins')
        if os.path.exists(qt_plugin_path):
            os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
            print(f"QT_PLUGIN_PATH set to: {qt_plugin_path}")
        else:
            print(f"Warning: QT_PLUGIN_PATH not found at {qt_plugin_path}")
    else:
        # Running in a normal Python environment, usually during development
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

        # Set RESOURCEPATH to the local resources directory
        resource_path = os.path.join(bundle_dir, 'resources')
        if os.path.exists(resource_path):
            os.environ['RESOURCEPATH'] = resource_path
            print(f"RESOURCEPATH set to: {resource_path}")
        else:
            print(f"Warning: RESOURCEPATH not found at {resource_path}")

# Call the function to set up the environment variables
setup_environment()
