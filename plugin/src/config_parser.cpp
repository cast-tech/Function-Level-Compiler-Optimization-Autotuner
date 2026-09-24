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
    } else if (key == "opt-aggressive-loop-optimizations") {
        rule.opts.opt_aggressive_loop_optimizations = parse_bool(value);
    } else if (key == "opt-align-functions") {
        rule.opts.opt_align_functions = parse_bool(value);
    } else if (key == "opt-align-jumps") {
        rule.opts.opt_align_jumps = parse_bool(value);
    } else if (key == "opt-align-labels") {
        rule.opts.opt_align_labels = parse_bool(value);
    } else if (key == "opt-align-loops") {
        rule.opts.opt_align_loops = parse_bool(value);
    } else if (key == "opt-allocation-dce") {
        rule.opts.opt_allocation_dce = parse_bool(value);
    } else if (key == "opt-allow-store-data-races") {
        rule.opts.opt_allow_store_data_races = parse_bool(value);
    } else if (key == "opt-asynchronous-unwind-tables") {
        rule.opts.opt_asynchronous_unwind_tables = parse_bool(value);
    } else if (key == "opt-auto-inc-dec") {
        rule.opts.opt_auto_inc_dec = parse_bool(value);
    } else if (key == "opt-avoid-store-forwarding") {
        rule.opts.opt_avoid_store_forwarding = parse_bool(value);
    } else if (key == "opt-bit-tests") {
        rule.opts.opt_bit_tests = parse_bool(value);
    } else if (key == "opt-branch-count-reg") {
        rule.opts.opt_branch_count_reg = parse_bool(value);
    } else if (key == "opt-branch-probabilities") {
        rule.opts.opt_branch_probabilities = parse_bool(value);
    } else if (key == "opt-caller-saves") {
        rule.opts.opt_caller_saves = parse_bool(value);
    } else if (key == "opt-code-hoisting") {
        rule.opts.opt_code_hoisting = parse_bool(value);
    } else if (key == "opt-combine-stack-adjustments") {
        rule.opts.opt_combine_stack_adjustments = parse_bool(value);
    } else if (key == "opt-compare-elim") {
        rule.opts.opt_compare_elim = parse_bool(value);
    } else if (key == "opt-conserve-stack") {
        rule.opts.opt_conserve_stack = parse_bool(value);
    } else if (key == "opt-cprop-registers") {
        rule.opts.opt_cprop_registers = parse_bool(value);
    } else if (key == "opt-crossjumping") {
        rule.opts.opt_crossjumping = parse_bool(value);
    } else if (key == "opt-cse-follow-jumps") {
        rule.opts.opt_cse_follow_jumps = parse_bool(value);
    } else if (key == "opt-cx-fortran-rules") {
        rule.opts.opt_cx_fortran_rules = parse_bool(value);
    } else if (key == "opt-cx-limited-range") {
        rule.opts.opt_cx_limited_range = parse_bool(value);
    } else if (key == "opt-dce") {
        rule.opts.opt_dce = parse_bool(value);
    } else if (key == "opt-defer-pop") {
        rule.opts.opt_defer_pop = parse_bool(value);
    } else if (key == "opt-delayed-branch") {
        rule.opts.opt_delayed_branch = parse_bool(value);
    } else if (key == "opt-delete-dead-exceptions") {
        rule.opts.opt_delete_dead_exceptions = parse_bool(value);
    } else if (key == "opt-delete-null-pointer-checks") {
        rule.opts.opt_delete_null_pointer_checks = parse_bool(value);
    } else if (key == "opt-devirtualize") {
        rule.opts.opt_devirtualize = parse_bool(value);
    } else if (key == "opt-devirtualize-speculatively") {
        rule.opts.opt_devirtualize_speculatively = parse_bool(value);
    } else if (key == "opt-dse") {
        rule.opts.opt_dse = parse_bool(value);
    } else if (key == "opt-early-inlining") {
        rule.opts.opt_early_inlining = parse_bool(value);
    } else if (key == "opt-expensive-optimizations") {
        rule.opts.opt_expensive_optimizations = parse_bool(value);
    } else if (key == "opt-ext-dce") {
        rule.opts.opt_ext_dce = parse_bool(value);
    } else if (key == "opt-finite-loops") {
        rule.opts.opt_finite_loops = parse_bool(value);
    } else if (key == "opt-finite-math-only") {
        rule.opts.opt_finite_math_only = parse_bool(value);
    } else if (key == "opt-float-store") {
        rule.opts.opt_float_store = parse_bool(value);
    } else if (key == "opt-fold-mem-offsets") {
        rule.opts.opt_fold_mem_offsets = parse_bool(value);
    } else if (key == "opt-forward-propagate") {
        rule.opts.opt_forward_propagate = parse_bool(value);
    } else if (key == "opt-fp-int-builtin-inexact") {
        rule.opts.opt_fp_int_builtin_inexact = parse_bool(value);
    } else if (key == "opt-function-cse") {
        rule.opts.opt_function_cse = parse_bool(value);
    } else if (key == "opt-gcse") {
        rule.opts.opt_gcse = parse_bool(value);
    } else if (key == "opt-gcse-after-reload") {
        rule.opts.opt_gcse_after_reload = parse_bool(value);
    } else if (key == "opt-gcse-las") {
        rule.opts.opt_gcse_las = parse_bool(value);
    } else if (key == "opt-gcse-lm") {
        rule.opts.opt_gcse_lm = parse_bool(value);
    } else if (key == "opt-gcse-sm") {
        rule.opts.opt_gcse_sm = parse_bool(value);
    } else if (key == "opt-graphite") {
        rule.opts.opt_graphite = parse_bool(value);
    } else if (key == "opt-graphite-identity") {
        rule.opts.opt_graphite_identity = parse_bool(value);
    } else if (key == "opt-guess-branch-probability") {
        rule.opts.opt_guess_branch_probability = parse_bool(value);
    } else if (key == "opt-hardcfr-check-exceptions") {
        rule.opts.opt_hardcfr_check_exceptions = parse_bool(value);
    } else if (key == "opt-hardcfr-check-returning-calls") {
        rule.opts.opt_hardcfr_check_returning_calls = parse_bool(value);
    } else if (key == "opt-hardcfr-skip-leaf") {
        rule.opts.opt_hardcfr_skip_leaf = parse_bool(value);
    } else if (key == "opt-harden-compares") {
        rule.opts.opt_harden_compares = parse_bool(value);
    } else if (key == "opt-harden-conditional-branches") {
        rule.opts.opt_harden_conditional_branches = parse_bool(value);
    } else if (key == "opt-harden-control-flow-redundancy") {
        rule.opts.opt_harden_control_flow_redundancy = parse_bool(value);
    } else if (key == "opt-hoist-adjacent-loads") {
        rule.opts.opt_hoist_adjacent_loads = parse_bool(value);
    } else if (key == "opt-if-conversion") {
        rule.opts.opt_if_conversion = parse_bool(value);
    } else if (key == "opt-if-conversion2") {
        rule.opts.opt_if_conversion2 = parse_bool(value);
    } else if (key == "opt-indirect-inlining") {
        rule.opts.opt_indirect_inlining = parse_bool(value);
    } else if (key == "opt-inline") {
        rule.opts.opt_inline = parse_bool(value);
    } else if (key == "opt-inline-atomics") {
        rule.opts.opt_inline_atomics = parse_bool(value);
    } else if (key == "opt-inline-functions") {
        rule.opts.opt_inline_functions = parse_bool(value);
    } else if (key == "opt-inline-functions-called-once") {
        rule.opts.opt_inline_functions_called_once = parse_bool(value);
    } else if (key == "opt-inline-small-functions") {
        rule.opts.opt_inline_small_functions = parse_bool(value);
    } else if (key == "opt-ipa-bit-cp") {
        rule.opts.opt_ipa_bit_cp = parse_bool(value);
    } else if (key == "opt-ipa-cp") {
        rule.opts.opt_ipa_cp = parse_bool(value);
    } else if (key == "opt-ipa-cp-clone") {
        rule.opts.opt_ipa_cp_clone = parse_bool(value);
    } else if (key == "opt-ipa-icf") {
        rule.opts.opt_ipa_icf = parse_bool(value);
    } else if (key == "opt-ipa-icf-functions") {
        rule.opts.opt_ipa_icf_functions = parse_bool(value);
    } else if (key == "opt-ipa-icf-variables") {
        rule.opts.opt_ipa_icf_variables = parse_bool(value);
    } else if (key == "opt-ipa-modref") {
        rule.opts.opt_ipa_modref = parse_bool(value);
    } else if (key == "opt-ipa-profile") {
        rule.opts.opt_ipa_profile = parse_bool(value);
    } else if (key == "opt-ipa-pta") {
        rule.opts.opt_ipa_pta = parse_bool(value);
    } else if (key == "opt-ipa-pure-const") {
        rule.opts.opt_ipa_pure_const = parse_bool(value);
    } else if (key == "opt-ipa-ra") {
        rule.opts.opt_ipa_ra = parse_bool(value);
    } else if (key == "opt-ipa-reference") {
        rule.opts.opt_ipa_reference = parse_bool(value);
    } else if (key == "opt-ipa-reference-addressable") {
        rule.opts.opt_ipa_reference_addressable = parse_bool(value);
    } else if (key == "opt-ipa-reorder-for-locality") {
        rule.opts.opt_ipa_reorder_for_locality = parse_bool(value);
    } else if (key == "opt-ipa-sra") {
        rule.opts.opt_ipa_sra = parse_bool(value);
    } else if (key == "opt-ipa-stack-alignment") {
        rule.opts.opt_ipa_stack_alignment = parse_bool(value);
    } else if (key == "opt-ipa-strict-aliasing") {
        rule.opts.opt_ipa_strict_aliasing = parse_bool(value);
    } else if (key == "opt-ipa-vrp") {
        rule.opts.opt_ipa_vrp = parse_bool(value);
    } else if (key == "opt-ira-hoist-pressure") {
        rule.opts.opt_ira_hoist_pressure = parse_bool(value);
    } else if (key == "opt-ira-loop-pressure") {
        rule.opts.opt_ira_loop_pressure = parse_bool(value);
    } else if (key == "opt-ira-share-save-slots") {
        rule.opts.opt_ira_share_save_slots = parse_bool(value);
    } else if (key == "opt-ira-share-spill-slots") {
        rule.opts.opt_ira_share_spill_slots = parse_bool(value);
    } else if (key == "opt-isolate-erroneous-paths-attribute") {
        rule.opts.opt_isolate_erroneous_paths_attribute = parse_bool(value);
    } else if (key == "opt-isolate-erroneous-paths-dereference") {
        rule.opts.opt_isolate_erroneous_paths_dereference = parse_bool(value);
    } else if (key == "opt-ivopts") {
        rule.opts.opt_ivopts = parse_bool(value);
    } else if (key == "opt-jump-tables") {
        rule.opts.opt_jump_tables = parse_bool(value);
    } else if (key == "opt-keep-gc-roots-live") {
        rule.opts.opt_keep_gc_roots_live = parse_bool(value);
    } else if (key == "opt-late-combine-instructions") {
        rule.opts.opt_late_combine_instructions = parse_bool(value);
    } else if (key == "opt-lifetime-dse") {
        rule.opts.opt_lifetime_dse = parse_bool(value);
    } else if (key == "opt-limit-function-alignment") {
        rule.opts.opt_limit_function_alignment = parse_bool(value);
    } else if (key == "opt-live-range-shrinkage") {
        rule.opts.opt_live_range_shrinkage = parse_bool(value);
    } else if (key == "opt-loop-interchange") {
        rule.opts.opt_loop_interchange = parse_bool(value);
    } else if (key == "opt-loop-nest-optimize") {
        rule.opts.opt_loop_nest_optimize = parse_bool(value);
    } else if (key == "opt-loop-parallelize-all") {
        rule.opts.opt_loop_parallelize_all = parse_bool(value);
    } else if (key == "opt-loop-unroll-and-jam") {
        rule.opts.opt_loop_unroll_and_jam = parse_bool(value);
    } else if (key == "opt-lra-remat") {
        rule.opts.opt_lra_remat = parse_bool(value);
    } else if (key == "opt-malloc-dce") {
        rule.opts.opt_malloc_dce = parse_bool(value);
    } else if (key == "opt-math-errno") {
        rule.opts.opt_math_errno = parse_bool(value);
    } else if (key == "opt-modulo-sched") {
        rule.opts.opt_modulo_sched = parse_bool(value);
    } else if (key == "opt-modulo-sched-allow-regmoves") {
        rule.opts.opt_modulo_sched_allow_regmoves = parse_bool(value);
    } else if (key == "opt-move-loop-invariants") {
        rule.opts.opt_move_loop_invariants = parse_bool(value);
    } else if (key == "opt-move-loop-stores") {
        rule.opts.opt_move_loop_stores = parse_bool(value);
    } else if (key == "opt-no-inline-stringops") {
        rule.opts.opt_no_inline_stringops = parse_bool(value);
    } else if (key == "opt-non-call-exceptions") {
        rule.opts.opt_non_call_exceptions = parse_bool(value);
    } else if (key == "opt-omit-frame-pointer") {
        rule.opts.opt_omit_frame_pointer = parse_bool(value);
    } else if (key == "opt-opt-info") {
        rule.opts.opt_opt_info = parse_bool(value);
    } else if (key == "opt-optimize-crc") {
        rule.opts.opt_optimize_crc = parse_bool(value);
    } else if (key == "opt-optimize-sibling-calls") {
        rule.opts.opt_optimize_sibling_calls = parse_bool(value);
    } else if (key == "opt-optimize-strlen") {
        rule.opts.opt_optimize_strlen = parse_bool(value);
    } else if (key == "opt-pack-struct") {
        rule.opts.opt_pack_struct = parse_bool(value);
    } else if (key == "opt-partial-inlining") {
        rule.opts.opt_partial_inlining = parse_bool(value);
    } else if (key == "opt-pcc-struct-return") {
        rule.opts.opt_pcc_struct_return = parse_bool(value);
    } else if (key == "opt-peel-loops") {
        rule.opts.opt_peel_loops = parse_bool(value);
    } else if (key == "opt-peephole") {
        rule.opts.opt_peephole = parse_bool(value);
    } else if (key == "opt-peephole2") {
        rule.opts.opt_peephole2 = parse_bool(value);
    } else if (key == "opt-plt") {
        rule.opts.opt_plt = parse_bool(value);
    } else if (key == "opt-predictive-commoning") {
        rule.opts.opt_predictive_commoning = parse_bool(value);
    } else if (key == "opt-prefetch-loop-arrays") {
        rule.opts.opt_prefetch_loop_arrays = parse_bool(value);
    } else if (key == "opt-printf-return-value") {
        rule.opts.opt_printf_return_value = parse_bool(value);
    } else if (key == "opt-profile-partial-training") {
        rule.opts.opt_profile_partial_training = parse_bool(value);
    } else if (key == "opt-profile-reorder-functions") {
        rule.opts.opt_profile_reorder_functions = parse_bool(value);
    } else if (key == "opt-reciprocal-math") {
        rule.opts.opt_reciprocal_math = parse_bool(value);
    } else if (key == "opt-ree") {
        rule.opts.opt_ree = parse_bool(value);
    } else if (key == "opt-rename-registers") {
        rule.opts.opt_rename_registers = parse_bool(value);
    } else if (key == "opt-reorder-blocks") {
        rule.opts.opt_reorder_blocks = parse_bool(value);
    } else if (key == "opt-reorder-blocks-and-partition") {
        rule.opts.opt_reorder_blocks_and_partition = parse_bool(value);
    } else if (key == "opt-reorder-functions") {
        rule.opts.opt_reorder_functions = parse_bool(value);
    } else if (key == "opt-rerun-cse-after-loop") {
        rule.opts.opt_rerun_cse_after_loop = parse_bool(value);
    } else if (key == "opt-reschedule-modulo-scheduled-loops") {
        rule.opts.opt_reschedule_modulo_scheduled_loops = parse_bool(value);
    } else if (key == "opt-rounding-math") {
        rule.opts.opt_rounding_math = parse_bool(value);
    } else if (key == "opt-save-optimization-record") {
        rule.opts.opt_save_optimization_record = parse_bool(value);
    } else if (key == "opt-sched-critical-path-heuristic") {
        rule.opts.opt_sched_critical_path_heuristic = parse_bool(value);
    } else if (key == "opt-sched-dep-count-heuristic") {
        rule.opts.opt_sched_dep_count_heuristic = parse_bool(value);
    } else if (key == "opt-sched-group-heuristic") {
        rule.opts.opt_sched_group_heuristic = parse_bool(value);
    } else if (key == "opt-sched-interblock") {
        rule.opts.opt_sched_interblock = parse_bool(value);
    } else if (key == "opt-sched-last-insn-heuristic") {
        rule.opts.opt_sched_last_insn_heuristic = parse_bool(value);
    } else if (key == "opt-sched-pressure") {
        rule.opts.opt_sched_pressure = parse_bool(value);
    } else if (key == "opt-sched-rank-heuristic") {
        rule.opts.opt_sched_rank_heuristic = parse_bool(value);
    } else if (key == "opt-sched-spec") {
        rule.opts.opt_sched_spec = parse_bool(value);
    } else if (key == "opt-sched-spec-insn-heuristic") {
        rule.opts.opt_sched_spec_insn_heuristic = parse_bool(value);
    } else if (key == "opt-sched-spec-load") {
        rule.opts.opt_sched_spec_load = parse_bool(value);
    } else if (key == "opt-sched-spec-load-dangerous") {
        rule.opts.opt_sched_spec_load_dangerous = parse_bool(value);
    } else if (key == "opt-sched-stalled-insns") {
        rule.opts.opt_sched_stalled_insns = parse_bool(value);
    } else if (key == "opt-sched-stalled-insns-dep") {
        rule.opts.opt_sched_stalled_insns_dep = parse_bool(value);
    } else if (key == "opt-sched2-use-superblocks") {
        rule.opts.opt_sched2_use_superblocks = parse_bool(value);
    } else if (key == "opt-schedule-fusion") {
        rule.opts.opt_schedule_fusion = parse_bool(value);
    } else if (key == "opt-schedule-insns") {
        rule.opts.opt_schedule_insns = parse_bool(value);
    } else if (key == "opt-schedule-insns2") {
        rule.opts.opt_schedule_insns2 = parse_bool(value);
    } else if (key == "opt-section-anchors") {
        rule.opts.opt_section_anchors = parse_bool(value);
    } else if (key == "opt-sel-sched-pipelining") {
        rule.opts.opt_sel_sched_pipelining = parse_bool(value);
    } else if (key == "opt-sel-sched-pipelining-outer-loops") {
        rule.opts.opt_sel_sched_pipelining_outer_loops = parse_bool(value);
    } else if (key == "opt-sel-sched-reschedule-pipelined") {
        rule.opts.opt_sel_sched_reschedule_pipelined = parse_bool(value);
    } else if (key == "opt-selective-scheduling") {
        rule.opts.opt_selective_scheduling = parse_bool(value);
    } else if (key == "opt-selective-scheduling2") {
        rule.opts.opt_selective_scheduling2 = parse_bool(value);
    } else if (key == "opt-semantic-interposition") {
        rule.opts.opt_semantic_interposition = parse_bool(value);
    } else if (key == "opt-short-enums") {
        rule.opts.opt_short_enums = parse_bool(value);
    } else if (key == "opt-short-wchar") {
        rule.opts.opt_short_wchar = parse_bool(value);
    } else if (key == "opt-shrink-wrap") {
        rule.opts.opt_shrink_wrap = parse_bool(value);
    } else if (key == "opt-shrink-wrap-separate") {
        rule.opts.opt_shrink_wrap_separate = parse_bool(value);
    } else if (key == "opt-signaling-nans") {
        rule.opts.opt_signaling_nans = parse_bool(value);
    } else if (key == "opt-signed-zeros") {
        rule.opts.opt_signed_zeros = parse_bool(value);
    } else if (key == "opt-single-precision-constant") {
        rule.opts.opt_single_precision_constant = parse_bool(value);
    } else if (key == "opt-split-ivs-in-unroller") {
        rule.opts.opt_split_ivs_in_unroller = parse_bool(value);
    } else if (key == "opt-split-loops") {
        rule.opts.opt_split_loops = parse_bool(value);
    } else if (key == "opt-split-paths") {
        rule.opts.opt_split_paths = parse_bool(value);
    } else if (key == "opt-split-wide-types") {
        rule.opts.opt_split_wide_types = parse_bool(value);
    } else if (key == "opt-split-wide-types-early") {
        rule.opts.opt_split_wide_types_early = parse_bool(value);
    } else if (key == "opt-ssa-backprop") {
        rule.opts.opt_ssa_backprop = parse_bool(value);
    } else if (key == "opt-ssa-phiopt") {
        rule.opts.opt_ssa_phiopt = parse_bool(value);
    } else if (key == "opt-stack-clash-protection") {
        rule.opts.opt_stack_clash_protection = parse_bool(value);
    } else if (key == "opt-stack-protector") {
        rule.opts.opt_stack_protector = parse_bool(value);
    } else if (key == "opt-stdarg-opt") {
        rule.opts.opt_stdarg_opt = parse_bool(value);
    } else if (key == "opt-store-merging") {
        rule.opts.opt_store_merging = parse_bool(value);
    } else if (key == "opt-strict-aliasing") {
        rule.opts.opt_strict_aliasing = parse_bool(value);
    } else if (key == "opt-strict-volatile-bitfields") {
        rule.opts.opt_strict_volatile_bitfields = parse_bool(value);
    } else if (key == "opt-thread-jumps") {
        rule.opts.opt_thread_jumps = parse_bool(value);
    } else if (key == "opt-toplevel-reorder") {
        rule.opts.opt_toplevel_reorder = parse_bool(value);
    } else if (key == "opt-tracer") {
        rule.opts.opt_tracer = parse_bool(value);
    } else if (key == "opt-trapping-math") {
        rule.opts.opt_trapping_math = parse_bool(value);
    } else if (key == "opt-trapv") {
        rule.opts.opt_trapv = parse_bool(value);
    } else if (key == "opt-tree-bit-ccp") {
        rule.opts.opt_tree_bit_ccp = parse_bool(value);
    } else if (key == "opt-tree-builtin-call-dce") {
        rule.opts.opt_tree_builtin_call_dce = parse_bool(value);
    } else if (key == "opt-tree-ccp") {
        rule.opts.opt_tree_ccp = parse_bool(value);
    } else if (key == "opt-tree-ch") {
        rule.opts.opt_tree_ch = parse_bool(value);
    } else if (key == "opt-tree-coalesce-vars") {
        rule.opts.opt_tree_coalesce_vars = parse_bool(value);
    } else if (key == "opt-tree-copy-prop") {
        rule.opts.opt_tree_copy_prop = parse_bool(value);
    } else if (key == "opt-tree-cselim") {
        rule.opts.opt_tree_cselim = parse_bool(value);
    } else if (key == "opt-tree-dce") {
        rule.opts.opt_tree_dce = parse_bool(value);
    } else if (key == "opt-tree-dominator-opts") {
        rule.opts.opt_tree_dominator_opts = parse_bool(value);
    } else if (key == "opt-tree-dse") {
        rule.opts.opt_tree_dse = parse_bool(value);
    } else if (key == "opt-tree-forwprop") {
        rule.opts.opt_tree_forwprop = parse_bool(value);
    } else if (key == "opt-tree-fre") {
        rule.opts.opt_tree_fre = parse_bool(value);
    } else if (key == "opt-tree-loop-distribute-patterns") {
        rule.opts.opt_tree_loop_distribute_patterns = parse_bool(value);
    } else if (key == "opt-tree-loop-distribution") {
        rule.opts.opt_tree_loop_distribution = parse_bool(value);
    } else if (key == "opt-tree-loop-if-convert") {
        rule.opts.opt_tree_loop_if_convert = parse_bool(value);
    } else if (key == "opt-tree-loop-im") {
        rule.opts.opt_tree_loop_im = parse_bool(value);
    } else if (key == "opt-tree-loop-ivcanon") {
        rule.opts.opt_tree_loop_ivcanon = parse_bool(value);
    } else if (key == "opt-tree-loop-optimize") {
        rule.opts.opt_tree_loop_optimize = parse_bool(value);
    } else if (key == "opt-tree-loop-vectorize") {
        rule.opts.opt_tree_loop_vectorize = parse_bool(value);
    } else if (key == "opt-tree-lrs") {
        rule.opts.opt_tree_lrs = parse_bool(value);
    } else if (key == "opt-tree-partial-pre") {
        rule.opts.opt_tree_partial_pre = parse_bool(value);
    } else if (key == "opt-tree-phiprop") {
        rule.opts.opt_tree_phiprop = parse_bool(value);
    } else if (key == "opt-tree-pre") {
        rule.opts.opt_tree_pre = parse_bool(value);
    } else if (key == "opt-tree-pta") {
        rule.opts.opt_tree_pta = parse_bool(value);
    } else if (key == "opt-tree-reassoc") {
        rule.opts.opt_tree_reassoc = parse_bool(value);
    } else if (key == "opt-tree-scev-cprop") {
        rule.opts.opt_tree_scev_cprop = parse_bool(value);
    } else if (key == "opt-tree-sink") {
        rule.opts.opt_tree_sink = parse_bool(value);
    } else if (key == "opt-tree-slp-vectorize") {
        rule.opts.opt_tree_slp_vectorize = parse_bool(value);
    } else if (key == "opt-tree-slsr") {
        rule.opts.opt_tree_slsr = parse_bool(value);
    } else if (key == "opt-tree-sra") {
        rule.opts.opt_tree_sra = parse_bool(value);
    } else if (key == "opt-tree-switch-conversion") {
        rule.opts.opt_tree_switch_conversion = parse_bool(value);
    } else if (key == "opt-tree-tail-merge") {
        rule.opts.opt_tree_tail_merge = parse_bool(value);
    } else if (key == "opt-tree-ter") {
        rule.opts.opt_tree_ter = parse_bool(value);
    } else if (key == "opt-tree-vectorize") {
        rule.opts.opt_tree_vectorize = parse_bool(value);
    } else if (key == "opt-tree-vrp") {
        rule.opts.opt_tree_vrp = parse_bool(value);
    } else if (key == "opt-unconstrained-commons") {
        rule.opts.opt_unconstrained_commons = parse_bool(value);
    } else if (key == "opt-unreachable-traps") {
        rule.opts.opt_unreachable_traps = parse_bool(value);
    } else if (key == "opt-unroll-all-loops") {
        rule.opts.opt_unroll_all_loops = parse_bool(value);
    } else if (key == "opt-unroll-completely-grow-size") {
        rule.opts.opt_unroll_completely_grow_size = parse_bool(value);
    } else if (key == "opt-unroll-loops") {
        rule.opts.opt_unroll_loops = parse_bool(value);
    } else if (key == "opt-unsafe-math-optimizations") {
        rule.opts.opt_unsafe_math_optimizations = parse_bool(value);
    } else if (key == "opt-unswitch-loops") {
        rule.opts.opt_unswitch_loops = parse_bool(value);
    } else if (key == "opt-unwind-tables") {
        rule.opts.opt_unwind_tables = parse_bool(value);
    } else if (key == "opt-var-tracking") {
        rule.opts.opt_var_tracking = parse_bool(value);
    } else if (key == "opt-var-tracking-assignments") {
        rule.opts.opt_var_tracking_assignments = parse_bool(value);
    } else if (key == "opt-var-tracking-assignments-toggle") {
        rule.opts.opt_var_tracking_assignments_toggle = parse_bool(value);
    } else if (key == "opt-var-tracking-uninit") {
        rule.opts.opt_var_tracking_uninit = parse_bool(value);
    } else if (key == "opt-variable-expansion-in-unroller") {
        rule.opts.opt_variable_expansion_in_unroller = parse_bool(value);
    } else if (key == "opt-version-loops-for-strides") {
        rule.opts.opt_version_loops_for_strides = parse_bool(value);
    } else if (key == "opt-vpt") {
        rule.opts.opt_vpt = parse_bool(value);
    } else if (key == "opt-web") {
        rule.opts.opt_web = parse_bool(value);
    } else if (key == "opt-wrapv") {
        rule.opts.opt_wrapv = parse_bool(value);
    } else if (key == "opt-wrapv-pointer") {
        rule.opts.opt_wrapv_pointer = parse_bool(value);
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
