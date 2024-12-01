import json

from PyQt5.QtCore import QSettings

class ConnectionManager:
    def __init__(self):
        self.settings = QSettings("Adjustment Rules Demystifier", "UKG")

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
