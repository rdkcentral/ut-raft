import websocket

class HDMIController:
    def __init__(self, config):
        self.ws_port = config['ws_port']
        self.supported_commands = config['supported_commands']
        
    def send_command(self, command_data):
        command = command_data.get('command')
        
        if command not in self.supported_commands:
            raise ValueError(f"Unsupported command: {command}")

        # connect to WebSocket & send command
        ws_url = f"ws://localhost:{self.ws_port}"
        ws = websocket.create_connection(ws_url)
        print(f"Sending HDMI command '{command}' to WebSocket at {ws_url}")
        ws.send(command)
        ws.close()
