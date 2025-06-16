import random
import threading
import logging
import time

caracter = ""
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )

attempt_counters = {}

def worker(lock):
    global caracter
    thread_name = threading.current_thread().name
    
    if thread_name not in attempt_counters:
        attempt_counters[thread_name] = 0
    
    for i in range (0,10):
        while True:
            if lock.acquire(blocking=False):
                try:
                    logging.debug(f"Entré en la sección crítica después de {attempt_counters[thread_name]} intentos fallidos")
                    caracter = thread_name
                    time.sleep(random.randint(1, 5))
                    logging.debug(f"Ronda {i}: valor de caracter - {caracter}")
                    break 
                finally:
                    lock.release()
            else:
                attempt_counters[thread_name] += 1
                logging.debug(f"Intento fallido #{attempt_counters[thread_name]}. Ronda {i}. Reintentando en 2 segundos...")
                time.sleep(2) 


lock = threading.Lock()
h1 = threading.Thread(target=worker, name="Hilo 1", args=(lock,))
h2 = threading.Thread(target=worker, name="Hilo 2", args=(lock,))
h1.start()
h2.start()
h1.join()
h2.join()

logging.debug(f"Estadísticas de intentos: {attempt_counters}")