#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>

#include "gcc-plugin.h"
#include "plugin-version.h"
#include "c-family/c-common.h"
#include "stringpool.h"

#include "config_parser.h"
#include "get_arg_config.h"

int plugin_is_GPL_compatible;

static tree make_attribute_optimize_flags(const char *flags) {
    tree attr_name = get_identifier("optimize");
    tree flag_str = build_string(strlen(flags) + 1, flags);
    tree arg_list = tree_cons(NULL_TREE, flag_str, NULL_TREE);
    return tree_cons(attr_name, arg_list, NULL_TREE);
}

static void set_function_attribute(tree fndecl, const std::string &attribute) {
    tree attr = make_attribute_optimize_flags(attribute.c_str());
    DECL_ATTRIBUTES(fndecl) = chainon(DECL_ATTRIBUTES(fndecl), attr);
}

static void handle_optimize_attribute(tree node, const std::string &attribute) {
    tree arg = build_string(attribute.size(), attribute.c_str());
    tree args = tree_cons(NULL_TREE, arg, NULL_TREE);

    struct cl_optimization cur_opts;
    tree old_opts = DECL_FUNCTION_SPECIFIC_OPTIMIZATION(node);

    cl_optimization_save(&cur_opts, &global_options, &global_options_set);

    if (old_opts)
        cl_optimization_restore(&global_options, &global_options_set,
                                TREE_OPTIMIZATION(old_opts));

    parse_optimize_options(args, true);
    DECL_FUNCTION_SPECIFIC_OPTIMIZATION(node) = build_optimization_node(&global_options, &global_options_set);

    cl_optimization_restore(&global_options, &global_options_set, &cur_opts);
}

static void append_to_attribute_stream(std::ostringstream &oss, unsigned int opt_set, const std::string &opt_name) {
    if (opt_set != OPTIMIZATION_SET_DEFAULT) {
        oss << "," << (opt_set == OPTIMIZATION_SET_ON ? "-f" : "-fno-") << opt_name;
    }
}

static std::string build_attribute_string(const Optimizations &opts) {
    std::ostringstream oss;

    oss << "-O" << opts.level;

    append_to_attribute_stream(oss, opts.selective_scheduling, "selective-scheduling");
    append_to_attribute_stream(oss, opts.selective_scheduling2, "selective-scheduling2");
    append_to_attribute_stream(oss, opts.schedule_insns, "schedule-insns");
    append_to_attribute_stream(oss, opts.schedule_insns2, "schedule-insns2");
    append_to_attribute_stream(oss, opts.sched_interblock, "sched-interblock");
    append_to_attribute_stream(oss, opts.unroll_loops, "unroll-loops");
    append_to_attribute_stream(oss, opts.peel_loops, "peel-loops");
    append_to_attribute_stream(oss, opts.unswitch_loops, "unswitch-loops");
    append_to_attribute_stream(oss, opts.tree_loop_vectorize, "tree-loop-vectorize");
    append_to_attribute_stream(oss, opts.tree_slp_vectorize, "tree-slp-vectorize");
    append_to_attribute_stream(oss, opts.tree_tail_merge, "tree-tail-merge");
    append_to_attribute_stream(oss, opts.tree_loop_distribute_patterns, "tree-loop-distribute-patterns");
    append_to_attribute_stream(oss, opts.branch_probabilities, "branch-probabilities");
    append_to_attribute_stream(oss, opts.code_hoisting, "code-hoisting");

    return oss.str();
}

static void on_parse_function(void *event_data, void *user_data) {
    tree fndecl = static_cast<tree>(event_data);
    if (fndecl->base.code != FUNCTION_DECL || DECL_ATTRIBUTES(fndecl) != NULL_TREE) {
        return;
    }

    auto function_name = std::string(IDENTIFIER_POINTER(DECL_NAME(fndecl)));
    location_t loc = DECL_SOURCE_LOCATION(fndecl);
    auto filename = std::string(basename(LOCATION_FILE(loc)));
    int line_number = LOCATION_LINE(loc);

    auto *rules = static_cast<std::vector<Rule> *>(user_data);

    for (auto it = rules->rbegin(); it != rules->rend(); ++it) {
        if (it->type != "function" || it->function_name != function_name) {
            continue;
        }
        if (it->line_number != -1 && it->line_number != line_number) {
            continue;
        }
        if (!it->filename.empty() && it->filename != filename) {
            continue;
        }
        std::string current_attribute = build_attribute_string(it->opts);
        handle_optimize_attribute(fndecl, current_attribute);
        set_function_attribute(fndecl, current_attribute);
        break;
    }
}

static void handle_optimize_pragma(const std::string &attribute) {
    tree arg = build_string(attribute.size(), attribute.c_str());
    tree args = tree_cons(NULL_TREE, arg, NULL_TREE);
    parse_optimize_options(args, false);
    current_optimize_pragma = chainon(current_optimize_pragma, args);
    optimization_current_node = build_optimization_node(&global_options, &global_options);
}

static void on_start_unit(std::vector<Rule> *rules) {
    for (auto it = rules->rbegin(); it != rules->rend(); ++it) {
        if (it->type == "file" && (it->filename == "*" || it->filename == std::string(main_input_basename))) {
            std::string attributes = build_attribute_string(it->opts);
            handle_optimize_pragma(attributes);
            break;
        }
    }
}

static void on_plugin_finish(void *event_data, void *user_data) {
    auto *data = static_cast<std::vector<Rule> *>(user_data);
    delete data;
}

int plugin_init(struct plugin_name_args *plugin_info,
                struct plugin_gcc_version *version) {
    if (!plugin_default_version_check(version, &gcc_version)) {
        fprintf(stderr, "GCC plugin version mismatch!\n");
        return 1;
    }

    const char *config_path = get_config_filepath(plugin_info);

    if (!config_path) {
        return 1;
    }

    std::vector<Rule> *rules = parse_config_file(config_path);

    on_start_unit(rules);

    register_callback(
        plugin_info->base_name,
        PLUGIN_FINISH_PARSE_FUNCTION,
        on_parse_function,
        rules
    );

    register_callback(
        plugin_info->base_name,
        PLUGIN_FINISH,
        on_plugin_finish,
        rules
    );

    return 0;
}
