from ... import global_vars
from ...settings import tools_qt


def tr(msg):
    tools_qt.manage_translation(global_vars.plugin_name, None, plugin_dir=global_vars.plugin_dir,
                                plugin_name=global_vars.plugin_name)
    return tools_qt.tr(msg, context_name=global_vars.plugin_name)
