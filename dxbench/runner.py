from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib.resources import as_file

from dxbench import CUT_DIR, LLM_GEN_DIR
from dxbench.bot import Bot
from dxbench.internal import build_sandbox, generate_test, run_in_sandbox, calculate_metrics, print_metrics
from dxbench.registry import cut_result_registry


def run(bot: Bot):
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_cut = {executor.submit(generate_test, bot, cut.cut_file): cut for cut in cut_result_registry}

        for future in as_completed(future_to_cut):
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred: {e}")

    build_sandbox()

    with as_file(CUT_DIR) as cut_dir:
        exit_code, per_file = run_in_sandbox(cut_dir, LLM_GEN_DIR)

        metrics = calculate_metrics(cut_result_registry, per_file)
        print_metrics(metrics)

        print("\nDetailed Results:")
        for cut_entry in cut_result_registry:
            filename = cut_entry.test_filename
            expected = cut_entry.should_pass
            actual = per_file.get(filename, False)
            status = "✓" if expected == actual else "✗"
            print(f" {status} {filename}: expected={expected}, actual={actual}")

        return exit_code, per_file, metrics
