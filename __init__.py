"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

from . import settings


def classFactory(iface): 
    """ Load Plugin class from main plugin file.
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    settings.init_plugin()
    from .main import GWAssetPlugin
    return GWAssetPlugin(iface)

