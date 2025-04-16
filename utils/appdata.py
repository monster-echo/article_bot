import os
import json
from pathlib import Path


class AppData:
    """Utility class to manage application data stored in app_data directory"""

    def __init__(self, base_dir=None):
        """
        Initialize the AppData utility.

        Args:
            base_dir (str, optional): The base directory where app_data will be created.
                                     If None, the project root directory will be used.
        """
        if base_dir is None:
            # Get the project root directory (where the current file is located)
            self.base_dir = Path(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        else:
            self.base_dir = Path(base_dir)

        # Define the app_data directory path
        self.app_data_dir = self.base_dir / "app_data"

        # Ensure the app_data directory exists
        self.ensure_app_data_dir()

    def ensure_app_data_dir(self):
        """Create the app_data directory if it doesn't exist."""
        if not self.app_data_dir.exists():
            self.app_data_dir.mkdir(exist_ok=True)
            print(f"Created app_data directory at: {self.app_data_dir}")

    def get_file_path(self, filename):
        """
        Get the full path to a file in the app_data directory.

        Args:
            filename (str): The name of subdirectory and file.

        Returns:
            Path: The full path to the file
        """
        path = self.app_data_dir / filename
        # get directory of the file
        file_dir = path.parent
        # create directory if it doesn't exist
        if not file_dir.exists():
            file_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory at: {file_dir}")
        return path


# Create a singleton instance
app_data = AppData()
