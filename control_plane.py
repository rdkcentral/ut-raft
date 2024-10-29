import yaml
from configRead import ConfigRead
from submodules.ir_blaster import IRBlasterController
from submodules.hdmi_controller import HDMIController

class ControlPlane:
    def __init__(self, config_path='config.yaml'):
        self.config = ConfigRead(config_path)
        
    def process_message(self, message_yaml):
        # parse yaml message
        message = yaml.safe_load(message_yaml)
        device_type = list(message.keys())[0]
        
        # get device type from config
        device_config = self.config.get(f'control_devices.{device_type}')
        
        if device_config['type'] == 'physical':
            if device_type == 'irblaster':
                controller = IRBlasterController(device_config)
                controller.send_command(message[device_type])
        
        elif device_config['type'] == 'virtual':
            if device_type == 'hdmicec':
                controller = HDMIController(device_config)
                controller.send_command(message[device_type])
