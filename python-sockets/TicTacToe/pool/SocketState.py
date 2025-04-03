from enum import Enum

class SocketState:
    state = Enum ('SocketState',[
        ('STARTING ', 0),
        ('RUNNING', 1),
        ('STOPPED', 2),
        ('FAILURE', 3)
    ])
    
    def __init__(self, socket, initialState):
        self.socket = socket
        self.state = initialState
        self.message_queues = {}
        self.message_queues[socket] = []
        self.message_queues[socket].append(b'')

    def getState(self):
        return self.state
    
    def setState(self, state):
        self.state = state

    def getSocket(self):
        return self.socket
    
    def setSocket(self, socket):
        self.socket = socket
    
    def getMessageQueue(self):
        return self.message_queues[self.socket]
    
    def setMessageQueue(self, message):
        self.message_queues[self.socket].append(message)

    def getMessageQueueSize(self):
        return len(self.message_queues[self.socket])
