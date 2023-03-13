from ... import global_vars
from ...settings import tools_qt


def tr(msg):
    return tools_qt.tr(msg, context_name=global_vars.plugin_name)
