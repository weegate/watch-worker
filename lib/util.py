import os
import logging
import yaml

ROOT_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

CONFIG_PATH = os.path.join(ROOT_PATH, "conf")
DATA_PATH = os.path.join(ROOT_PATH, "data")
LOG_PATH = os.path.join(ROOT_PATH, "logs")
LIB_PATH = os.path.join(ROOT_PATH, "lib")
POLICY_PATH = os.path.join(ROOT_PATH, "policy")

def config(*fname):
    return os.path.join(CONFIG_PATH, *fname)

def data(*fname):
    return os.path.join(DATA_PATH, *fname)

def init_logger(name=""):
    """
    :param name: set log name
    :return: logging obj
    """
    """
    """
    logging.basicConfig(format='%(levelname)s|%(filename)s|%(lineno)d|%(asctime)s|%(message)s',level=logging.INFO)
    logger = logging.getLogger(name)

    config_path = os.path.join(CONFIG_PATH, 'worker.yaml');
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            profile = yaml.safe_load(f)
            if 'log' in profile and 'level' in profile['log']:
                logger.setLevel(eval("logging."+profile['log']['level']))

    return logger

def get_policy_config(policy_name=""):
    """
    :param policy_name: policy name from diversion type
    :return: policy config dict
    """
    policy_config = {}
    config_path = os.path.join(CONFIG_PATH, 'policy.yaml');
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            profile = yaml.safe_load(f)
            if policy_name in profile:
                policy_config = profile[policy_name]
            elif policy_name == "":
                policy_config = profile

    return policy_config

