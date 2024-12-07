import os
import time
import threading
import multiprocessing
from queue import Queue

# Список ключових слів для пошуку
KEYWORDS = ["error", "warning", "critical"]

# Функція для пошуку ключових слів у файлах
def search_keywords_in_file(file_path, keywords):
    results = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for keyword in keywords:
                if keyword in content:
                    if keyword not in results:
                        results[keyword] = []
                    results[keyword].append(file_path)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return results

# Функція для багатопотокової обробки
def process_files_threading(file_list, keywords):
    results = {}
    lock = threading.Lock()

    def worker(files):
        nonlocal results
        local_results = {}
        for file in files:
            file_results = search_keywords_in_file(file, keywords)
            for key, value in file_results.items():
                if key not in local_results:
                    local_results[key] = []
                local_results[key].extend(value)
        with lock:
            for key, value in local_results.items():
                if key not in results:
                    results[key] = []
                results[key].extend(value)

    num_threads = min(len(file_list), os.cpu_count())
    chunk_size = len(file_list) // num_threads
    threads = []

    for i in range(num_threads):
        chunk = file_list[i * chunk_size:(i + 1) * chunk_size]
        if i == num_threads - 1:
            chunk = file_list[i * chunk_size:]
        thread = threading.Thread(target=worker, args=(chunk,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results

# Функція для багатопроцесорної обробки
def process_files_multiprocessing(file_list, keywords):
    def worker(files, keywords, queue):
        local_results = {}
        for file in files:
            file_results = search_keywords_in_file(file, keywords)
            for key, value in file_results.items():
                if key not in local_results:
                    local_results[key] = []
                local_results[key].extend(value)
        queue.put(local_results)

    num_processes = min(len(file_list), os.cpu_count())
    chunk_size = len(file_list) // num_processes
    processes = []
    queue = multiprocessing.Queue()

    for i in range(num_processes):
        chunk = file_list[i * chunk_size:(i + 1) * chunk_size]
        if i == num_processes - 1:
            chunk = file_list[i * chunk_size:]
        process = multiprocessing.Process(target=worker, args=(chunk, keywords, queue))
        processes.append(process)
        process.start()

    results = {}
    for _ in range(num_processes):
        local_results = queue.get()
        for key, value in local_results.items():
            if key not in results:
                results[key] = []
            results[key].extend(value)

    for process in processes:
        process.join()

    return results

if __name__ == "__main__":
    # Створити список файлів для аналізу
    directory = "test_files"  # Змінити на свою папку з файлами
    file_list = [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]

    print("Starting threading version...")
    start_time = time.time()
    threading_results = process_files_threading(file_list, KEYWORDS)
    print("Threading results:", threading_results)
    print("Threading execution time:", time.time() - start_time, "seconds")

    print("\nStarting multiprocessing version...")
    start_time = time.time()
    multiprocessing_results = process_files_multiprocessing(file_list, KEYWORDS)
    print("Multiprocessing results:", multiprocessing_results)
    print("Multiprocessing execution time:", time.time() - start_time, "seconds")
