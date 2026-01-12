#include "config_parser.h"

#include <string>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <iostream>

static void trim(std::string& s) {
    s.erase(0, s.find_first_not_of(" \t\r\n"));
    s.erase(s.find_last_not_of(" \t\r\n") + 1);
}

static unsigned int parse_bool(const std::string& value) {
    std::string lower = value;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
    if (lower == "true" || lower == "1") {
        return OPTIMIZATION_SET_ON;
    } else {
        return OPTIMIZATION_SET_OFF;
    }
}

static bool parse_key_value(const std::string& line, std::string& key, std::string& value) {
    size_t eq_pos = line.find('=');
    if (eq_pos == std::string::npos) {
        return false;
    }

    key = line.substr(0, eq_pos);
    value = line.substr(eq_pos + 1);
    trim(key);
    trim(value);
    return true;
}

static void apply_field(Rule& rule, const std::string& key, const std::string& value) {
    if (key == "type") {
        rule.type = value;
    } else if (key == "function_name") {
        rule.function_name = value;
    } else if (key == "filename") {
        rule.filename = value;
    } else if (key == "line_number") {
        rule.line_number = std::stoi(value);
    } else if (key == "opt-level") {
        rule.opts.level = std::stoi(value);
    } else if (key == "opt-selective-scheduling") {
        rule.opts.selective_scheduling = parse_bool(value);
    } else if (key == "opt-selective-scheduling2") {
        rule.opts.selective_scheduling2 = parse_bool(value);
    } else if (key == "opt-schedule-insns") {
        rule.opts.schedule_insns = parse_bool(value);
    } else if (key == "opt-schedule-insns2") {
        rule.opts.schedule_insns2 = parse_bool(value);
    } else if (key == "opt-sched-interblock") {
        rule.opts.sched_interblock = parse_bool(value);
    } else if (key == "opt-unroll-loops") {
        rule.opts.unroll_loops = parse_bool(value);
    } else if (key == "opt-peel-loops") {
        rule.opts.peel_loops = parse_bool(value);
    } else if (key == "opt-unswitch-loops") {
        rule.opts.unswitch_loops = parse_bool(value);
    } else if (key == "opt-tree-loop-vectorize") {
        rule.opts.tree_loop_vectorize = parse_bool(value);
    } else if (key == "opt-tree-slp-vectorize") {
        rule.opts.tree_slp_vectorize = parse_bool(value);
    } else if (key == "opt-tree-tail-merge") {
        rule.opts.tree_tail_merge = parse_bool(value);
    } else if (key == "opt-tree-loop-distribute-patterns") {
        rule.opts.tree_loop_distribute_patterns = parse_bool(value);
    } else if (key == "opt-branch-probabilities") {
        rule.opts.branch_probabilities = parse_bool(value);
    } else if (key == "opt-code-hoisting") {
        rule.opts.code_hoisting = parse_bool(value);
    }
}

bool is_valid_rule(const Rule &rule) {
    return (rule.type == "function" && !rule.function_name.empty()) || (rule.type == "file" && !rule.filename.empty());
}

std::vector<Rule>* parse_config_file(const std::string& filepath) {
    auto rules = new std::vector<Rule>();
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Failed to open optimizations config file!\n";
        return rules;
    }

    std::string line;
    Rule current_rule;

    while (std::getline(file, line)) {
        trim(line);

        if (line.empty()) {
            continue;
        }

        if (line == "---") {
            if (is_valid_rule(current_rule)) {
                rules->push_back(current_rule);
                current_rule = Rule();
            }
            continue;
        }

        std::string key, value;
        if (parse_key_value(line, key, value)) {
            apply_field(current_rule, key, value);
        }
    }

    if (is_valid_rule(current_rule)) {
        rules->push_back(current_rule);
    }

    file.close();
    return rules;
}
