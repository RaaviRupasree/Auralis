from time import perf_counter


def start_timer():
    return perf_counter()


def elapsed_seconds(started_at):
    return perf_counter() - started_at