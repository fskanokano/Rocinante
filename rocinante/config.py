class Config(object):
    _config = {}

    @classmethod
    def get_config(cls, name):
        return cls._config.get(name, None)

    @classmethod
    def set_config(cls, name, config):
        config_dict = {key: getattr(config, key) for key in dir(config) if
                       not key.startswith('__') and not callable(getattr(config, key))}
        cls._config[name] = config_dict
