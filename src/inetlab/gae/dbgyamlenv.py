import os, logging, yaml

def set_env_from_yaml(app_yaml):
    try:
        app_cfg = yaml.load(open(app_yaml), Loader=yaml.FullLoader)
    except AttributeError as err:
        if 'FullLoader' in str(err):
            app_cfg = yaml.load(open(app_yaml))
        else:
            raise err

    for env_name, env_value in app_cfg['env_variables'].items():
        logging.info("%s = %s", env_name, '*' * len(env_value) if 'password' in env_name else env_value)
        os.environ[env_name] = env_value
