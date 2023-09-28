__author__ = "Beck Isakov"
__copyright__ = "Beck isakov"
__credits__ = "Martin Huus Bjerge"
__contact__ = "https://github.com/Jp-Beck"
__license__ = "GPL v3"
__version__ = "0.2.0"
__maintainer__ = "Beck Isakov"
__email__ = "jp-beck@outlook.com"
__status__ = "Development"


# Import Modules
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
from openur.dashboard import Dashboard
from openur.rtde_command import RTDECommands
from openur.urscript import URClient


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Main class
class OpenUR:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.tree = ET.parse('rtde_configuration.xml')
        self.root = self.tree.getroot()
        self.recipe_rco = self.root.find(".//recipe[@key='rco']")
        self.recipe_rci = self.root.find(".//recipe[@key='rci']")
        self.rtde_cmd = RTDECommands(host=ip_address, recipe_setp="rci", recipe_out="rco")
        self.rtde_cmd.connect()
        self.dashboard = Dashboard(ip_address)
        self.dashboard.connect()
        self.ur_client = URClient(ip_address)
        self.ur_client.connect()
    
    def close(self):
        self.rtde_cmd.close()
        self.dashboard.close()
        self.ur_client.close()
    
    def _write_pretty_xml(self, filename):
        xml_string = ET.tostring(self.root).decode()
        # Remove all whitespace between tags
        xml_string = ''.join(line.strip() for line in xml_string.splitlines())
        # Pretty print XML with minidom
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="\t", encoding=None, newl='\n')
        with open(filename, 'w') as f:
            # Remove the first line which is the XML declaration
            f.write(pretty_xml.split('\n', 1)[1])
    
    def _add_rco_field_to_xml(self, name, type, value=None):
        if self.recipe_rco.find(".//field[@name='" + name + "']") is None:
            new_field = ET.Element('field', {'name': name, 'type': type})
            if value:
                new_field.text = str(value)
            self.recipe_rco.append(new_field)
            self._write_pretty_xml('rtde_configuration.xml')
    
    def _add_rci_field_to_xml(self, name, type, value=None):
        if self.recipe_rci.find(".//field[@name='" + name + "']") is None:
            new_field = ET.Element('field', {'name': name, 'type': type})
            if value:
                new_field.text = str(value)
            self.recipe_rci.append(new_field)
            self._write_pretty_xml('rtde_configuration.xml')


    
    # Dashbaoard Methods
    def is_in_remote(self):
        return self.dashboard.is_in_remote()
    
    def load_program(self, program):
        return self.dashboard.load_program(program)

    def play(self):
        return self.dashboard.play()
    
    def pause(self):
        return self.dashboard.pause()
    
    def stop(self):
        return self.dashboard.stop()
    
    def quit(self):
        return self.dashboard.quit()
    
    def shutdown(self):
        return self.dashboard.shutdown()
    
    def running(self):
        return self.dashboard.running()

    def robotmode(self):
        return self.dashboard.robotmode()
    
    def get_loaded_program(self):
        return self.dashboard.get_loaded_program()
    
    def popup(self, message):
        return self.dashboard.popup(message)
    
    def close_popup(self):
        return self.dashboard.close_popup()
    
    def add_to_log(self, message):
        return self.dashboard.add_to_log(message)
    
    def is_program_saved(self):
        return self.dashboard.is_program_saved()
    
    def program_state(self):
        return self.dashboard.program_state()
    
    def polyscope_version(self):
        return self.dashboard.polyscope_version()
    
    def market_version(self):
        return self.dashboard.marketing_version()
    
    def set_operational_mode(self, mode):
        return self.dashboard.set_operational_mode(mode)

    def get_operational_mode(self):
        return self.dashboard.get_operational_mode()
    
    def clear_operational_mode(self):
        return self.dashboard.clear_operational_mode()
    
    def power_on(self):
        return self.dashboard.power_on()

    def power_off(self):
        return self.dashboard.power_off()
    
    def brake_release(self):
        return self.dashboard.brake_release()
    
    def safety_status(self):
        return self.dashboard.safety_status()
    
    def unlock_protective_stop(self):
        return self.dashboard.unlock_protective_stop()
    
    def close_safety_popup(self):
        return self.dashboard.close_safety_popup()
    
    def load_installation(self, installation):
        return self.dashboard.load_installation(installation)
    
    def restart_safety(self):
        return self.dashboard.restart_safety()
    
    def get_serial_number(self):
        return self.dashboard.get_serial_number()
    
    def get_robot_model(self):
        return self.dashboard.get_robot_model()
    
    def generate_flight_report(self):
        return self.dashboard.generate_flight_report() 
    
    def transfer_files(self, files):
        return self.dashboard.transfer_files(files)
    
    def generate_support_file(self):
        return self.dashboard.generate_support_file()

    # Real Time Data Exchange Methods

    ## Robot Controller Outputs
    
    def timestamp(self):
        self._add_rco_field_to_xml('timestamp', 'DOUBLE')
        return self.rtde_cmd.timestamp()

    def target_q(self):
        self._add_rco_field_to_xml('target_q', 'VECTOR6D')
        return self.rtde_cmd.target_q()
    
    def target_qd(self):
        self._add_rco_field_to_xml('target_qd', 'VECTOR6D')
        return self.rtde_cmd.target_qd()
    
    def target_qdd(self):
        self._add_rco_field_to_xml('target_qdd', 'VECTOR6D')
        return self.rtde_cmd.target_qdd()
    
    def target_current(self):
        self._add_rco_field_to_xml('target_current', 'VECTOR6D')
        return self.rtde_cmd.target_current()
    
    def target_moment(self):
        self._add_rco_field_to_xml('target_moment', 'VECTOR6D')
        return self.rtde_cmd.target_moment()
    
    def actual_q(self):
        self._add_rco_field_to_xml('actual_q', 'VECTOR6D')
        return self.rtde_cmd.actual_q()
    
    def actual_qd(self):
        self._add_rco_field_to_xml('actual_qd', 'VECTOR6D')
        return self.rtde_cmd.actual_qd()
    
    def actual_current(self):
        self._add_rco_field_to_xml('actual_current', 'VECTOR6D')
        return self.rtde_cmd.actual_current()
    
    def joint_control_output(self):
        self._add_rco_field_to_xml('joint_control_output', 'VECTOR6D')
        return self.rtde_cmd.joint_control_output()
    
    def actual_TCP_pose(self):
        self._add_rco_field_to_xml('actual_TCP_pose', 'VECTOR6D')
        return self.rtde_cmd.actual_TCP_pose()
    
    def actual_TCP_speed(self):
        self._add_rco_field_to_xml('actual_TCP_speed', 'VECTOR6D')
        return self.rtde_cmd.actual_TCP_speed()
    
    def actual_TCP_force(self):
        self._add_rco_field_to_xml('actual_TCP_force', 'VECTOR6D')
        return self.rtde_cmd.actual_TCP_force()
    
    def actual_digital_input_bits(self):
        self._add_rco_field_to_xml('actual_digital_input_bits', 'UINT64')
        return self.rtde_cmd.actual_digital_input_bits()
    
    def joint_temperatures(self):
        self._add_rco_field_to_xml('joint_temperatures', 'VECTOR6D')
        return self.rtde_cmd.joint_temperatures()
    
    def actual_execution_time(self):
        self._add_rco_field_to_xml('actual_execution_time', 'DOUBLE')
        return self.rtde_cmd.actual_execution_time()
    
    def robot_mode(self):
        self._add_rco_field_to_xml('robot_mode', 'INT32')
        return self.rtde_cmd.robot_mode()

    def joint_mode(self):
        self._add_rco_field_to_xml('joint_mode', 'VECTOR6INT32')
        return self.rtde_cmd.joint_mode()

    def safety_mode(self):
        self._add_rco_field_to_xml('safety_mode', 'INT32')
        return self.rtde_cmd.safety_mode()
    
    def safety_status(self):
        self._add_rco_field_to_xml('safety_status', 'INT32')
        return self.rtde_cmd.safety_status()

    def actual_tool_accelerometer(self):
        self._add_rco_field_to_xml('actual_tool_accelerometer', 'VECTOR3D')
        return self.rtde_cmd.actual_tool_accelerometer()
    
    def speed_scaling(self):
        self._add_rco_field_to_xml('speed_scaling', 'DOUBLE')
        return self.rtde_cmd.speed_scaling()
    
    def target_speed_fraction(self):
        self._add_rco_field_to_xml('target_speed_fraction', 'DOUBLE')
        return self.rtde_cmd.target_speed_fraction()
    
    def actual_momentum(self):
        self._add_rco_field_to_xml('actual_momentum', 'DOUBLE')
        return self.rtde_cmd.actual_momentum()
    
    def actual_main_voltage(self):
        self._add_rco_field_to_xml('actual_main_voltage', 'DOUBLE')
        return self.rtde_cmd.actual_main_voltage()
    
    def actual_robot_voltage(self):
        self._add_rco_field_to_xml('actual_robot_voltage', 'DOUBLE')
        return self.rtde_cmd.actual_robot_voltage()
    
    def actual_robot_current(self):
        self._add_rco_field_to_xml('actual_robot_current', 'DOUBLE')
        return self.rtde_cmd.actual_robot_current()

    def actual_joint_voltage(self):
        self._add_rco_field_to_xml('actual_joint_voltage', 'VECTOR6D')
        return self.rtde_cmd.actual_joint_voltage()

    def runtime_state(self):
        self._add_rco_field_to_xml('runtime_state', 'UINT32')
        return self.rtde_cmd.runtime_state()

    def elbow_position(self):
        self._add_rco_field_to_xml('elbow_position', 'VECTOR3D')
        return self.rtde_cmd.elbow_position()

    def elbow_velocity(self):
        self._add_rco_field_to_xml('elbow_velocity', 'VECTOR3D')
        return self.rtde_cmd.elbow_velocity()

    def safety_status_bits(self):
        self._add_rco_field_to_xml('safety_status_bits', 'UINT32')
        return self.rtde_cmd.safety_status_bits()
    
    def robot_status_bits(self):
        self._add_rco_field_to_xml('robot_status_bits', 'UINT32')
        return self.rtde_cmd.robot_status_bits()

    def analog_io_types(self):
        self._add_rco_field_to_xml('analog_io_types', 'UINT32')
        return self.rtde_cmd.analog_io_types()
        
    def standard_analog_input(self, number):
        number = 1 if number > 0 else 0
        self._add_rco_field_to_xml('standard_analog_input' + str(number), 'DOUBLE')
        return self.rtde_cmd.standard_analog_input(number)
        
    def io_current(self):
        self._add_rco_field_to_xml('io_current', 'DOUBLE')
        return self.rtde_cmd.io_current()

    
    def euromap67_input_bits(self):
        self._add_rco_field_to_xml('euromap67_input_bits', 'UINT32')
        return self.rtde_cmd.euromap67_input_bits()

    def euromap67_output_bits(self):
        self._add_rco_field_to_xml('euromap67_output_bits', 'UINT32')
        return self.rtde_cmd.euromap67_output_bits()

    def euromap67_24V_voltage(self):
        self._add_rco_field_to_xml('euromap67_24V_voltage', 'DOUBLE')
        return self.rtde_cmd.euromap67_24V_voltage()
    
    def euromap67_24V_current(self):
        self._add_rco_field_to_xml('euromap67_24V_current', 'DOUBLE')
        return self.rtde_cmd.euromap67_24V_current()
    
    def tool_mode(self):
        self._add_rco_field_to_xml('tool_mode', 'UINT32')
        return self.rtde_cmd.tool_mode()
    
    def tool_analog_input_types(self):
        self._add_rco_field_to_xml('tool_analog_input_types', 'UINT32')
        return self.rtde_cmd.tool_analog_input_types()
    
    def tool_analog_input(self, number):
        number = 1 if number > 0 else 0
        self._add_rco_field_to_xml('tool_analog_input' + str(number), 'DOUBLE')
        return self.rtde_cmd.tool_analog_input(number)
    
    def tool_output_voltage(self):
        self._add_rco_field_to_xml('tool_output_voltage', 'INT32')
        return self.rtde_cmd.tool_output_voltage()
    
    def tool_output_current(self):
        self._add_rco_field_to_xml('tool_output_current', 'DOUBLE')
        return self.rtde_cmd.tool_output_current()
    
    def tool_temperature(self):
        self._add_rco_field_to_xml('tool_temperature', 'DOUBLE')
        return self.rtde_cmd.tool_temperature()
    
    def tcp_force_scalar(self):
        self._add_rco_field_to_xml('tcp_force_scalar', 'DOUBLE')
        return self.rtde_cmd.tcp_force_scalar()
    
    def output_bit_registers(self):
        self._add_rco_field_to_xml('output_bit_registers', 'UINT32')
        return self.rtde_cmd.output_bit_registers()

    def output_bit_registers0_to_31(self):
        self._add_rco_field_to_xml('output_bit_registers0_to_31', 'UINT32')
        return self.rtde_cmd.output_bit_registers0_to_31()
    
    def output_bit_registers32_to_63(self):
        self._add_rco_field_to_xml('output_bit_registers32_to_63', 'UINT32')
        return self.rtde_cmd.output_bit_registers32_to_63()
    
    def output_bit_register_x(self, number):
        self._add_rco_field_to_xml('output_bit_register_' + str(number), 'BOOL')
        return self.rtde_cmd.output_bit_register_x(number)
    
    def output_int_register_x(self, number):
        self._add_rco_field_to_xml('output_int_register_' + str(number), 'BOOL')
        return self.rtde_cmd.output_int_register_x(number)

    def output_double_register_x(self, number):
        self._add_rco_field_to_xml('output_double_register_' + str(number), 'DOUBLE')
        return self.rtde_cmd.output_double_register_x(number)
    
    def tool_output_mode(self):
        self._add_rco_field_to_xml('tool_output_mode', 'UINT8')
        return self.rtde_cmd.tool_output_mode()

    def tool_digital_outputX_mode(self, X):
        self._add_rco_field_to_xml('tool_digital_output' + str(X) + '_mode', 'UINT8')
        return self.rtde_cmd.tool_digital_outputX_mode(X)

    def payload(self):
        self._add_rco_field_to_xml('payload', 'DOUBLE')
        return self.rtde_cmd.payload()

    def payload_cog(self):
        self._add_rco_field_to_xml('payload_cog', 'VECTOR3D')
        return self.rtde_cmd.payload_cog()
    
    def payload_inertia(self):
        self._add_rco_field_to_xml('payload_inertia', 'DOUBLE')
        return self.rtde_cmd.payload_inertia()
    
    def script_control_line(self):
        self._add_rco_field_to_xml('script_control_line', 'UINT32')
        return self.rtde_cmd.script_control_line()
    
    def ft_raw_wrench(self):
        self._add_rco_field_to_xml('ft_raw_wrench', 'VECTOR6D')
        return self.rtde_cmd.ft_raw_wrench()
    
    def actual_digital_input_bits(self):
        self._add_rco_field_to_xml('actual_digital_input_bits', 'UINT64')
        return self.rtde_cmd.actual_digital_input_bits()
    
    def read_standard_digital_inputs(self, number):
        self._add_rco_field_to_xml('actual_digital_input_bits' + str(number), 'UINT64')
        return self.rtde_cmd.read_standard_digital_inputs(number)
    
    def read_standard_digital_inputs_true(self):
        self._add_rco_field_to_xml('actual_digital_input_bits', 'UINT64')
        return self.rtde_cmd.read_standard_digital_inputs_true()
    
    def read_standard_digital_inputs_false(self):
        self._add_rco_field_to_xml('actual_digital_input_bits', 'UINT64')
        return self.rtde_cmd.read_standard_digital_inputs_false()

    def read_configurable_digital_inputs(self, number):
        self._add_rco_field_to_xml('actual_digital_input_bits', 'UINT64')
        return self.rtde_cmd.read_configurable_digital_inputs(number)
    
    def tool_digital_inputs(self, number):
        self._add_rco_field_to_xml('actual_digital_input_bits', 'UINT64')
        return self.rtde_cmd.tool_digital_inputs(number)
    
    def actual_digital_output_bits(self):
        self._add_rco_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.actual_digital_output_bits()
    
    def read_tool_digital_outputs(self,number):
        self._add_rco_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.read_tool_digital_outputs(number)
    
    def read_tool_digital_outputs_true(self):
        self._add_rco_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.read_tool_digital_outputs_true()
    
    def read_tool_digital_outputs_false(self):
        self._add_rco_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.read_tool_digital_outputs_false()
    
    ## Robot Controller Inputs

    def speed_slider_mask(self):
        self._add_rci_field_to_xml('speed_slider_mask', 'UINT32')
        return self.rtde_cmd.speed_slider_mask()
    
    def speed_slider_fraction(self):
        self._add_rci_field_to_xml('speed_slider_fraction', 'DOUBLE')
        return self.rtde_cmd.speed_slider_fraction()
    
    def standard_digital_output_mask(self, number):
        self._add_rci_field_to_xml('standard_digital_output_mask', 'UINT8')
        return self.rtde_cmd.standard_digital_output_mask(number)
    
    def configurable_digital_output_mask(self):
        self._add_rci_field_to_xml('configurable_digital_output_mask', 'UINT8')
        return self.rtde_cmd.configurable_digital_output_mask()

    def read_standard_digital_output(self,number):
        self._add_rco_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.read_standard_digital_output(number)
    
    def read_standard_digital_output_true(self):
        self._add_rci_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.read_standard_digital_output_true()
    
    def read_standard_digital_output_false(self):
        self._add_rci_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.read_standard_digital_output_false()
    
    def read_configurable_digital_output(self):
        self._add_rci_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.read_configurable_digital_output()
    
    def read_configurable_digital_output_true(self):
        self._add_rci_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.read_configurable_digital_output_true()
    
    def read_configurable_digital_output_false(self):
        self._add_rci_field_to_xml('actual_digital_output_bits', 'UINT64')
        return self.rtde_cmd.read_configurable_digital_output_false()
    
    def standard_analog_output_mask(self):
        self._add_rci_field_to_xml('standard_analog_output_mask', 'UINT8')
        return self.rtde_cmd.standard_analog_output_mask()
    
    def standard_analog_output_type(self):
        self._add_rci_field_to_xml('standard_analog_output_type', 'UINT8')
        return self.rtde_cmd.standard_analog_output_type()
    
    def standard_analog_output(self, number):
        number = 1 if number > 0 else 0
        self._add_rci_field_to_xml('standard_analog_output_' + str(number), 'DOUBLE')
        return self.rtde_cmd.standard_analog_output(number)
    
    def input_bit_registers(self):
        self._add_rci_field_to_xml('input_bit_registers0_to_31', 'UINT32')
        self._add_rci_field_to_xml('input_bit_registers32_to_63', 'UINT32')
        return self.rtde_cmd.input_bit_registers()
    
    def input_bit_register_x(self, number):
        self._add_rci_field_to_xml('input_bit_register_' + str(number), 'BOOL')
        return self.rtde_cmd.input_bit_registers_x(number)
    
    def input_int_register_X(self, number):
        self._add_rci_field_to_xml('input_int_register_' + str(number), 'INT32')
        return self.rtde_cmd.input_int_register_x(number)
    
    def input_double_register_x(self, number):
        self._add_rci_field_to_xml('input_double_register_' + str(number), 'DOUBLE')
        return self.rtde_cmd.input_double_register_x(number)

    def set_standard_digital_output(self, number, value):
        self._add_rci_field_to_xml('standard_digital_output_mask', 'UINT8')
        self._add_rci_field_to_xml('standard_digital_output', 'UINT8')
        return self.rtde_cmd.set_standard_digital_output(number, value)

    ## URClient Methods
    def stop_command(self):
        return self.ur_client.stop_command()
    
    def send_script(self, script):
        return self.ur_client.send_script(script)

    def send_raw_program(self, program):
        return self.ur_client.send_raw_program(program)
    
    def send_txt_program(self, program):
        return self.ur_client.send_txt_program(program)

    def movej(self, joints, a=1.2, v=0.25):
        return self.ur_client.movej(joints, a, v)
    
    def get_actual_joint_positions(self):
        return self.ur_client.get_actual_joint_positions()

    def set_tcp(self, pose):
        return self.ur_client.set_tcp(pose)
    
    def force_mode(self, task_frame, selection_vector, wrench, f_type, limits):
        return self.ur_client.force_mode(task_frame, selection_vector, wrench, f_type, limits)

