# src/version_manager.py

import os
import subprocess
import sys
import logging

import requests
from packaging import version
from pathlib import Path


class VersionManager:
    def __init__(self, current_version="1.1.0", repository_url=None):
        """
        Initialize the version manager with the current application version
        and the repository URL where updates are hosted.

        Args:
        current_version (str): The current version of the application
        repository_url (str): The base URL of the repository where updates are hosted
        """

        self.current_version=version.parse(current_version)
        self.repository_url = "https://api.github.com/repos/augie0x/ard-releases"
        self.update_info = None
        self.update_dir = self._initialise_update_directory()

    def _initialise_update_directory(self):

        if sys.platform.startswith('win'):
            # Windows: Use LOCALAPPDATA
            base_dir = os.environ.get('LOCALAPPDATA')
            if not base_dir:
                base_dir = os.path.expanduser('~')
        else:
            # Linux/Mac: Use home directory
            base_dir = os.path.expanduser('~')

            # Create full path for updates directory
        update_dir = Path(base_dir) / ".adjustmentrules" / "updates"

        update_dir.mkdir(parents=True, exist_ok=True)

        self._cleanup_old_installers(update_dir)

        return update_dir


    def _cleanup_old_installers(self, directory):
        """Clean up old installer files"""
        try:
            # Adjust pattern based on platform
            pattern = "*.exe" if sys.platform.startswith('win') else "*"
            installer_files = list(directory.glob(pattern))
            if len(installer_files) > 1:
                installer_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for installer in installer_files[1:]:
                    installer.unlink()
        except Exception as e:
            logging.error(f"Error cleaning up old installers: {str(e)}")

    def check_for_updates(self):
        """
        Check GitHub repository for newer versions of the application.

        Returns:
            tuple: (bool, dict) - (update_available, update_info)
                  update_info contains version, download URL, and release notes
        """
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
            }

            response = requests.get(
                f"{self.repository_url}/releases/latest",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                latest_release = response.json()
                latest_version = version.parse(latest_release['tag_name'].lstrip('v'))

                if latest_version > self.current_version:
                    platform_suffix = '.exe' if sys.platform.startswith('win') else '.deb'
                    matching_assets = [
                        asset for asset in latest_release['assets']
                        if asset['name'].endswith(platform_suffix)
                    ]
                    if matching_assets:
                        self.update_info = {
                            'version': str(latest_version),
                            'download_url': matching_assets[0]['browser_download_url'],
                            'release_notes': latest_release['body'],
                            'publish_date': latest_release['published_at'],
                            'installer_name': matching_assets[0]['name']
                        }
                        return True, self.update_info

                return False, None

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error checking for updates: {str(e)}")
            return False, None

        except Exception as e:
            logging.error(f"Error checking for updates: {str(e)}")
            return False, None

        return False, None

    def download_update(self, progress_callback=None):
        """
        Download the update installer from the respository.

        Args: progress_callback: Optional callback for update progress

        Returns: str: Path to download installer
        """
        if not self.update_info:
            return None

        try:
            update_dir = self._initialize_update_directory()
            installer_path = self.update_dir / f"AdjustmentRuleDemystifier_v{self.update_info['version']}_setup.exe"

            # Download the installer
            response = requests.get(self.update_info['download_url'], stream=True)
            file_size = int(response.headers.get('content-length',0))

            block_size = 8192
            downloaded = 0

            with open(installer_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    if progress_callback:
                        progress=(downloaded/file_size*100) if file_size else 0
                        progress_callback(min(progress,100))

            return str(installer_path)

        except Exception as e:
            logging.error(f"Error downloading update: {str(e)}")
            return None

    def install_update(self, installer_path):
        """
        Start the installation of the update using the Inno Setup installer.
        Args:
            installer_path (str): Path to the downloaded installer
        Returns:
            bool: True if installation was initiated successfully
        """
        try:
            if not os.path.exists(installer_path):
                return False

            # Start installer with Inno Setup silent installation flags
            subprocess.Popen(
                [
                    installer_path,
                    '/SILENT',  # Silent installation
                    '/CLOSEAPPLICATIONS',  # Close the application if running
                    '/RESTARTAPPLICATIONS',  # Restart the application after update
                    '/NOCANCEL'  # Prevent cancellation
                ],
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )

            # Exit the current application to allow the update to proceed
            sys.exit(0)
            return True

        except Exception as e:
            logging.error(f"Error installing update: {str(e)}")
            return False