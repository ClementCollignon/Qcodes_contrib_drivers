# OxfordInstruments_Kelvinox_IGH class, to perform the communication between the Wrapper and the device

# Clement Collignon <clement.collignon.0@gmail.com>, 2024

from qcodes.instrument import VisaInstrument
from qcodes import validators as vals
import logging

log = logging.getLogger(__name__)

"""
TO DO:
    • Add descriptions to class and methods
    • Test the code with our Mercury
    • Add 'luxury' functions to flow control (sweep, heater mode etc)
"""

class MercuryiTC(VisaInstrument):
    """
    Driver for Oxford Instrument Mercury ientelligent Temperature Controller

    name
    address
    board_mapping
    status_mapping
    """
    def __init__(self, name: str, address: str, **kwargs):
        log.debug('Initializing instrument')
        super().__init__(name, address, **kwargs)
        self._address = address
        self.board_mapping = {"VTI" : "MB1",
                               "VTI_heater" : "MB0",
                               "probe" : "DB8",
                               "probe_heater" : "DB3",
                               "gasflow" : "DB4",
                               "pressure" : "DB5"
                               }
        self.status_mapping = {"ON" : True,
                                "OFF" : False}
        self.reverse_board_mapping = self._reverse_mapping(self.board_mapping)
        self.reverse_status_mapping = self._reverse_mapping(self.status_mapping)

        vti_uid = self.board_mapping["VTI"]
        probe_uid = self.board_mapping["probe"]
        self.pressure_uid = self.board_mapping["pressure"]

        ### VTI parameters ###
        self.add_parameter(name = "VTI_temp",
                           unit = 'K',
                           label = "T_VTI",
                           get_cmd = lambda: self._get_temperature(vti_uid))
        
        self.add_parameter(name = "VTI_setpoint",
                           unit = 'K',
                           get_cmd = lambda: self._get_temperature_setpoint(vti_uid),
                           set_cmd = lambda setpoint: self._set_temperature_setpoint(vti_uid, setpoint),
                           vals = vals.Numbers(min_value = 0, max_value = 300))
        
        self.add_parameter(name = "VTI_ramp_rate",
                           unit = 'K/min',
                           get_cmd = lambda: self._get_temperature_ramp_rate(vti_uid),
                           set_cmd = lambda ramp_rate: self._set_temperature_ramp_rate(vti_uid, ramp_rate),
                           vals = vals.Numbers(min_value = 0, max_value = 10))
        
        self.add_parameter(name = "VTI_ramp_mode",
                           unit = '',
                           get_cmd = lambda: self._get_ramp_mode(vti_uid),
                           set_cmd = lambda ramp_mode: self._set_ramp_mode(vti_uid, ramp_mode),
                           vals = vals.Bool())
        
        self.add_parameter(name = "VTI_pid_mode",
                           unit = '',
                           get_cmd = lambda: self._get_pid_mode(vti_uid),
                           set_cmd = lambda pid_mode: self._set_pid_mode(vti_uid, pid_mode),
                           vals = vals.Bool())
        
        self.add_parameter(name = "VTI_heater",
                           unit = '%',
                           get_cmd = lambda: self._get_heater_output(vti_uid),
                           set_cmd = lambda heater_output: self._set_heater_output(vti_uid, heater_output),
                           vals = vals.Numbers(min_value = 0, max_value = 100))
        
        ### Probe parameters ###
        self.add_parameter(name = "probe_temp",
                           unit = 'K',
                           label = "T_probe",
                           get_cmd = lambda: self._get_temperature(probe_uid))
        
        self.add_parameter(name = "probe_setpoint",
                           unit = 'K',
                           get_cmd = lambda: self._get_temperature_setpoint(probe_uid),
                           set_cmd = lambda setpoint: self._set_temperature_setpoint(probe_uid, setpoint),
                           vals = vals.Numbers(min_value = 0, max_value = 300))
        
        self.add_parameter(name = "probe_ramp_rate",
                           unit = 'K/min',
                           get_cmd = lambda: self._get_temperature_ramp_rate(probe_uid),
                           set_cmd = lambda ramp_rate: self._set_temperature_ramp_rate(probe_uid, ramp_rate),
                           vals = vals.Numbers(min_value = 0, max_value = 10))
        
        self.add_parameter(name = "probe_ramp_mode",
                           unit = '',
                           get_cmd = lambda: self._get_ramp_mode(probe_uid),
                           set_cmd = lambda ramp_mode: self._set_ramp_mode(probe_uid, ramp_mode),
                           vals = vals.Bool())
        
        self.add_parameter(name = "probe_pid_mode",
                           unit = '',
                           get_cmd = lambda: self._get_pid_mode(probe_uid),
                           set_cmd = lambda pid_mode: self._set_pid_mode(probe_uid, pid_mode),
                           vals = vals.Bool())
        
        self.add_parameter(name = "probe_heater",
                           unit = '%',
                           get_cmd = lambda: self._get_heater_output(probe_uid),
                           set_cmd = lambda heater_output: self._set_heater_output(probe_uid, heater_output),
                           vals = vals.Numbers(min_value = 0, max_value = 100))
        
        ### Flow parameters ###
        self.add_parameter(name = "pressure_control_mode",
                           unit = '',
                           get_cmd = lambda: self._get_pressure_mode(self.pressure_uid),
                           set_cmd = lambda control_mode: self._set_pressure_mode(probe_uid, control_mode),
                           vals = vals.Bool())
        
        self.add_parameter(name = "flow",
                           unit = '%',
                           get_cmd = lambda: self._get_flow(self.pressure_uid),
                           set_cmd = lambda flow: self._set_flow(probe_uid, flow),
                           vals = vals.Numbers(min_value=0, max_value=100))

        self.add_parameter(name = "pressure",
                           unit = 'mb',
                           get_cmd = lambda: self._get_pressure(self.pressure_uid))
        
        self.add_parameter(name = "pressure_setpoint",
                           unit = 'mb',
                           get_cmd = lambda: self._get_pressure_setpoint(self.pressure_uid),
                           set_cmd = lambda pressure_setpoint: self._set_pressure(probe_uid, pressure_setpoint),
                           vals = vals.Numbers(min_value=3, max_value=50))
        

    #Private methods Getters
    def _get_temperature(self, uid: str):
        command = f"READ:DEV:{uid}:TEMP:SIG:TEMP"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        temperature = splitted_repsonse[6]
        log.debug(f'Deduced temperature: {temperature} K')
        info_message = f"Temperature of {self.reverse_board_mapping[uid]}: {temperature} K"
        log.info(info_message)
        return float(temperature)


    def _get_temperature_setpoint(self, uid: str) -> float:
        command = f"READ:DEV:{uid}:TEMP:SIG:CTMP"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        set_temperature = splitted_repsonse[6]
        log.debug(f'Deduced setpoint temperature: {set_temperature} K')
        info_message = f"Temperature of {self.reverse_board_mapping[uid]} set to: {set_temperature} K"
        log.info(info_message)
        return float(set_temperature)
    

    def _get_temperature_ramp_rate(self, uid: str) -> float:
        command = f"READ:DEV:{uid}:TEMP:LOOP:RSET"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        ramp_rate = response[6]
        log.debug(f'Deduced ramp rate: {ramp_rate} K/min')
        info_message = f"Ramp rate of {self.reverse_board_mapping[uid]} set to: {ramp_rate} K/min"
        log.info(info_message)
        return float(ramp_rate)
    

    def _get_ramp_mode(self, uid: str) -> bool:
        """
        Get ramp status of the loop associated to UID.
        Returns:
            - ramp_status (bool): True for "ON" or False for "OFF"
        """
        command = f"READ:DEV:{uid}:TEMP:LOOP:RENA"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        ramp_status = response[6]
        info_message = f"Ramp status of {self.reverse_board_mapping[uid]} is: {ramp_status}"
        log.info(info_message)
        ramp_status = self.status_mapping[ramp_status]
        log.debug(f'Deduced ramp status: {ramp_status}')
        return ramp_status
    

    def _get_pid_mode(self, uid: str) -> bool:
        """
        Get PID status of the loop associated to UID.
        Returns:
            - pid_status (bool): True for Enabled or False for Manual mode
        """
        command = f"READ:DEV:{uid}:TEMP:LOOP:ENAB"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        pid_status = response[6]
        info_message = f"PID status of {self.reverse_board_mapping[uid]} is: {pid_status}"
        log.info(info_message)
        pid_status = self.status_mapping[pid_status]
        log.debug(f'Deduced PID status: {pid_status}')
        return pid_status
    

    def _get_heater_output(self, uid: str) -> float:
        command = f"READ:DEV:{uid}:TEMP:LOOP:HSET"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        heater_output = response[6]
        info_message = f"Heater output of {self.reverse_board_mapping[uid]} is: {heater_output} %"
        log.info(info_message)
        log.debug(f'Deduced heater output: {heater_output} %')
        return float(heater_output)
    

    def _get_pressure_mode(self, uid: str) -> bool:
        """
        Get control status of the pressure loop associated to UID.
        Returns:
            - control_status (bool): True for Enabled or False for Manual mode
        """
        command = f"READ:DEV:{uid}:PRES:LOOP:ENAB"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        control_status = response[6]
        info_message = f"Pressure control status of {self.reverse_board_mapping[uid]} is: {control_status}"
        log.info(info_message)
        control_status = self.status_mapping[control_status]
        log.debug(f'Deduced pressure control status: {control_status}')
        return control_status
    

    def _get_flow(self, uid: str) -> float:
        command = f"READ:DEV:{uid}:PRES:LOOP:FSET"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        flow_percentage = response[6]
        info_message = f"Flow percentage associated with {self.reverse_board_mapping[uid]} is: {flow_percentage} %"
        log.info(info_message)
        log.debug(f'Deduced flow percentage: {flow_percentage} %')
        return float(flow_percentage)
    

    def _get_pressure(self, uid: str) -> float:
        command = f"READ:DEV:{uid}:PRES:SIG:PRES"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        pressure = response[6]
        info_message = f"VTI pressure is: {pressure} mb"
        log.info(info_message)
        return float(pressure)
    

    def _get_pressure_setpoint(self, uid: str) -> float:
        command = f"READ:DEV:{uid}:PRES:LOOP:TSET"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        pressure = response[6]
        info_message = f"VTI pressure setpoint is: {pressure} mb"
        log.info(info_message)
        return float(pressure)


    #Private methods Setters
    def _set_temperature_setpoint(self, uid: str, temperature_setpoint: float) -> None:
        command = f"SET:DEV:{uid}:TEMP:LOOP:TSET:{temperature_setpoint:0.3f}"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        info_message = f"Temperature of {self.reverse_board_mapping[uid]} set to: {temperature_setpoint} K"
        log.info(info_message)
        

    def _set_temperature_ramp_rate(self, uid: str, ramp_rate: float) -> None:
        command = f"SET:DEV:{uid}:TEMP:LOOP:RSET:{ramp_rate:0.3f}"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        info_message = f"Ramp rate of {self.reverse_board_mapping[uid]} set to: {ramp_rate} K/min"
        log.info(info_message)


    def _set_ramp_mode(self, uid: str, ramp_mode: bool) -> None:
        """
        Set ramp status of the loop associated to UID to True ("ON") or False ("OFF").
        """
        ramp_mode = self.reverse_status_mapping(ramp_mode)
        command = f"SET:DEV:{uid}:TEMP:LOOP:RENA:{ramp_mode}"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        info_message = f"Ramp status of {self.reverse_board_mapping[uid]} set to: {ramp_mode}"
        log.info(info_message)

    
    def _set_pid_mode(self, uid: str, pid_mode: bool) -> None:
        """
        Set PID status of the loop associated to UID to True ("ON" i.e. enabled) or False ("OFF" i.e manual).
        """
        pid_mode = self.reverse_status_mapping(pid_mode)
        command = f"SET:DEV:{uid}:TEMP:LOOP:ENAB:{pid_mode}"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        info_message = f"PID status of {self.reverse_board_mapping[uid]} set to: {pid_mode}"
        log.info(info_message)

    
    def _set_heater_output(self, uid: str, heater_output: float) -> None:
        command = f"SET:DEV:{uid}:TEMP:LOOP:HSET:{heater_output:0.2f}"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        info_message = f"Heater output of {self.reverse_board_mapping[uid]} set to: {heater_output:0.2f} %"
        log.info(info_message)
    

    def _set_pressure_mode(self, uid: str, control_mode: bool) -> None:
        """
        Set pressure control mode of the loop associated to UID to True ("ON" i.e. enabled) or False ("OFF" i.e manual).
        """
        control_mode = self.reverse_status_mapping(control_mode)
        command = f"SET:DEV:{uid}:PRES:LOOP:ENAB:{control_mode}"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        info_message = f"Pressure control status of {self.reverse_board_mapping[uid]} set to: {control_mode}"
        log.info(info_message)
    

    def _set_flow(self, uid: str, flow: float) -> None:
        command = f"SET:DEV:{uid}:PRES:LOOP:FSET:{flow:0.2f}"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        info_message = f"Flow associated with {self.reverse_board_mapping[uid]} set to: {flow:0.2f} %"
        log.info(info_message)
    

    def _set_pressure(self, uid: str, pressure: float) -> None:
        command = f"SET:DEV:{uid}:PRES:LOOP:TSET:{pressure:0.2f}"
        log.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        log.debug(f'Received {response} from address {self._address}')
        info_message = f"VTI pressure setpoint set to: {pressure} mb"
        log.info(info_message)
    

    def _reverse_mapping(self, map: dict) -> dict:
        reversed_mapping = {value: key for key, value in map.items()}
        return reversed_mapping