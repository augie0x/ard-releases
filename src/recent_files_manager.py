# recent_files_manager.py

from PyQt5.QtCore import QSettings
import os
import json
from datetime import datetime

class RecentFilesManager:
    def __init__(self, max_files=10):
        self.settings = QSettings('Augie Inc', 'AdjustmentRuleUpdater')
        self.max_files = max_files


    def add_file(self,filepath):
        if not os.path.exists(filepath):
            return False

        recent_files = self.get_files()

        file_entry={
            'path': filepath,
            'name': os.path.basename(filepath),
            'last_accessed': datetime.now().isoformat(),
            'size': os.path.getsize(filepath)
        }

        recent_files = [f for f in recent_files if f['path'] != filepath]

        recent_files.insert(0, file_entry)

        if len(recent_files) > self.max_files:
            recent_files = recent_files[:self.max_files]

        self.settings.setValue('recent_files', json.dumps(recent_files))
        return True

    def get_files(self):
        try:
            files = json.loads(self.settings.value('recent_files','[]'))
            return [f for f in files if os.path.exists(f['path'])]
        except:
            return []

    def clear_recent_files(self):
        self.settings.setValue('recent_files','[]')