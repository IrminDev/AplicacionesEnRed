import threading
import time
import random

class BankAccount:
    def __init__(self):
        self.balance = 0
        self.lock = threading.Lock() # Lock object to synchronize threads
    
    def deposit(self, quantity):
        with self.lock:
            self.balance += quantity
            print(f"{threading.current_thread().name}: You've deposited {quantity}. Current balance: {self.balance}")
    
    def withdraw(self, quantity):
        with self.lock:
            if self.balance >= quantity:
                self.balance -= quantity
                print(f"{threading.current_thread().name}: You've withdrew {quantity}. Current balance: {self.balance}")
            else:
                print(f"{threading.current_thread().name}: Insufficient funds, you can't withdraw {quantity}.")
    
    def checkCurrentBalance(self):
        with self.lock:
            print(f"{threading.current_thread().name}: Current balance: {self.balance}")

def doDeposit(account):
    for _ in range(5):
        quantity = random.randint(100, 500)
        account.deposit(quantity)
        time.sleep(random.uniform(0.1, 0.5))

def doWithdraw(account):
    for _ in range(5):
        quantity = random.randint(100, 500)
        account.withdraw(quantity)
        time.sleep(random.uniform(0.1, 0.5))

def checkBalance(account):
    for _ in range(5):
        account.checkCurrentBalance()
        time.sleep(random.uniform(0.1, 0.5))

if __name__ == "__main__":
    account = BankAccount()
    
    depositThread = threading.Thread(target=doDeposit, args=(account,), name="DepositThread")
    withdrawThread = threading.Thread(target=doWithdraw, args=(account,), name="WithdrawThread")
    checkThread = threading.Thread(target=checkBalance, args=(account,), name="CheckThread")
    
    depositThread.start()
    withdrawThread.start()
    checkThread.start()
    
    depositThread.join()
    withdrawThread.join()
    checkThread.join()
    
    print("Operation finished")