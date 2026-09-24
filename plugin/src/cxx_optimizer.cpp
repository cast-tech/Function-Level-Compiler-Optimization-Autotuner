#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cstdarg>
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

// --- debug logging (opt-in) ----------------------------------------------------
// GCC's stderr is swallowed by the Python builders during tuning, so when
// CXX_OPTIMIZER_DEBUG_LOG names a file we append there; otherwise CXX_OPTIMIZER_DEBUG
// (any value) sends diagnostics to stderr. Unset => zero overhead, no output.
static FILE *cxx_dbg_stream() {
    static bool initialized = false;
    static FILE *stream = nullptr;
    if (!initialized) {
        initialized = true;
        const char *path = getenv("CXX_OPTIMIZER_DEBUG_LOG");
        if (path && path[0]) {
            stream = fopen(path, "a");
        } else if (getenv("CXX_OPTIMIZER_DEBUG")) {
            stream = stderr;
        }
    }
    return stream;
}

static void cxx_dbg(const char *fmt, ...) {
    FILE *s = cxx_dbg_stream();
    if (!s) return;
    va_list ap;
    va_start(ap, fmt);
    vfprintf(s, fmt, ap);
    va_end(ap);
    fputc('\n', s);
    fflush(s);
}

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

    append_to_attribute_stream(oss, opts.opt_aggressive_loop_optimizations, "aggressive-loop-optimizations");
    append_to_attribute_stream(oss, opts.opt_align_functions, "align-functions");
    append_to_attribute_stream(oss, opts.opt_align_jumps, "align-jumps");
    append_to_attribute_stream(oss, opts.opt_align_labels, "align-labels");
    append_to_attribute_stream(oss, opts.opt_align_loops, "align-loops");
    append_to_attribute_stream(oss, opts.opt_allocation_dce, "allocation-dce");
    append_to_attribute_stream(oss, opts.opt_allow_store_data_races, "allow-store-data-races");
    append_to_attribute_stream(oss, opts.opt_asynchronous_unwind_tables, "asynchronous-unwind-tables");
    append_to_attribute_stream(oss, opts.opt_auto_inc_dec, "auto-inc-dec");
    append_to_attribute_stream(oss, opts.opt_avoid_store_forwarding, "avoid-store-forwarding");
    append_to_attribute_stream(oss, opts.opt_bit_tests, "bit-tests");
    append_to_attribute_stream(oss, opts.opt_branch_count_reg, "branch-count-reg");
    append_to_attribute_stream(oss, opts.opt_branch_probabilities, "branch-probabilities");
    append_to_attribute_stream(oss, opts.opt_caller_saves, "caller-saves");
    append_to_attribute_stream(oss, opts.opt_code_hoisting, "code-hoisting");
    append_to_attribute_stream(oss, opts.opt_combine_stack_adjustments, "combine-stack-adjustments");
    append_to_attribute_stream(oss, opts.opt_compare_elim, "compare-elim");
    append_to_attribute_stream(oss, opts.opt_conserve_stack, "conserve-stack");
    append_to_attribute_stream(oss, opts.opt_cprop_registers, "cprop-registers");
    append_to_attribute_stream(oss, opts.opt_crossjumping, "crossjumping");
    append_to_attribute_stream(oss, opts.opt_cse_follow_jumps, "cse-follow-jumps");
    append_to_attribute_stream(oss, opts.opt_cx_fortran_rules, "cx-fortran-rules");
    append_to_attribute_stream(oss, opts.opt_cx_limited_range, "cx-limited-range");
    append_to_attribute_stream(oss, opts.opt_dce, "dce");
    append_to_attribute_stream(oss, opts.opt_defer_pop, "defer-pop");
    append_to_attribute_stream(oss, opts.opt_delayed_branch, "delayed-branch");
    append_to_attribute_stream(oss, opts.opt_delete_dead_exceptions, "delete-dead-exceptions");
    append_to_attribute_stream(oss, opts.opt_delete_null_pointer_checks, "delete-null-pointer-checks");
    append_to_attribute_stream(oss, opts.opt_devirtualize, "devirtualize");
    append_to_attribute_stream(oss, opts.opt_devirtualize_speculatively, "devirtualize-speculatively");
    append_to_attribute_stream(oss, opts.opt_dse, "dse");
    append_to_attribute_stream(oss, opts.opt_early_inlining, "early-inlining");
    append_to_attribute_stream(oss, opts.opt_expensive_optimizations, "expensive-optimizations");
    append_to_attribute_stream(oss, opts.opt_ext_dce, "ext-dce");
    append_to_attribute_stream(oss, opts.opt_finite_loops, "finite-loops");
    append_to_attribute_stream(oss, opts.opt_finite_math_only, "finite-math-only");
    append_to_attribute_stream(oss, opts.opt_float_store, "float-store");
    append_to_attribute_stream(oss, opts.opt_fold_mem_offsets, "fold-mem-offsets");
    append_to_attribute_stream(oss, opts.opt_forward_propagate, "forward-propagate");
    append_to_attribute_stream(oss, opts.opt_fp_int_builtin_inexact, "fp-int-builtin-inexact");
    append_to_attribute_stream(oss, opts.opt_function_cse, "function-cse");
    append_to_attribute_stream(oss, opts.opt_gcse, "gcse");
    append_to_attribute_stream(oss, opts.opt_gcse_after_reload, "gcse-after-reload");
    append_to_attribute_stream(oss, opts.opt_gcse_las, "gcse-las");
    append_to_attribute_stream(oss, opts.opt_gcse_lm, "gcse-lm");
    append_to_attribute_stream(oss, opts.opt_gcse_sm, "gcse-sm");
    append_to_attribute_stream(oss, opts.opt_graphite, "graphite");
    append_to_attribute_stream(oss, opts.opt_graphite_identity, "graphite-identity");
    append_to_attribute_stream(oss, opts.opt_guess_branch_probability, "guess-branch-probability");
    append_to_attribute_stream(oss, opts.opt_hardcfr_check_exceptions, "hardcfr-check-exceptions");
    append_to_attribute_stream(oss, opts.opt_hardcfr_check_returning_calls, "hardcfr-check-returning-calls");
    append_to_attribute_stream(oss, opts.opt_hardcfr_skip_leaf, "hardcfr-skip-leaf");
    append_to_attribute_stream(oss, opts.opt_harden_compares, "harden-compares");
    append_to_attribute_stream(oss, opts.opt_harden_conditional_branches, "harden-conditional-branches");
    append_to_attribute_stream(oss, opts.opt_harden_control_flow_redundancy, "harden-control-flow-redundancy");
    append_to_attribute_stream(oss, opts.opt_hoist_adjacent_loads, "hoist-adjacent-loads");
    append_to_attribute_stream(oss, opts.opt_if_conversion, "if-conversion");
    append_to_attribute_stream(oss, opts.opt_if_conversion2, "if-conversion2");
    append_to_attribute_stream(oss, opts.opt_indirect_inlining, "indirect-inlining");
    append_to_attribute_stream(oss, opts.opt_inline, "inline");
    append_to_attribute_stream(oss, opts.opt_inline_atomics, "inline-atomics");
    append_to_attribute_stream(oss, opts.opt_inline_functions, "inline-functions");
    append_to_attribute_stream(oss, opts.opt_inline_functions_called_once, "inline-functions-called-once");
    append_to_attribute_stream(oss, opts.opt_inline_small_functions, "inline-small-functions");
    append_to_attribute_stream(oss, opts.opt_ipa_bit_cp, "ipa-bit-cp");
    append_to_attribute_stream(oss, opts.opt_ipa_cp, "ipa-cp");
    append_to_attribute_stream(oss, opts.opt_ipa_cp_clone, "ipa-cp-clone");
    append_to_attribute_stream(oss, opts.opt_ipa_icf, "ipa-icf");
    append_to_attribute_stream(oss, opts.opt_ipa_icf_functions, "ipa-icf-functions");
    append_to_attribute_stream(oss, opts.opt_ipa_icf_variables, "ipa-icf-variables");
    append_to_attribute_stream(oss, opts.opt_ipa_modref, "ipa-modref");
    append_to_attribute_stream(oss, opts.opt_ipa_profile, "ipa-profile");
    append_to_attribute_stream(oss, opts.opt_ipa_pta, "ipa-pta");
    append_to_attribute_stream(oss, opts.opt_ipa_pure_const, "ipa-pure-const");
    append_to_attribute_stream(oss, opts.opt_ipa_ra, "ipa-ra");
    append_to_attribute_stream(oss, opts.opt_ipa_reference, "ipa-reference");
    append_to_attribute_stream(oss, opts.opt_ipa_reference_addressable, "ipa-reference-addressable");
    append_to_attribute_stream(oss, opts.opt_ipa_reorder_for_locality, "ipa-reorder-for-locality");
    append_to_attribute_stream(oss, opts.opt_ipa_sra, "ipa-sra");
    append_to_attribute_stream(oss, opts.opt_ipa_stack_alignment, "ipa-stack-alignment");
    append_to_attribute_stream(oss, opts.opt_ipa_strict_aliasing, "ipa-strict-aliasing");
    append_to_attribute_stream(oss, opts.opt_ipa_vrp, "ipa-vrp");
    append_to_attribute_stream(oss, opts.opt_ira_hoist_pressure, "ira-hoist-pressure");
    append_to_attribute_stream(oss, opts.opt_ira_loop_pressure, "ira-loop-pressure");
    append_to_attribute_stream(oss, opts.opt_ira_share_save_slots, "ira-share-save-slots");
    append_to_attribute_stream(oss, opts.opt_ira_share_spill_slots, "ira-share-spill-slots");
    append_to_attribute_stream(oss, opts.opt_isolate_erroneous_paths_attribute, "isolate-erroneous-paths-attribute");
    append_to_attribute_stream(oss, opts.opt_isolate_erroneous_paths_dereference, "isolate-erroneous-paths-dereference");
    append_to_attribute_stream(oss, opts.opt_ivopts, "ivopts");
    append_to_attribute_stream(oss, opts.opt_jump_tables, "jump-tables");
    append_to_attribute_stream(oss, opts.opt_keep_gc_roots_live, "keep-gc-roots-live");
    append_to_attribute_stream(oss, opts.opt_late_combine_instructions, "late-combine-instructions");
    append_to_attribute_stream(oss, opts.opt_lifetime_dse, "lifetime-dse");
    append_to_attribute_stream(oss, opts.opt_limit_function_alignment, "limit-function-alignment");
    append_to_attribute_stream(oss, opts.opt_live_range_shrinkage, "live-range-shrinkage");
    append_to_attribute_stream(oss, opts.opt_loop_interchange, "loop-interchange");
    append_to_attribute_stream(oss, opts.opt_loop_nest_optimize, "loop-nest-optimize");
    append_to_attribute_stream(oss, opts.opt_loop_parallelize_all, "loop-parallelize-all");
    append_to_attribute_stream(oss, opts.opt_loop_unroll_and_jam, "loop-unroll-and-jam");
    append_to_attribute_stream(oss, opts.opt_lra_remat, "lra-remat");
    append_to_attribute_stream(oss, opts.opt_malloc_dce, "malloc-dce");
    append_to_attribute_stream(oss, opts.opt_math_errno, "math-errno");
    append_to_attribute_stream(oss, opts.opt_modulo_sched, "modulo-sched");
    append_to_attribute_stream(oss, opts.opt_modulo_sched_allow_regmoves, "modulo-sched-allow-regmoves");
    append_to_attribute_stream(oss, opts.opt_move_loop_invariants, "move-loop-invariants");
    append_to_attribute_stream(oss, opts.opt_move_loop_stores, "move-loop-stores");
    append_to_attribute_stream(oss, opts.opt_no_inline_stringops, "no-inline-stringops");
    append_to_attribute_stream(oss, opts.opt_non_call_exceptions, "non-call-exceptions");
    append_to_attribute_stream(oss, opts.opt_omit_frame_pointer, "omit-frame-pointer");
    append_to_attribute_stream(oss, opts.opt_opt_info, "opt-info");
    append_to_attribute_stream(oss, opts.opt_optimize_crc, "optimize-crc");
    append_to_attribute_stream(oss, opts.opt_optimize_sibling_calls, "optimize-sibling-calls");
    append_to_attribute_stream(oss, opts.opt_optimize_strlen, "optimize-strlen");
    append_to_attribute_stream(oss, opts.opt_pack_struct, "pack-struct");
    append_to_attribute_stream(oss, opts.opt_partial_inlining, "partial-inlining");
    append_to_attribute_stream(oss, opts.opt_pcc_struct_return, "pcc-struct-return");
    append_to_attribute_stream(oss, opts.opt_peel_loops, "peel-loops");
    append_to_attribute_stream(oss, opts.opt_peephole, "peephole");
    append_to_attribute_stream(oss, opts.opt_peephole2, "peephole2");
    append_to_attribute_stream(oss, opts.opt_plt, "plt");
    append_to_attribute_stream(oss, opts.opt_predictive_commoning, "predictive-commoning");
    append_to_attribute_stream(oss, opts.opt_prefetch_loop_arrays, "prefetch-loop-arrays");
    append_to_attribute_stream(oss, opts.opt_printf_return_value, "printf-return-value");
    append_to_attribute_stream(oss, opts.opt_profile_partial_training, "profile-partial-training");
    append_to_attribute_stream(oss, opts.opt_profile_reorder_functions, "profile-reorder-functions");
    append_to_attribute_stream(oss, opts.opt_reciprocal_math, "reciprocal-math");
    append_to_attribute_stream(oss, opts.opt_ree, "ree");
    append_to_attribute_stream(oss, opts.opt_rename_registers, "rename-registers");
    append_to_attribute_stream(oss, opts.opt_reorder_blocks, "reorder-blocks");
    append_to_attribute_stream(oss, opts.opt_reorder_blocks_and_partition, "reorder-blocks-and-partition");
    append_to_attribute_stream(oss, opts.opt_reorder_functions, "reorder-functions");
    append_to_attribute_stream(oss, opts.opt_rerun_cse_after_loop, "rerun-cse-after-loop");
    append_to_attribute_stream(oss, opts.opt_reschedule_modulo_scheduled_loops, "reschedule-modulo-scheduled-loops");
    append_to_attribute_stream(oss, opts.opt_rounding_math, "rounding-math");
    append_to_attribute_stream(oss, opts.opt_save_optimization_record, "save-optimization-record");
    append_to_attribute_stream(oss, opts.opt_sched_critical_path_heuristic, "sched-critical-path-heuristic");
    append_to_attribute_stream(oss, opts.opt_sched_dep_count_heuristic, "sched-dep-count-heuristic");
    append_to_attribute_stream(oss, opts.opt_sched_group_heuristic, "sched-group-heuristic");
    append_to_attribute_stream(oss, opts.opt_sched_interblock, "sched-interblock");
    append_to_attribute_stream(oss, opts.opt_sched_last_insn_heuristic, "sched-last-insn-heuristic");
    append_to_attribute_stream(oss, opts.opt_sched_pressure, "sched-pressure");
    append_to_attribute_stream(oss, opts.opt_sched_rank_heuristic, "sched-rank-heuristic");
    append_to_attribute_stream(oss, opts.opt_sched_spec, "sched-spec");
    append_to_attribute_stream(oss, opts.opt_sched_spec_insn_heuristic, "sched-spec-insn-heuristic");
    append_to_attribute_stream(oss, opts.opt_sched_spec_load, "sched-spec-load");
    append_to_attribute_stream(oss, opts.opt_sched_spec_load_dangerous, "sched-spec-load-dangerous");
    append_to_attribute_stream(oss, opts.opt_sched_stalled_insns, "sched-stalled-insns");
    append_to_attribute_stream(oss, opts.opt_sched_stalled_insns_dep, "sched-stalled-insns-dep");
    append_to_attribute_stream(oss, opts.opt_sched2_use_superblocks, "sched2-use-superblocks");
    append_to_attribute_stream(oss, opts.opt_schedule_fusion, "schedule-fusion");
    append_to_attribute_stream(oss, opts.opt_schedule_insns, "schedule-insns");
    append_to_attribute_stream(oss, opts.opt_schedule_insns2, "schedule-insns2");
    append_to_attribute_stream(oss, opts.opt_section_anchors, "section-anchors");
    append_to_attribute_stream(oss, opts.opt_sel_sched_pipelining, "sel-sched-pipelining");
    append_to_attribute_stream(oss, opts.opt_sel_sched_pipelining_outer_loops, "sel-sched-pipelining-outer-loops");
    append_to_attribute_stream(oss, opts.opt_sel_sched_reschedule_pipelined, "sel-sched-reschedule-pipelined");
    append_to_attribute_stream(oss, opts.opt_selective_scheduling, "selective-scheduling");
    append_to_attribute_stream(oss, opts.opt_selective_scheduling2, "selective-scheduling2");
    append_to_attribute_stream(oss, opts.opt_semantic_interposition, "semantic-interposition");
    append_to_attribute_stream(oss, opts.opt_short_enums, "short-enums");
    append_to_attribute_stream(oss, opts.opt_short_wchar, "short-wchar");
    append_to_attribute_stream(oss, opts.opt_shrink_wrap, "shrink-wrap");
    append_to_attribute_stream(oss, opts.opt_shrink_wrap_separate, "shrink-wrap-separate");
    append_to_attribute_stream(oss, opts.opt_signaling_nans, "signaling-nans");
    append_to_attribute_stream(oss, opts.opt_signed_zeros, "signed-zeros");
    append_to_attribute_stream(oss, opts.opt_single_precision_constant, "single-precision-constant");
    append_to_attribute_stream(oss, opts.opt_split_ivs_in_unroller, "split-ivs-in-unroller");
    append_to_attribute_stream(oss, opts.opt_split_loops, "split-loops");
    append_to_attribute_stream(oss, opts.opt_split_paths, "split-paths");
    append_to_attribute_stream(oss, opts.opt_split_wide_types, "split-wide-types");
    append_to_attribute_stream(oss, opts.opt_split_wide_types_early, "split-wide-types-early");
    append_to_attribute_stream(oss, opts.opt_ssa_backprop, "ssa-backprop");
    append_to_attribute_stream(oss, opts.opt_ssa_phiopt, "ssa-phiopt");
    append_to_attribute_stream(oss, opts.opt_stack_clash_protection, "stack-clash-protection");
    append_to_attribute_stream(oss, opts.opt_stack_protector, "stack-protector");
    append_to_attribute_stream(oss, opts.opt_stdarg_opt, "stdarg-opt");
    append_to_attribute_stream(oss, opts.opt_store_merging, "store-merging");
    append_to_attribute_stream(oss, opts.opt_strict_aliasing, "strict-aliasing");
    append_to_attribute_stream(oss, opts.opt_strict_volatile_bitfields, "strict-volatile-bitfields");
    append_to_attribute_stream(oss, opts.opt_thread_jumps, "thread-jumps");
    append_to_attribute_stream(oss, opts.opt_toplevel_reorder, "toplevel-reorder");
    append_to_attribute_stream(oss, opts.opt_tracer, "tracer");
    append_to_attribute_stream(oss, opts.opt_trapping_math, "trapping-math");
    append_to_attribute_stream(oss, opts.opt_trapv, "trapv");
    append_to_attribute_stream(oss, opts.opt_tree_bit_ccp, "tree-bit-ccp");
    append_to_attribute_stream(oss, opts.opt_tree_builtin_call_dce, "tree-builtin-call-dce");
    append_to_attribute_stream(oss, opts.opt_tree_ccp, "tree-ccp");
    append_to_attribute_stream(oss, opts.opt_tree_ch, "tree-ch");
    append_to_attribute_stream(oss, opts.opt_tree_coalesce_vars, "tree-coalesce-vars");
    append_to_attribute_stream(oss, opts.opt_tree_copy_prop, "tree-copy-prop");
    append_to_attribute_stream(oss, opts.opt_tree_cselim, "tree-cselim");
    append_to_attribute_stream(oss, opts.opt_tree_dce, "tree-dce");
    append_to_attribute_stream(oss, opts.opt_tree_dominator_opts, "tree-dominator-opts");
    append_to_attribute_stream(oss, opts.opt_tree_dse, "tree-dse");
    append_to_attribute_stream(oss, opts.opt_tree_forwprop, "tree-forwprop");
    append_to_attribute_stream(oss, opts.opt_tree_fre, "tree-fre");
    append_to_attribute_stream(oss, opts.opt_tree_loop_distribute_patterns, "tree-loop-distribute-patterns");
    append_to_attribute_stream(oss, opts.opt_tree_loop_distribution, "tree-loop-distribution");
    append_to_attribute_stream(oss, opts.opt_tree_loop_if_convert, "tree-loop-if-convert");
    append_to_attribute_stream(oss, opts.opt_tree_loop_im, "tree-loop-im");
    append_to_attribute_stream(oss, opts.opt_tree_loop_ivcanon, "tree-loop-ivcanon");
    append_to_attribute_stream(oss, opts.opt_tree_loop_optimize, "tree-loop-optimize");
    append_to_attribute_stream(oss, opts.opt_tree_loop_vectorize, "tree-loop-vectorize");
    append_to_attribute_stream(oss, opts.opt_tree_lrs, "tree-lrs");
    append_to_attribute_stream(oss, opts.opt_tree_partial_pre, "tree-partial-pre");
    append_to_attribute_stream(oss, opts.opt_tree_phiprop, "tree-phiprop");
    append_to_attribute_stream(oss, opts.opt_tree_pre, "tree-pre");
    append_to_attribute_stream(oss, opts.opt_tree_pta, "tree-pta");
    append_to_attribute_stream(oss, opts.opt_tree_reassoc, "tree-reassoc");
    append_to_attribute_stream(oss, opts.opt_tree_scev_cprop, "tree-scev-cprop");
    append_to_attribute_stream(oss, opts.opt_tree_sink, "tree-sink");
    append_to_attribute_stream(oss, opts.opt_tree_slp_vectorize, "tree-slp-vectorize");
    append_to_attribute_stream(oss, opts.opt_tree_slsr, "tree-slsr");
    append_to_attribute_stream(oss, opts.opt_tree_sra, "tree-sra");
    append_to_attribute_stream(oss, opts.opt_tree_switch_conversion, "tree-switch-conversion");
    append_to_attribute_stream(oss, opts.opt_tree_tail_merge, "tree-tail-merge");
    append_to_attribute_stream(oss, opts.opt_tree_ter, "tree-ter");
    append_to_attribute_stream(oss, opts.opt_tree_vectorize, "tree-vectorize");
    append_to_attribute_stream(oss, opts.opt_tree_vrp, "tree-vrp");
    append_to_attribute_stream(oss, opts.opt_unconstrained_commons, "unconstrained-commons");
    append_to_attribute_stream(oss, opts.opt_unreachable_traps, "unreachable-traps");
    append_to_attribute_stream(oss, opts.opt_unroll_all_loops, "unroll-all-loops");
    append_to_attribute_stream(oss, opts.opt_unroll_completely_grow_size, "unroll-completely-grow-size");
    append_to_attribute_stream(oss, opts.opt_unroll_loops, "unroll-loops");
    append_to_attribute_stream(oss, opts.opt_unsafe_math_optimizations, "unsafe-math-optimizations");
    append_to_attribute_stream(oss, opts.opt_unswitch_loops, "unswitch-loops");
    append_to_attribute_stream(oss, opts.opt_unwind_tables, "unwind-tables");
    append_to_attribute_stream(oss, opts.opt_var_tracking, "var-tracking");
    append_to_attribute_stream(oss, opts.opt_var_tracking_assignments, "var-tracking-assignments");
    append_to_attribute_stream(oss, opts.opt_var_tracking_assignments_toggle, "var-tracking-assignments-toggle");
    append_to_attribute_stream(oss, opts.opt_var_tracking_uninit, "var-tracking-uninit");
    append_to_attribute_stream(oss, opts.opt_variable_expansion_in_unroller, "variable-expansion-in-unroller");
    append_to_attribute_stream(oss, opts.opt_version_loops_for_strides, "version-loops-for-strides");
    append_to_attribute_stream(oss, opts.opt_vpt, "vpt");
    append_to_attribute_stream(oss, opts.opt_web, "web");
    append_to_attribute_stream(oss, opts.opt_wrapv, "wrapv");
    append_to_attribute_stream(oss, opts.opt_wrapv_pointer, "wrapv-pointer");;

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
        cxx_dbg("[cxx_optimizer] function MATCH name='%s' file='%s' line=%d -> optimize(\"%s\")",
                function_name.c_str(), filename.c_str(), line_number, current_attribute.c_str());
        handle_optimize_attribute(fndecl, current_attribute);
        set_function_attribute(fndecl, current_attribute);
        return;
    }
    cxx_dbg("[cxx_optimizer] function seen name='%s' file='%s' line=%d -> no rule",
            function_name.c_str(), filename.c_str(), line_number);
}

