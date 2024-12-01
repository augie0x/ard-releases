# build_complete.py
import os
import shutil
import sys

import PyInstaller.__main__

from src.version import __app_name__, __version__

def ensure_resources():
    """Ensure all required resources exist"""
    # Create resources directories if they don't exist
    os.makedirs('resources/images', exist_ok=True)

    # Check for icon file
    icon_path = os.path.join('resources', 'images', 'ard.ico')
    if not os.path.exists(icon_path):
        print("Warning: Icon file not found. Using default PyInstaller icon.")
        icon_path = None

    return icon_path


def clean_build_directories():
    """Clean build and dist directories"""
    directories = ['build', 'dist']
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)


def copy_dependencies():
    """Copy necessary DLL files to dist directory"""
    qt_bin_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'bin')
    dist_path = os.path.join('dist', 'AdjustmentRuleUpdater')

    if not os.path.exists(dist_path):
        os.makedirs(dist_path)

    required_dlls = [
        'Qt5Core.dll',
        'Qt5Gui.dll',
        'Qt5Widgets.dll',
        'Qt5Svg.dll',
        'Qt5DBus.dll',
        'Qt5Network.dll',
        'Qt5WebSockets.dll',
        'libEGL.dll',
        'libGLESv2.dll',
        'opengl32sw.dll',
        'd3dcompiler_47.dll',
    ]

    for dll in required_dlls:
        dll_path = os.path.join(qt_bin_path, dll)
        if os.path.exists(dll_path):
            shutil.copy2(dll_path, dist_path)


def build_executable():
    """Build the executable using PyInstaller"""
    # Get icon path or None if not found
    icon_path = ensure_resources()

    # Define the command list first
    command = [
        'main.py',
        f'--name={__app_name__.replace(" ", "")}',
        f'--version={__version__}',
        '--onefile',
        '--windowed',
        '--add-data=resources/images;resources/images',
        '--runtime-hook=runtime_hooks.py',
        '--add-binary=venv/Lib/site-packages/PyQt5/Qt5/plugins/platforms;PyQt5/Qt5/plugins/platforms',
        '--add-binary=venv/Lib/site-packages/PyQt5/Qt5/plugins/styles;PyQt5/Qt5/plugins/styles',
        '--add-binary=venv/Lib/site-packages/PyQt5/Qt5/bin;PyQt5/Qt5/bin',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.sip',
        '--hidden-import=PyQt5.QtSvg',
        '--hidden-import=qt_material',
        '--hidden-import=QDarkStyle',
        '--clean',
        '--noconfirm'
    ]

    # Add icon if available
    if icon_path:
        command.insert(4, f'--icon={icon_path}')

    # Run PyInstaller
    PyInstaller.__main__.run(command)


def main():
    """Main build process"""
    print("Cleaning previous build...")
    clean_build_directories()

    print("Building executable...")
    build_executable()

    print("Copying dependencies...")
    copy_dependencies()

    print("Build complete!")


if __name__ == "__main__":
    main()