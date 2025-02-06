class InvalidIPAddressError(Exception):
    def __init__(self, ip_address, message: str = "Invalid Port Number"):
        self.ip_address = ip_address
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} | ip_address={self.ip_address}"


class InvalidPortNumberError(Exception):
    def __init__(self, port_number, message: str = "Invalid Port Number"):
        self.port_number = port_number
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} | port_number={self.port_number}"

class TrainDataNotFoundError(Exception):
    def __init__(self, message: str = "Can not find data to train requested model."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"
    
class InitializingFailError(Exception):
    def __init__(self, message: str = "Failed to initialize server"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"


class InvalidFormatError(Exception):
    def __init__(self, message: str = "Invalid format"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"


class InfluxDataLoadError(Exception):
    def __init__(
        self,
        message: str = "Failed to load historical data requested tag may not exist or No data",
    ):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"


class InfluxConnectionError(Exception):
    def __init__(self, message: str = "Failed to connect to Inluxdb"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"


class InvalidDurationError(Exception):
    def __init__(self, message: str = "Invalid duration"):
        self.message = message

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"
