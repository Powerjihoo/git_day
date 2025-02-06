class SingletonInstance(type):
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super(SingletonInstance, cls).__call__(*args, **kwargs)
        return cls._instance[cls]
