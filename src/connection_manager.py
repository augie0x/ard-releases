import json

from PyQt5.QtCore import QSettings
from src.version import __app_name__

class ConnectionManager:
    def __init__(self):
        self.settings = QSettings(__app_name__, "adjustment_rules_tenants")
        #print(f"Settings file location: {self.settings.fileName()}")

    def save_connection(self, connection_name, credentials):
        connections = self.get_all_connections()
        connections[connection_name] = credentials
        self.settings.setValue('saved_connections', json.dumps(connections))

    def get_connection(self, connection_name):
        connections = self.get_all_connections()
        return connections.get(connection_name)

    def get_all_connections(self):
        connections_str = self.settings.value('saved_connections', '{}')
        return json.loads(connections_str)

    def remove_connection(self, connection_name):
        connections = self.get_connection()
        if connection_name in connections:
            del connections[connection_name]
            self.settings.setValue('saved_connections', json.dumps(connections))

    def connection_exists(self, connection_name):
        connections = self.get_all_connections()
        return connection_name in connections
