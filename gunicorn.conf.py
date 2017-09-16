import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1   # pylint: disable=global-variable,invalid-name
timeout = 3600  # pylint: disable=global-variable,invalid-name
