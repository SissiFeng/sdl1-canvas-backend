import logging
import time
import serial
import serial.tools.list_ports

LOGGER = logging.getLogger(__name__)

class ArduinoException(Exception):
    pass
class ArduinoTimeout(Exception):
    pass

class Arduino:
    """Class for the arduino robot relate activities for the openTron setup."""

    heaterSetPoints = []

    def __init__(
        self,
        arduinoPort: str = "COM3",
        basePlates: list = [0, 1],
        nozzlePumps: list = [0,1,2], # Water, HCL, WasteOut
        rinsePumps: list = [3,5,4], # Water, HCL, WasteOut
        pump_slope: dict = {0: 7.97/5, 1: 8.00/5, 2: 7.87/5, 3: 7.92/5, 4: 8.18/5, 5: 7.48/5}, # mL/s
    ):
        """Initialize the arduino robotic parts. The robot consist of
        cartridges that are inserted into the openTron robot. Each cartridge
        has a temperature sensor, heating elements that are PID controlled
        through a setpoint and an ultrasonic transducer.
        Pumps and ultrasonic drivers that are all connected to relays.

        The robot assumes that cartridges are numbered from 0 and up.
        The robot assumes that relays are used both for pumps and ultrasonic
        sensors.
        The robot assumes that cartridge 0 is connected to the first ultrasound
        relay and so on; eg. cartridge 0 is connected to ultrasonic relay 6,
        while cartridge 1 is connected to ultrasonic relay 7.

        The pump calibration is done by a linear calibration, by the following
        equation: volume = pump_slope * relay_time_on + pump_intercept
        It can be measured by running the pump while measuring the weight
        dispensed, at eg. 0.5 seconds, 1 seconds, 2 seconds, 5 seconds,
        10 seconds, 20 seconds.

        Args:
            arduino_search_string (str, optional): _description_. Defaults to
                "CH340".
            list_of_cartridges (list, optional): List of cartridge numbers.
                Defaults to [0, 1].
            list_of_pump_relays (list, optional): List of pump relay numbers.
                Must correspond with wirering.  Defaults to [0, 1, 2, 3, 4, 5].
            list_of_ultrasonic_relays (list, optional): List of ultrasonic
                relay numbers. Must correspond with wirering.
                Defaults to [6, 7].
            pump_slope (dict, optional): Dictionary with pump number as key and
                slope as value.
                Defaults to {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0}.
            pump_intercept (dict, optional): Dictionary with pump number as
                key and intercept as value.
                Defaults to {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}.
        """
        self.SERIAL_PORT = self.__define_arduino_port(arduinoPort)
        self.BAUD_RATE = 115200
        self.list_of_cartridges = basePlates
        self.pump_slope = pump_slope
        self.connect()


    def connect(self, timeout_s:int=300) -> None:
        """Connects to serial port of arduino.  Default 300s timeout"""
        # Connection to arduino
        self.connection = serial.Serial(
            port=self.SERIAL_PORT,
            baudrate=self.BAUD_RATE,
            timeout=timeout_s,
        )
        time.sleep(3)  # Loadtime compensation, don't know if needed

        # Set target temperatures for heaters again
        for heaterNum, temp in enumerate(self.heaterSetPoints):
            self.setTemp(heaterNum, temp)


    def disconnect(self) -> None:
        """Disconnects from serial port of arduino"""
        self.connection.close()


    def refreshConnection(self) -> None:
        self.disconnect()
        time.sleep(0.5)
        self.connect()


    def getPumpOn(self, pumpNumber:int, retries:int=3) -> bool:
        LOGGER.info(f"Getting status of pump {pumpNumber}")
        self.connection.write(f"get_pump_state {pumpNumber}\n".encode())
        
        res = self.__getSafeResponse()

        if res[0] == "1":
            LOGGER.info(f"Pump {pumpNumber} is ON")
            return True
        elif res[0] == "0":
            LOGGER.info(f"Pump {pumpNumber} is OFF")
            return False

        raise ArduinoException("Arduino returned invalid pump state")


    def setPump(self, pumpNumber:int, turnOn:bool, retries:int=3) -> None:
        LOGGER.info(f"{'Enabling' if turnOn else 'Disabling'} pump {pumpNumber}")
        if turnOn:
            self.connection.write(f"set_pump_on {pumpNumber}\n".encode())
        else:
            self.connection.write(f"set_pump_off {pumpNumber}\n".encode())
            
        self.__getSafeResponse(retries, Arduino.setPump, (self, pumpNumber, turnOn, 0), not turnOn)
        LOGGER.debug(f"Pump {pumpNumber} is {'on' if turnOn else 'off'}")


    def setPumpOnTimer(self, pumpNumber:int, timeOn_ms:int, retries:int=3) -> None:
        LOGGER.info(f"Enabling pump {pumpNumber} for {timeOn_ms}ms")
        self.connection.write(f"set_pump_on_time {pumpNumber} {timeOn_ms}\n".encode())
            
        self.__getSafeResponse(retries, Arduino.setPumpOnTimer, (self, pumpNumber, timeOn_ms, 0), True, timeout_s=timeOn_ms/1000 + 3) # Ensures Arduino completes successfully
        LOGGER.debug(f"Pump {pumpNumber} ran for {timeOn_ms}ms")


    def setTemp(self, baseNumber:int, targetTemp:float, retries:int=3) -> None:
        targetTemp = round(targetTemp, 1) # All that's supported by the PID

        LOGGER.info(f"Setting base {baseNumber} temperature to {targetTemp}C")
        self.connection.write(f"set_base_temp {baseNumber} {targetTemp}\n".encode())
        
        self.__getSafeResponse(retries, Arduino.setTemp, (self, baseNumber, targetTemp, 0), False) # Ensures Arduino completes successfully

        # Update the object to reset the temperatures whenever the connection resets
        while len(self.heaterSetPoints) < baseNumber:
            self.heaterSetPoints.append(0) # Fix size of tracked setpoints if it doesn't make sense
        self.heaterSetPoints[baseNumber] = targetTemp

        LOGGER.debug(f"Base {baseNumber} temperature set successfully")


    def getTemp(self, baseNumber:int) -> float:
        LOGGER.info(f"Getting temperature from base {baseNumber}")
        self.connection.write(f"get_base_temp {baseNumber}\n".encode())
        
        res = self.__getResponse()
        temperature = float(res[0])
        LOGGER.debug(f"Base {baseNumber} returned a temperature reading of {temperature}C")

        return temperature


    def setUltrasonic(self, baseNumber:int, turnOn:bool, retries:int=3) -> None:
        LOGGER.info(f"{'Enabling' if turnOn else 'Disabling'} base {baseNumber}'s sonicator")
        if turnOn:
            self.connection.write(f"set_ultrasonic_on {baseNumber}\n".encode())
        else:
            self.connection.write(f"set_ultrasonic_off {baseNumber}\n".encode())

        self.__getSafeResponse(retries, Arduino.setUltrasonic, (self, baseNumber, turnOn, 0), not turnOn)        
        LOGGER.debug(f"Base {baseNumber}'s sonicator is {'on' if turnOn else 'off'}")
        

    def setUltrasonicOnTimer(self, baseNumber:int, timeOn_ms:int, retries:int=3) -> None:
        LOGGER.info(f"Enabling base {baseNumber}'s sonicator for {timeOn_ms}ms")
        self.connection.write(f"set_ultrasonic_on_time {baseNumber} {timeOn_ms}\n".encode())
            
        self.__getSafeResponse(retries, Arduino.setUltrasonicOnTimer, (self, baseNumber, timeOn_ms, 0), True, timeout_s=timeOn_ms/1000 + 3) # Ensures Arduino completes successfully
        LOGGER.debug(f"Base {baseNumber}'s sonicator ran for {timeOn_ms}ms")


    def __getResponse(self, timeout_s:int=3):
        # Collect all data sent over serial line
        # Exit when '0' or '1' is sent on it's own line
        returnData = []
        line = b""
        startTime = time.time()

        while (time.time() - startTime < timeout_s):
            if self.connection.in_waiting > 0:
                line += self.connection.read()
                # print(line)
                if line.endswith(b'\r\n'):
                    lineStr = line.decode().strip()
                    line = b''
                    if lineStr == "0":
                        return returnData
                    elif lineStr == "1":
                        LOGGER.error("Arduino function recieved bad arguments")
                        raise ArduinoException("Arduino function recieved bad arguments")
                    else:
                        returnData.append(lineStr)

        # Timed out, EMI may have fried the I2C line and caused the arduino to freeze
        # Try restarting the Serial connection to reset the arduino
        self.refreshConnection()
        LOGGER.error("Arduino response timed out, resetting the Arduino")
        raise ArduinoTimeout("Arduino response timed out")


    def __getSafeResponse(self, retries, retryFunc, retryArgs, resetIsSuccess, timeout_s=2):
        try:
            return self.__getResponse(timeout_s=timeout_s) # Ensures Arduino completes successfully
        except ArduinoTimeout:
            if retries == 0 or resetIsSuccess: return

            # Try again
            tryCount = 0
            while tryCount < retries:
                try:
                    return retryFunc(retryArgs)
                except:
                    tryCount += 1
            raise ArduinoTimeout(f"Arduino failed all {1+retries} attempts")
        

    def dispense_ml(self, pumpNumber:int, volume:float):
        """Dispense the given volume in ml.
        Args:
            pump (int): Pump number
            volume (float): Volume in ml to be dispensed.
        """
        # Calculate the time to turn on the pump
        time_on = int(volume / self.pump_slope[pumpNumber] * 1000)

        LOGGER.info(f"Dispensing {volume}ml from pump {pumpNumber}")

        self.setPumpOnTimer(pumpNumber, time_on)


    def __define_arduino_port(self, search_string: str) -> str:
        """Find the port of the Arduino.
        Args:
            search_string (str, optional): Name of the Arduino.
        Returns:
            str: Port of the Arduino.
        """

        # List Arduinos on computer
        ports = list(serial.tools.list_ports.comports())
        logging.info("List of USB ports:")
        for p in ports:
            logging.info(f"{p}")
        arduino_ports = [p.device for p in ports if search_string in p.description]
        if not arduino_ports:
            logging.error("No Arduino found")
            raise IOError("No Arduino found")
        if len(arduino_ports) > 1:
            logging.warning("Multiple Arduinos found - using the first")

        # Automatically find Arduino
        arduino = str(serial.Serial(arduino_ports[0]).port)
        logging.info(f"Arduino found on port: {arduino}")
        return arduino


    # def wait_for_arduino(self, max_wait_time: int = 2000):
    #     """To make sure arduino completed the particular task.

    #     Args:
    #         max_wait_time (int, optional): Maximum wait time to get response
    #         from arduino in seconds. Defaults to 2000.

    #     Raises:
    #         RuntimeWarning: Arduino did not finish the job in given time.
    #     """
    #     max_try = (1 / self.CONNECTION_TIMEOUT) * max_wait_time
    #     count = 0
    #     while count < max_try:
    #         LOGGER.debug("waiting for arduino to finish the task")
    #         state = self.connection.read().decode()
    #         if state == "#":
    #             LOGGER.debug("Arduino finished the task")
    #             break
    #         count += 1
    #     else:
    #         raise RuntimeWarning(
    #             "Arduino did not finish the job.",
    #             "Check arduino IDE or increase the value of max_wait_time.",
    #         )


    # def set_relay_on_time(self, relay_num: int, time_on: float) -> None:
    #     """Turn on the relay for the given time.

    #     Args:
    #         relay_num (int): Number of the relay.
    #         time_on (float): Time in seconds which relay should turned on.
    #     """
    #     LOGGER.info(f"Switching relay {relay_num} on for {time_on} seconds")
    #     time_ms = round(time_on * 1000, 0)
    #     self.connection.write(f"<set_relay_on_time,{relay_num},{time_ms}>".encode())
    #     self.wait_for_arduino()

    # def get_relay_status(self, relay_num: int) -> bool:
    #     """Get the status of the relay.

    #     Args:
    #         relay_num (int): Number of the relay.

    #     Returns:
    #         bool: Status of the relay.
    #     """

    #     LOGGER.info(f"Getting status of relay {relay_num}")
    #     self.connection.write(f"<get_relay_{relay_num}_state>".encode())
    #     status = self.connection.readline().decode()
    #     if status == "True":
    #         LOGGER.info(f"Status of relay {relay_num}: High / On")
    #         return True
    #     else:
    #         LOGGER.info(f"Status of relay {relay_num}: Low / Off")
    #         return False
