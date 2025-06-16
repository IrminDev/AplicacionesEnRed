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
        self.current_state = initialState if initialState else self.state.STARTING
        self.player_name = f"Player-{addr[1]}"
        self.game_id = None
        self.player_symbol = None
        self.last_activity = time.time()
    
    def getState(self):
        return self.current_state
    
    def setState(self, state):
        self.current_state = state
    
    def getSocket(self):
        return self.socket
    
    def setSocket(self, socket):
        self.socket = socket
    
    def getAddress(self):
        return self.addr
        
    def getPlayerName(self):
        return self.player_name
        
    def setPlayerName(self, name):
        self.player_name = name
        
    def setGameId(self, game_id):
        self.game_id = game_id
        
    def getGameId(self):
        return self.game_id
        
    def setPlayerSymbol(self, symbol):
        self.player_symbol = symbol
        
    def getPlayerSymbol(self):
        return self.player_symbol
        
    def updateActivity(self):
        self.last_activity = time.time()
        
    def getLastActivity(self):
        return self.last_activity
    
    def getMessageQueue(self):
        # Not implemented in this version
        return []
    
    def setMessageQueue(self, message):
        # Not implemented in this version
        pass