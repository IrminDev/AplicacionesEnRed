import logging
import threading
import queue
import time
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s (%(threadName)-2s) %(message)s',
)

BUFFER_SIZE = 10
buffer = queue.Queue(maxsize=BUFFER_SIZE)

def consumer(consumer_id):
    logging.debug(f'Consumer-{consumer_id} started.')
    while True:
        if buffer.empty():
            logging.debug(f'Consumer-{consumer_id} waiting, buffer is empty.')
        item = buffer.get()
        logging.debug(f'Consumer-{consumer_id} consumed item: {item}')
        buffer.task_done()
        time.sleep(1)  # Simulate processing time

def producer(producer_id):
    logging.debug(f'Producer-{producer_id} started.')
    item_counter = 0
    while True:
        if buffer.full():
            logging.debug(f'Producer-{producer_id} waiting, buffer is full.')
        item = f'Item-{item_counter} from Producer-{producer_id}'
        buffer.put(item)
        logging.debug(f'Producer-{producer_id} produced item: {item}')
        item_counter += 1
        time.sleep(1)  # Simulate production time

def main():
    if len(sys.argv) != 3:
        print("Usage: python producer_consumer_queue.py <num_producers> <num_consumers>")
        sys.exit(1)

    num_producers = int(sys.argv[1])
    num_consumers = int(sys.argv[2])

    producers = []
    for i in range(num_producers):
        p = threading.Thread(target=producer, args=(i,), name=f'Producer-{i}')
        producers.append(p)
        p.start()

    consumers = []
    for i in range(num_consumers):
        c = threading.Thread(target=consumer, args=(i,), name=f'Consumer-{i}')
        consumers.append(c)
        c.start()

    for p in producers:
        p.join()

    for c in consumers:
        c.join()

    buffer.join()

if __name__ == '__main__':
    main()