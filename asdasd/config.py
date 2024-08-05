import yaml

config_data = yaml.load("config.yaml")


class Setting:
    def __init__(self):
        self.a = 1
        self.b = 2




setting1 = Setting()

# setting1.a -> 1
# setting1.b -> 2


setting1.a = 5


# setting1.a -> 5


setting2 = Setting()
id(setting1)
id(setting2)
# setting2.a -> 5

# 디자인패턴
# - Singleton
# - Factory


