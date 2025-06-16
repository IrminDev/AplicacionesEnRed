from enum import Enum
import time

class SocketState:
    state = Enum('SocketState', [
        ('STARTING', 0),
        ('RUNNING', 1),
        ('STOPPING', 2),
        ('STOPPED', 3),
        ('FAILURE', 4)
    ])
    
    def __init__(self, socket, addr, initialState=None):
        self.socket = socket
        self.addr = addr
        self.state = initialState if initialState else self.state.STARTING
        self.message_queues = {}
        self.message_queues[socket] = []
        self.message_queues[socket].append(b'')
        self.last_activity = time.time()
        self.player_name = None
        self.player_symbol = None  # X or O
        self.game_id = None        # Which game this player is in
    
    def getState(self):
        return self.state
    
    def setState(self, state):
        self.state = state
        self.last_activity = time.time()
    
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
    
    def getAddress(self):
        return self.addr
    
    def updateActivity(self):
        """Update the last activity timestamp"""
        self.last_activity = time.time()
    
    def isInactive(self, timeout=120):
        """Check if connection has been inactive for longer than timeout"""
        return (time.time() - self.last_activity) > timeout
    
    def setPlayerName(self, name):
        self.player_name = name
    
    def getPlayerName(self):
        return self.player_name if self.player_name else f"Player-{self.addr[1]}"
    
    def setPlayerSymbol(self, symbol):
        self.player_symbol = symbol
    
    def getPlayerSymbol(self):
        return self.player_symbol
    
    def setGameId(self, game_id):
        self.game_id = game_id
    
    def getGameId(self):
        return self.game_id