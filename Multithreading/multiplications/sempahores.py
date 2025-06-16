import logging
import random
import threading
import time

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(threadName)-2s) %(message)s',
                    )

semaphores = []
threads = []
sem = threading.Semaphore(1)
semaphores.append(sem)

for i in range(10):
    sem = threading.Semaphore(1)
    sem.acquire()
    semaphores.append(sem)

def printMultiplication(i, semaphores):
    with semaphores[i-1]:
        logging.debug('Printing the multiplication table %d ', i)
        for j in range(1, 21):
            logging.debug('%d x %d = %d', i, j, i * j)
            time.sleep(0.1)
            if j == 10: # Wait for the 10th multiplication to realease the next semaphore
                if i < 10:
                    semaphores[i].release()
                else:
                    semaphores[0].release()
                semaphores[i-1].acquire() # Block the current semaphore until the next thread finishes
        if i < 10:
            semaphores[i].release()
        else:
            semaphores[0].release()
        logging.debug('Releasing the next semaphore %d ', i+1)
    semaphores[i-1].acquire() # Block the current semaphore until the next thread finishes

for i in range(1,11):
    t = threading.Thread(target=printMultiplication, args=(i, semaphores), name=str(i))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

logging.debug('All threads finished.')