static void handle_optimize_pragma(const std::string &attribute) {
    tree arg = build_string(attribute.size(), attribute.c_str());
    tree args = tree_cons(NULL_TREE, arg, NULL_TREE);
    parse_optimize_options(args, false);
    current_optimize_pragma = chainon(current_optimize_pragma, args);
    optimization_current_node = build_optimization_node(&global_options, &global_options);
}

static void on_start_unit(std::vector<Rule> *rules) {
    cxx_dbg("[cxx_optimizer] on_start_unit main_input_basename='%s'",
            main_input_basename ? main_input_basename : "(null)");
    for (auto it = rules->rbegin(); it != rules->rend(); ++it) {
        if (it->type == "file" && (it->filename == "*" || it->filename == std::string(main_input_basename))) {
            std::string attributes = build_attribute_string(it->opts);
            cxx_dbg("[cxx_optimizer] file MATCH filename='%s' -> optimize(\"%s\")",
                    it->filename.c_str(), attributes.c_str());
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

    cxx_dbg("=== [cxx_optimizer] plugin_init base_name='%s' config='%s' main_input='%s'",
            plugin_info->base_name, config_path,
            main_input_filename ? main_input_filename : "(null)");

    std::vector<Rule> *rules = parse_config_file(config_path);

    cxx_dbg("[cxx_optimizer] parsed %zu rule(s) from config", rules->size());
    for (size_t i = 0; i < rules->size(); ++i) {
        const Rule &r = (*rules)[i];
        cxx_dbg("[cxx_optimizer]   rule[%zu] type='%s' function_name='%s' filename='%s' line_number=%d level=%u",
                i, r.type.c_str(), r.function_name.c_str(), r.filename.c_str(),
                r.line_number, r.opts.level);
    }

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
