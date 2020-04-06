# wrapper for loading settings from a hjson file validating fields

import os
import hjson


def load_configuration():
    """
    load config from /configuration/config.hjson, validate required fields
    """
    # home directory and the config.hjson file
    this_directory = os.path.dirname(__file__)
    config_filename = os.path.join(this_directory, 'config.hjson')

    # error if the config.hjson file doesn't exist
    if not os.path.exists(config_filename):
        raise Exception('load_configuration() ERROR: The config.hjson file does not exist here: %s. Copy sample'
                        '_config.hjson to config.hjson and change the settings to match your environment.' %
                        config_filename)

    # load the settings file
    config = hjson.loads(open(config_filename).read())

    return config
