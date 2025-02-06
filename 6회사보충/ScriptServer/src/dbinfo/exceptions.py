class ModelInfoNotExistsError(Exception):
    def __init__(
        self,
        model_key,
        message: str = "Model does not exists",
    ):
        self.model_key = model_key
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        # logger.debug(f"{self.message} | {self.num_model_data:} {self.num_db_tag}")
        return f"{'Not Loaded':12} | {__class__.__name__}: {self.message} | model_key={self.model_key}"


class InitializingFailError(Exception):
    def __init__(self, message: str = "Can not initialize server"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"


class DBConnectionError(Exception):
    def __init__(self, message: str = "Can not read database info from IPCM Server"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"


class IgnoreSettingParsingError(Exception):
    def __init__(self, message: str = "Can not parse the Ignore setting"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"


class ModelTagSettingError(Exception):
    def __init__(self, message: str = "Can not find tagSettingList"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{__class__.__name__}: {self.message}"
