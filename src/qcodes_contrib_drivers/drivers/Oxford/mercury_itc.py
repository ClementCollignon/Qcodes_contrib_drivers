# OxfordInstruments MercuryiTC class for Teslatron VTI
# Change the board maping to your specific system.
# Setup LOGFILE to some path if you want to keep track of your system over the years. 
# Clement Collignon <clement.collignon.0@gmail.com>, 2024

from qcodes.instrument import VisaInstrument
from qcodes import validators as vals
import logging

LOG = logging.getLogger(__name__)
LOGFILE = None

class Teslatron_MercuryiTC(VisaInstrument):
    """
    Oxford Instrument Mercury iTC Driver for Teslatron VTI

    Args:
        - name: name of the VTI temperature controller.
        - address: IP-address of the Mercury controller.
        - terminator: Defaults to '\n'
        - **kwargs: Forwarded to base class.

    Attributes:
        - board_mapping: maps the motherboard/daughterboard address of
        each sensor or heater or valve.

    Status: beta-version.
    """

    def __init__(self, name: str, address: str, terminator: str = "\n", **kwargs):
        LOG.debug('Initializing instrument')
        super().__init__(name, address, **kwargs)
        self.set_terminator(terminator)

        if LOGFILE:
            log_file = logging.FileHandler(LOGFILE)
            log_file.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            log_file.setFormatter(formatter)
            LOG.addHandler(LOGFILE)

        self.board_mapping = {"VTI" : "MB1.T1",
                               "VTI_heater" : "MB0",
                               "probe" : "DB8.T1",
                               "probe_heater" : "DB3",
                               "gasflow" : "DB4",
                               "pressure" : "DB5.P1"
                               }
        self.status_mapping = {"ON" : True,
                                "OFF" : False}
        self.reverse_board_mapping = self._reverse_mapping(self.board_mapping)
        self.reverse_status_mapping = self._reverse_mapping(self.status_mapping)

        vti_uid = self.board_mapping["VTI"]
        probe_uid = self.board_mapping["probe"]
        pressure_uid = self.board_mapping["pressure"]

        ### VTI temperature parameters ###
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
        
        ### Probe temperature parameters ###
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
        
        ### Flow/Pressure parameters ###
        self.add_parameter(name = "pressure_control_mode",
                           unit = '',
                           get_cmd = lambda: self._get_pressure_mode(pressure_uid),
                           set_cmd = lambda control_mode: self._set_pressure_mode(pressure_uid, control_mode),
                           vals = vals.Bool())
        
        self.add_parameter(name = "flow",
                           unit = '%',
                           get_cmd = lambda: self._get_flow(pressure_uid),
                           set_cmd = lambda flow: self._set_flow(pressure_uid, flow),
                           vals = vals.Numbers(min_value=0, max_value=100))

        self.add_parameter(name = "pressure",
                           unit = 'mb',
                           get_cmd = lambda: self._get_pressure(pressure_uid))
        
        self.add_parameter(name = "pressure_setpoint",
                           unit = 'mb',
                           get_cmd = lambda: self._get_pressure_setpoint(pressure_uid),
                           set_cmd = lambda pressure_setpoint: self._set_pressure(pressure_uid, pressure_setpoint),
                           vals = vals.Numbers(min_value=1, max_value=50))
        

    #Private methods: Getters
    def _get_temperature(self, uid: str):
        """
        Read temperature of device located at `uid`.
        Returns:
            - temperature (float): the temperature reading in K. 
        """
        command = f"READ:DEV:{uid}:TEMP:SIG:TEMP"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        temperature = splitted_repsonse[6]
        LOG.debug(f'Deduced temperature: {temperature}')
        info_message = f"Temperature of {self.reverse_board_mapping[uid]}: {temperature}"
        LOG.info(info_message)
        return float(temperature[:-1])


    def _get_temperature_setpoint(self, uid: str) -> float:
        """
        Read temperature setpoint of device located at `uid`.
        Returns:
            - set_temperature (float): the temperature setpoint in K. 
        """
        command = f"READ:DEV:{uid}:TEMP:LOOP:TSET"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        set_temperature = splitted_repsonse[6]
        LOG.debug(f'Deduced setpoint temperature: {set_temperature}')
        info_message = f"Setpoint of {self.reverse_board_mapping[uid]} is: {set_temperature}"
        LOG.info(info_message)
        return float(set_temperature[:-1])
    

    def _get_temperature_ramp_rate(self, uid: str) -> float:
        """
        Read ramp rate of the loop controling the device located at `uid`.
        Returns:
            - ramp_rate (float): in K/min 
        """
        command = f"READ:DEV:{uid}:TEMP:LOOP:RSET"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        ramp_rate = splitted_repsonse[6]
        LOG.debug(f'Deduced ramp rate: {ramp_rate}')
        info_message = f"Ramp rate of {self.reverse_board_mapping[uid]} set to: {ramp_rate}"
        LOG.info(info_message)
        return float(ramp_rate[:-3])
    

    def _get_ramp_mode(self, uid: str) -> bool:
        """
        Get ramp status of the loop associated to `uid`.
        Returns:
            - ramp_status (bool): True for "ON" or False for "OFF"
        """
        command = f"READ:DEV:{uid}:TEMP:LOOP:RENA"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        ramp_status = splitted_repsonse[6]
        info_message = f"Ramp status of {self.reverse_board_mapping[uid]} is: {ramp_status}"
        LOG.info(info_message)
        ramp_status = self.status_mapping[ramp_status]
        LOG.debug(f'Deduced ramp status: {ramp_status}')
        return ramp_status
    

    def _get_pid_mode(self, uid: str) -> bool:
        """
        Get PID status of the loop associated to `uid`.
        Returns:
            - pid_status (bool): True for Enabled or False for Manual mode
        """
        command = f"READ:DEV:{uid}:TEMP:LOOP:ENAB"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        pid_status = splitted_repsonse[6]
        info_message = f"PID status of {self.reverse_board_mapping[uid]} is: {pid_status}"
        LOG.info(info_message)
        pid_status = self.status_mapping[pid_status]
        LOG.debug(f'Deduced PID status: {pid_status}')
        return pid_status
    

    def _get_heater_output(self, uid: str) -> float:
        """
        Read heater output of the loop associated to `uid`.
        Returns:
            - heater_output (float): heater output in percent
        """
        command = f"READ:DEV:{uid}:TEMP:LOOP:HSET"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        heater_output = splitted_repsonse[6]
        info_message = f"Heater output of {self.reverse_board_mapping[uid]} is: {heater_output} %"
        LOG.info(info_message)
        LOG.debug(f'Deduced heater output: {heater_output} %')
        return float(heater_output)
    

    def _get_pressure_mode(self, uid: str) -> bool:
        """
        Get control status of the pressure loop associated to `uid`.
        Returns:
            - control_status (bool): True for Enabled or False for Manual mode
        """
        command = f"READ:DEV:{uid}:PRES:LOOP:ENAB"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        control_status = splitted_repsonse[6]
        info_message = f"Pressure control status of {self.reverse_board_mapping[uid]} is: {control_status}"
        LOG.info(info_message)
        control_status = self.status_mapping[control_status]
        LOG.debug(f'Deduced pressure control status: {control_status}')
        return control_status
    

    def _get_flow(self, uid: str) -> float:
        """
        Get the actual flow of the loop associated to `uid`.
        Returns:
            - flow_percentage (float): the flow in percent.
        """
        command = f"READ:DEV:{uid}:PRES:LOOP:FSET"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        flow_percentage = splitted_repsonse[6]
        info_message = f"Flow percentage associated with {self.reverse_board_mapping[uid]} is: {flow_percentage} %"
        LOG.info(info_message)
        LOG.debug(f'Deduced flow percentage: {flow_percentage} %')
        return float(flow_percentage)
    

    def _get_pressure(self, uid: str) -> float:
        """
        Get the pressure reading of device `uid`.
        Returns:
            - pressure (float): the pressure in mb.
        """
        command = f"READ:DEV:{uid}:PRES:SIG:PRES"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        pressure = splitted_repsonse[6]
        info_message = f"VTI pressure is: {pressure}"
        LOG.info(info_message)
        return float(pressure[:-2])
    

    def _get_pressure_setpoint(self, uid: str) -> float:
        """
        Get the pressure setpoint of the loop associated to `uid`.
        Returns:
            - pressure (float): the pressure setpoint in mb.
        """
        command = f"READ:DEV:{uid}:PRES:LOOP:PRST"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        splitted_repsonse = response.split(":")
        pressure = splitted_repsonse[6]
        info_message = f"VTI pressure setpoint is: {pressure} mb"
        LOG.info(info_message)
        return float(pressure[:-2])


    #Private methods: Setters
    def _set_temperature_setpoint(self, uid: str, temperature_setpoint: float) -> None:
        """
        Set the temperature setpoint of the loop associated to `uid` to `temperature_setpoint`.
        """
        command = f"SET:DEV:{uid}:TEMP:LOOP:TSET:{temperature_setpoint:0.3f}"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        info_message = f"Temperature of {self.reverse_board_mapping[uid]} set to: {temperature_setpoint} K"
        LOG.info(info_message)
        

    def _set_temperature_ramp_rate(self, uid: str, ramp_rate: float) -> None:
        """
        Set the tempramp rate of the loop associated to `uid` to `ramp_rate`.
        """
        command = f"SET:DEV:{uid}:TEMP:LOOP:RSET:{ramp_rate:0.3f}"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        info_message = f"Ramp rate of {self.reverse_board_mapping[uid]} set to: {ramp_rate} K/min"
        LOG.info(info_message)


    def _set_ramp_mode(self, uid: str, ramp_mode: bool) -> None:
        """
        Set ramp status of the loop associated to `uid` to True ("ON") or False ("OFF").
        """
        ramp_mode = self.reverse_status_mapping[ramp_mode]
        command = f"SET:DEV:{uid}:TEMP:LOOP:RENA:{ramp_mode}"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        info_message = f"Ramp status of {self.reverse_board_mapping[uid]} set to: {ramp_mode}"
        LOG.info(info_message)

    
    def _set_pid_mode(self, uid: str, pid_mode: bool) -> None:
        """
        Set PID status of the loop associated to `uid` to True ("ON" i.e. enabled) or False ("OFF" i.e manual).
        """
        pid_mode = self.reverse_status_mapping[pid_mode]
        command = f"SET:DEV:{uid}:TEMP:LOOP:ENAB:{pid_mode}"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        info_message = f"PID status of {self.reverse_board_mapping[uid]} set to: {pid_mode}"
        LOG.info(info_message)

    
    def _set_heater_output(self, uid: str, heater_output: float) -> None:
        """
        Set the heater output of the loop associated to `uid` to `heater_output`.
        """
        command = f"SET:DEV:{uid}:TEMP:LOOP:HSET:{heater_output:0.2f}"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        info_message = f"Heater output of {self.reverse_board_mapping[uid]} set to: {heater_output:0.2f} %"
        LOG.info(info_message)
    

    def _set_pressure_mode(self, uid: str, control_mode: bool) -> None:
        """
        Set pressure control mode of the loop associated to `uid` to True ("ON" i.e. enabled) or False ("OFF" i.e manual).
        """
        control_mode = self.reverse_status_mapping[control_mode]
        command = f"SET:DEV:{uid}:PRES:LOOP:ENAB:{control_mode}"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        info_message = f"Pressure control status of {self.reverse_board_mapping[uid]} set to: {control_mode}"
        LOG.info(info_message)
    

    def _set_flow(self, uid: str, flow: float) -> None:
        """
        Set the flow of the loop associated to `uid` to `flow`.
        """
        command = f"SET:DEV:{uid}:PRES:LOOP:FSET:{flow:0.2f}"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        info_message = f"Flow associated with {self.reverse_board_mapping[uid]} set to: {flow:0.2f} %"
        LOG.info(info_message)
    

    def _set_pressure(self, uid: str, pressure: float) -> None:
        """
        Set the pressure setpoint output of the loop associated to `uid` to `pressure`.
        """
        command = f"SET:DEV:{uid}:PRES:LOOP:PRST:{pressure:0.2f}"
        LOG.debug(f'Sending {command} at address {self._address}')
        response = self.visa_handle.query(command)
        LOG.debug(f'Received {response} from address {self._address}')
        info_message = f"VTI pressure setpoint set to: {pressure}"
        LOG.info(info_message)
    

    def _reverse_mapping(self, map: dict) -> dict:
        """
        Reverse the mapping of a dict. Needs all the values to be unique.
        """
        reversed_mapping = {value: key for key, value in map.items()}
        return reversed_mapping