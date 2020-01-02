import pytest


def pytest_addoption(parser):
    parser.addoption(
        '-B',
        '--run-benchmarks',
        action='store_true',
        default=False,
        help='run benchmarks',
    )


def pytest_runtest_setup(item):
    """
    Skip tests marked benchmark unless --run-benchmark is given to pytest
    """
    run_benchmarks = item.config.getoption('--run-benchmarks')

    is_benchmark = any(item.iter_markers(name="benchmark"))

    if is_benchmark:
        if run_benchmarks:
            return

        pytest.skip(
            'need --run-benchmarks to run benchmarks'
        )


def pytest_collection_modifyitems(items):
    """
    Add the "benchmark" mark to tests that start with "benchmark_".
    """
    for item in items:
        test_class_name = item.cls.__name__
        if test_class_name.startswith("benchmark_"):
            item.add_marker(pytest.mark.benchmark)
