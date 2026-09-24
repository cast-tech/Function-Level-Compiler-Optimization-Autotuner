import json
import logging
import os
import time
import copy
import csv
from datetime import datetime

from tools.services.enhanced_builder import EnhancedBuilder
from tools.services.enhanced_builder import EnhancedBuilderError
from tools.interfaces.runner import RunError
from tools.interfaces.builder import BuildError

logger = logging.getLogger(__name__)


class Reduce():
    def __init__(self, best_configuration_file_path, runner, enhanced_builder, output_dir,
                 initial_group_size=50, impact_threshold=0.1, min_flags_to_keep=0,
                 ranked_flags_csv=None, entry_index=0, retries=1):
        with open(best_configuration_file_path, "r") as f:
            self.best_configuration = json.load(f)

        if isinstance(self.best_configuration, dict):
            self.best_configuration = [self.best_configuration]
        if not isinstance(self.best_configuration, list) or not self.best_configuration:
            raise ValueError("Optimization configuration must be a non-empty object or list")
        if entry_index < 0 or entry_index >= len(self.best_configuration):
            raise ValueError(
                f"Entry index {entry_index} is outside the configuration range "
                f"0..{len(self.best_configuration) - 1}"
            )
        optimizations = self.best_configuration[entry_index].get("optimizations")
        if not isinstance(optimizations, dict) or "level" not in optimizations:
            raise ValueError("Selected configuration entry must contain optimizations.level")
        if initial_group_size < 1:
            raise ValueError("Initial group size must be at least 1")
        if min_flags_to_keep < 0:
            raise ValueError("Minimum flags to keep cannot be negative")
        if retries < 1:
            raise ValueError("Retries must be at least 1")

        self.flag_rank = {}
        if ranked_flags_csv:
            with open(ranked_flags_csv, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.flag_rank[row["flag"]] = int(row["rank"])
        self.enhanced_builder = enhanced_builder
        self.runner = runner
        self.output_dir = output_dir
        self.impact_threshold = impact_threshold
        self.initial_group_size = initial_group_size
        self.min_flags_to_keep = min_flags_to_keep
        self.entry_index = entry_index
        self.retries = retries

        self.run_log = []
        self.run_counter = 0

        os.makedirs(output_dir, exist_ok=True)
        self.log_file = os.path.join(output_dir, "reduction_log.jsonl")
        self.summary_file = os.path.join(output_dir, "reduction_summary.json")
        self.csv_file = os.path.join(output_dir, "runtime_log.csv")

        # Each invocation produces one internally consistent set of logs.
        open(self.log_file, "w").close()

        # Initialize CSV with headers
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "run_id",
                "timestamp",
                "iteration",
                "group_size",
                "label",
                "n_flags",
                "runtime",
                "relative_to_baseline",
                "flags_removed",
                "wall_time"
            ])

        logger.info("Measuring baseline runtime with full best configuration")
        self.base_runtime = None
        self.base_runtime = self.get_runtime(self.best_configuration, label="baseline")
        self.O3_runtime = self.get_runtime([], label="O3_baseline")
        logger.info(f"Baseline runtime: {self.base_runtime:.4f}s "
                     f"({len(self._get_flags(self.best_configuration))} tunable flags)")

    def _get_flags(self, configuration):
        return [
            flag for flag in configuration[self.entry_index]["optimizations"]
            if flag != "level"
        ]

    def _log_run(self, run_info):
        """Append a single run record to both JSONL and CSV."""
        self.run_counter += 1
        run_info["run_id"] = self.run_counter
        run_info["timestamp"] = datetime.now().isoformat()
        self.run_log.append(run_info)

        # JSONL
        with open(self.log_file, "a") as f:
            f.write(json.dumps(run_info) + "\n")

        # CSV
        with open(self.csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                run_info.get("run_id", ""),
                run_info.get("timestamp", ""),
                run_info.get("iteration", ""),
                run_info.get("group_size", ""),
                run_info.get("label", ""),
                run_info.get("n_flags", ""),
                run_info.get("runtime", ""),
                run_info.get("relative_to_baseline", ""),
                run_info.get("flags_removed", ""),
                run_info.get("wall_time", "")
            ])

    def _sort_flags_by_rank(self, flags):
        """Sort flags by CSV rank (lowest rank = highest priority, first in list).
        Flags absent from the CSV are placed at the end in their original order."""
        unranked = [f for f in flags if f not in self.flag_rank]
        ranked = sorted(
            [f for f in flags if f in self.flag_rank],
            key=lambda f: self.flag_rank[f]
        )
        return ranked + unranked

    def get_optimization_groups(self, flags, group_size):
        groups = []
        for i in range(0, len(flags), group_size):
            groups.append(flags[i:i + group_size])
        return groups

    def get_runtime(self, configuration, label="", iteration=None, group_size=None,
                    flags_removed=None, retries=None):
        """Compile and benchmark a configuration, with logging and retry."""
        if configuration:
            n_flags = len(self._get_flags(configuration))
        else:
            n_flags = 0
        start = time.time()
        retries = self.retries if retries is None else retries

        runtimes = []
        for attempt in range(retries):
            try:
                build_info = self.enhanced_builder.build_with_optimizations(
                    configuration, ["-O3", "-march=native"]
                )
                runtime = self.runner.run(build_info)
                runtimes.append(runtime)
            except (EnhancedBuilderError, BuildError) as e:
                logger.warning(f"Build failed (attempt {attempt+1}): {e}")
                runtimes.append(float('inf'))
            except RunError as e:
                logger.warning(f"Run failed (attempt {attempt+1}): {e}")
                runtimes.append(float('inf'))

        runtimes = [r for r in runtimes if r != float('inf')]
        if not runtimes:
            median_runtime = float('inf')
        else:
            runtimes.sort()
            median_runtime = runtimes[len(runtimes) // 2]

        elapsed = time.time() - start

        self._log_run({
            "label": label,
            "iteration": iteration,
            "group_size": group_size,
            "n_flags": n_flags,
            "runtime": median_runtime,
            "all_runtimes": runtimes,
            "wall_time": round(elapsed, 2),
            "flags_removed": flags_removed,
            "relative_to_baseline": (
                round(((median_runtime - self.base_runtime) / self.base_runtime) * 100, 6)
                if self.base_runtime and self.base_runtime != float('inf') else None
            )
        })

        return median_runtime

    def griddy_reduce(self, sorted_flags, current_configuration, iteration, group_size):
        worse_groups = [group for group in sorted_flags if group[1] < self.impact_threshold]

        remaining_count = len(self._get_flags(current_configuration))
        max_removable = max(0, remaining_count - self.min_flags_to_keep)
        removable_groups = []
        removable_count = 0
        for group in worse_groups:
            group_flag_count = len(group[0].split())
            if removable_count + group_flag_count <= max_removable:
                removable_groups.append(group)
                removable_count += group_flag_count
        worse_groups = removable_groups

        if not worse_groups:
            logger.info("No groups below impact threshold to remove")
            return current_configuration, [], self.base_runtime

        logger.info(f"Griddy reduce: {len(worse_groups)} groups below "
                     f"{self.impact_threshold:.2f}% threshold")

        low, high = 0, len(worse_groups)
        best_to_remove = 0
        best_runtime = self.base_runtime
        best_config = current_configuration

        while low <= high:
            mid = (low + high) // 2
            if mid == 0:
                low = mid + 1
                continue

            test_config = copy.deepcopy(current_configuration)
            removed_flags = []
            for i in range(mid):
                for flag in worse_groups[i][0].split():
                    test_config[self.entry_index]["optimizations"].pop(flag, None)
                    removed_flags.append(flag)

            runtime = self.get_runtime(
                test_config,
                label=f"griddy_remove_{mid}_groups",
                iteration=iteration,
                group_size=group_size,
                flags_removed=",".join(removed_flags)
            )
            degradation = ((runtime - self.base_runtime) / self.base_runtime) * 100

            logger.info(f"  Removing {mid} groups ({len(removed_flags)} flags): "
                        f"runtime={runtime:.4f}s, degradation={degradation:+.3f}%")

            if degradation > self.impact_threshold:
                high = mid - 1
            else:
                best_runtime = runtime
                best_to_remove = mid
                best_config = test_config
                low = mid + 1

        removed_groups = worse_groups[:best_to_remove]
        removed_flag_names = []
        for group_key, _ in removed_groups:
            removed_flag_names.extend(group_key.split())

        logger.info(f"Griddy result: removed {best_to_remove} groups "
                     f"({len(removed_flag_names)} flags), "
                     f"runtime: {best_runtime:.4f}s")

        return best_config, removed_groups, best_runtime

    def reduce(self):
        if self.base_runtime == float('inf'):
            raise RuntimeError("The tuned configuration could not be built and benchmarked")

        improvement = None
        if self.O3_runtime not in (0, float('inf')):
            improvement = (self.O3_runtime - self.base_runtime) / self.O3_runtime * 100
        if improvement is not None and improvement < 0.5:
            logger.info(
                f"Best configuration improvement over O3 is {improvement:.2f}% "
                f"(base={self.base_runtime:.4f}s, O3={self.O3_runtime:.4f}s). "
                f"Skipping reduction."
            )
            final_flags = self._get_flags(self.best_configuration)
            self._save_results(self.best_configuration, final_flags, [],
                               skipped_reason="improvement below 0.5%")
            return self.best_configuration, final_flags

        current_configuration = copy.deepcopy(self.best_configuration)
        group_size = self.initial_group_size
        iteration = 0
        total_removed = 0
        initial_flag_count = len(self._get_flags(current_configuration))

        iteration_summaries = []

        logger.info(f"Starting reduction: {initial_flag_count} flags, "
                     f"initial group_size={group_size}, "
                     f"min_flags_to_keep={self.min_flags_to_keep}")

        while group_size >= 1:
            iteration += 1
            remaining_flags = self._get_flags(current_configuration)
            n_remaining = len(remaining_flags)

            logger.info(f"\n{'='*70}")
            logger.info(f"ITERATION {iteration}: group_size={group_size}, "
                         f"{n_remaining} flags remaining")
            logger.info(f"{'='*70}")

            if n_remaining <= self.min_flags_to_keep:
                logger.info(f"Reached minimum flag count ({n_remaining} <= "
                             f"{self.min_flags_to_keep}). Stopping.")
                break

            if self.flag_rank:
                remaining_flags = self._sort_flags_by_rank(remaining_flags)
            groups = self.get_optimization_groups(remaining_flags, group_size)
            logger.info(f"Split into {len(groups)} groups of ~{group_size}")

            flags_impact = {}
            for group_idx, group in enumerate(groups):
                temp_configuration = copy.deepcopy(current_configuration)
                for flag in group:
                    temp_configuration[self.entry_index]["optimizations"].pop(flag, None)

                temp_runtime = self.get_runtime(
                    temp_configuration,
                    label=f"iter{iteration}_group{group_idx}_size{group_size}",
                    iteration=iteration,
                    group_size=group_size,
                    flags_removed=",".join(group)
                )
                key = " ".join(group)
                impact = ((temp_runtime - self.base_runtime) / self.base_runtime) * 100
                flags_impact[key] = impact

                logger.info(f"  Group {group_idx} ({len(group)} flags): "
                             f"impact={impact:+.4f}% "
                             f"{'[LOW]' if impact < self.impact_threshold else '[KEEP]'}")

            sorted_flags = sorted(flags_impact.items(), key=lambda x: x[1])
            before_count = len(self._get_flags(current_configuration))
            current_configuration, removed_groups, new_runtime = self.griddy_reduce(
                sorted_flags, current_configuration, iteration, group_size
            )
            after_count = len(self._get_flags(current_configuration))
            removed_this_iter = before_count - after_count
            total_removed += removed_this_iter

            if new_runtime != float('inf'):
                self.base_runtime = new_runtime

            iter_summary = {
                "iteration": iteration,
                "group_size": group_size,
                "flags_before": before_count,
                "flags_after": after_count,
                "flags_removed": removed_this_iter,
                "total_removed": total_removed,
                "n_groups_tested": len(groups),
                "n_groups_removed": len(removed_groups),
                "runtime_after": new_runtime,
                "group_impacts": sorted_flags
            }
            iteration_summaries.append(iter_summary)

            logger.info(f"Iteration {iteration} result: "
                         f"{before_count} → {after_count} flags "
                         f"(-{removed_this_iter}), runtime={new_runtime:.4f}s")

            group_size = group_size // 2

        final_flags = self._get_flags(current_configuration)
        logger.info(f"\n{'='*70}")
        logger.info(f"REDUCTION COMPLETE")
        logger.info(f"  {initial_flag_count} → {len(final_flags)} flags "
                     f"({total_removed} removed)")
        logger.info(f"  Final runtime: {self.base_runtime:.4f}s")
        logger.info(f"  Iterations: {iteration}")
        logger.info(f"  Total evaluations: {self.run_counter}")
        logger.info(f"{'='*70}")

        for i, flag in enumerate(final_flags):
            logger.info(f"  {i+1:3d}. {flag}")

        self._save_results(current_configuration, final_flags, iteration_summaries)

        return current_configuration, final_flags

    def _save_results(self, final_configuration, final_flags, iteration_summaries,
                      skipped_reason=None):
        with open(os.path.join(self.output_dir, "reduced_configuration.json"), "w") as f:
            json.dump(final_configuration, f, indent=4)

        with open(os.path.join(self.output_dir, "reduced_flags.txt"), "w") as f:
            f.write("\n".join(final_flags))

        summary = {
            "entry_index": self.entry_index,
            "initial_flag_count": len(self._get_flags(self.best_configuration)),
            "final_flag_count": len(final_flags),
            "final_flags": final_flags,
            "final_runtime": self.base_runtime,
            "impact_threshold": self.impact_threshold,
            "initial_group_size": self.initial_group_size,
            "total_evaluations": self.run_counter,
            "iterations": iteration_summaries,
            "skipped_reason": skipped_reason,
        }
        with open(self.summary_file, "w") as f:
            json.dump(summary, f, indent=4)

        logger.info(f"Results saved to {self.output_dir}/")
        logger.info(f"  reduced_configuration.json")
        logger.info(f"  reduced_flags.txt")
        logger.info(f"  reduction_summary.json")
        logger.info(f"  reduction_log.jsonl")
        logger.info(f"  runtime_log.csv")
