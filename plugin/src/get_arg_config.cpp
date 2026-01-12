#include "get_arg_config.h"

#include <iostream>
#include <cstring>

const char *get_config_filepath(struct plugin_name_args *plugin_info) {
    const char *config_path = nullptr;

    for (int i = 0; i < plugin_info->argc; ++i) {
        const char *key = plugin_info->argv[i].key;
        const char *value = plugin_info->argv[i].value;

        if (strcmp(key, config_arg_name) == 0) {
            if (value) {
                config_path = value;
            } else {
                fprintf(stderr, "Error: '%s' argument requires a value.\n", config_arg_name);
                return nullptr;
            }
        }
    }

    if (!config_path) {
        fprintf(stderr, "Error: Required plugin argument '%s' not provided.\n", config_arg_name);
        return nullptr;
    }

    return config_path;
}
