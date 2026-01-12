#ifndef DEFINITION_GET_ARG_CONFIG_H
#define DEFINITION_GET_ARG_CONFIG_H

#include "gcc-plugin.h"
#include "plugin.h"

inline const char *config_arg_name = "config";

const char *get_config_filepath(struct plugin_name_args *plugin_info);

#endif // DEFINITION_GET_ARG_CONFIG_H
