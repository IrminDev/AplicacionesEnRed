import logging
import threading
import time
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s (%(threadName)-2s) %(message)s',
)

BUFFER_SIZE = 10
buffer = []

producer_condition = threading.Condition()
consumer_condition = threading.Condition()

def consumer(consumer_id):
    global buffer
    logging.debug(f'Consumer-{consumer_id} started.')
    while True:
        with consumer_condition:
            while not buffer:
                logging.debug(f'Consumer-{consumer_id} waiting, buffer is empty.')
                consumer_condition.wait()
            item = buffer.pop(0)
            logging.debug(f'Consumer-{consumer_id} consumed item: {item}')
        with producer_condition:
            producer_condition.notify()
        time.sleep(1) 


def producer(producer_id):
    global buffer
    logging.debug(f'Producer-{producer_id} started.')
    item_counter = 0
    while True:
        with producer_condition:
            while len(buffer) >= BUFFER_SIZE:
                logging.debug(f'Producer-{producer_id} waiting, buffer is full.')
                producer_condition.wait()
            item = f'Item-{item_counter} from Producer-{producer_id}'
            buffer.append(item)
            logging.debug(f'Producer-{producer_id} produced item: {item}')
            item_counter += 1
        with consumer_condition:
            consumer_condition.notify()
        time.sleep(1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python producer_consumer_conditions.py <num_producers> <num_consumers>")
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


if __name__ == "__main__":
    main()