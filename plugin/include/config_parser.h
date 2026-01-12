#ifndef DEFINITION_CONFIG_PARSER_H
#define DEFINITION_CONFIG_PARSER_H

#include <string>
#include <vector>

constexpr unsigned int OPTIMIZATION_SET_DEFAULT = 0;
constexpr unsigned int OPTIMIZATION_SET_ON = 1;
constexpr unsigned int OPTIMIZATION_SET_OFF = 2;

struct Optimizations {
    unsigned int level : 2;
    unsigned int selective_scheduling : 2;
    unsigned int selective_scheduling2 : 2;
    unsigned int schedule_insns : 2;
    unsigned int schedule_insns2 : 2;
    unsigned int sched_interblock : 2;
    unsigned int unroll_loops : 2;
    unsigned int peel_loops : 2;
    unsigned int unswitch_loops : 2;
    unsigned int tree_loop_vectorize : 2;
    unsigned int tree_slp_vectorize : 2;
    unsigned int tree_tail_merge : 2;
    unsigned int tree_loop_distribute_patterns : 2;
    unsigned int branch_probabilities : 2;
    unsigned int code_hoisting : 2;
};

struct Rule {
    std::string type;
    std::string function_name;
    std::string filename;
    int line_number = -1;
    Optimizations opts{};
};

std::vector<Rule> *parse_config_file(const std::string &filepath);

#endif // DEFINITION_CONFIG_PARSER_H
