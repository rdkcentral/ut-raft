
class IRBlasterController:
    
    def __init__(self, config):
        self.command_port = config['command_port']
        self.supported_commands = config['supported_commands']

    def send_command(self, command_data):
        command = command_data.get('command')
        
        if command not in self.supported_commands:
            raise ValueError(f"Unsupported command: {command}")

        # simulate sending command to IR Blaster
        print(f"Sending IR command '{command}' to port {self.command_port}")
        # code for actual command sending added after this
