import random
import uuid
import threading

class TicTacToeGame:
    def __init__(self, size=3):
        self.id = str(uuid.uuid4())[:8]
        self.grid = self.generateGrid(size)
        self.size = size
        self.players = []  # List of player socket states
        self.current_turn_idx = 0  # Index of player whose turn it is
        self.lock = threading.Lock()
        self.game_over = False
        self.winner = None
    
    def generateGrid(self, n):
        return [[" " for _ in range(n)] for _ in range(n)]
    
    def addPlayer(self, player_state):
        """Add a player to the game"""
        with self.lock:
            if len(self.players) >= 2:
                return False
            
            player_state.setGameId(self.id)
            player_state.setState(player_state.state.RUNNING)
            
            # Assign X to first player, O to second
            symbol = "X" if len(self.players) == 0 else "O"
            player_state.setPlayerSymbol(symbol)
            
            self.players.append(player_state)
            return True
    
    def makeMove(self, player_state, row, col):
        """Make a move on the game board"""
        with self.lock:
            if self.game_over:
                return False, "Game is over"
                
            # Check if it's this player's turn
            if self.players[self.current_turn_idx] != player_state:
                return False, "Not your turn"
            
            # Check if move is valid
            if not (0 <= row < self.size and 0 <= col < self.size):
                return False, "Invalid coordinates"
                
            if self.grid[row][col] != " ":
                return False, "Cell already occupied"
            
            # Make the move
            symbol = player_state.getPlayerSymbol()
            self.grid[row][col] = symbol
            
            # Check for win
            if self.checkWin(symbol):
                self.game_over = True
                self.winner = player_state
                return True, "win"
            
            # Check for tie
            if self.checkTie():
                self.game_over = True
                return True, "tie"
            
            # Switch turns
            self.current_turn_idx = (self.current_turn_idx + 1) % len(self.players)
                    
            return True, "valid"
    
    def checkWin(self, player):
        """Check if the given player has won"""
        # Check rows
        for row in self.grid:
            if all(cell == player for cell in row):
                return True
        
        # Check columns
        for col in range(self.size):
            if all(self.grid[row][col] == player for row in range(self.size)):
                return True
        
        # Check diagonals
        if all(self.grid[i][i] == player for i in range(self.size)):
            return True
            
        if all(self.grid[i][self.size-1-i] == player for i in range(self.size)):
            return True
            
        return False
    
    def checkTie(self):
        """Check if the game is a tie"""
        return all(cell != " " for row in self.grid for cell in row)
    
    def getGameState(self):
        """Get the current game state as a dictionary"""
        with self.lock:
            state = {
                "id": self.id,
                "grid": self.grid,
                "size": self.size,
                "players": [p.getPlayerName() for p in self.players],
                "current_turn": self.players[self.current_turn_idx].getPlayerName() if not self.game_over and self.players else None,
                "game_over": self.game_over,
                "winner": self.winner.getPlayerName() if self.winner else None,
                "is_tie": self.game_over and not self.winner
            }
            return state
    
    def removePlayer(self, player_state):
        """Remove a player from the game"""
        with self.lock:
            if player_state in self.players:
                self.players.remove(player_state)
                # If no players left, game is over
                if not self.players:
                    return True  # Game should be removed
            return False  # Game should continue

class GameManager:
    def __init__(self):
        self.games = {}  # Dictionary of active games
        self.waiting_players = []  # Players waiting for a game
        self.lock = threading.Lock()
    
    def createGame(self, size=3):
        """Create a new game"""
        game = TicTacToeGame(size)
        with self.lock:
            self.games[game.id] = game
        return game
    
    def findGameForPlayer(self, player_state):
        """Find a game for a player or create a new one"""
        with self.lock:
            # Try to find a game with one player
            for game_id, game in self.games.items():
                if len(game.players) == 1 and not game.game_over:
                    if game.addPlayer(player_state):
                        return game
            
            # No available games, create a new one
            game = self.createGame()
            game.addPlayer(player_state)
            return game
    
    def addToWaitingList(self, player_state):
        """Add a player to the waiting list"""
        with self.lock:
            self.waiting_players.append(player_state)
    
    def matchWaitingPlayers(self):
        """Match waiting players into games"""
        with self.lock:
            if len(self.waiting_players) >= 2:
                player1 = self.waiting_players.pop(0)
                player2 = self.waiting_players.pop(0)
                
                game = self.createGame()
                game.addPlayer(player1)
                game.addPlayer(player2)
                return game
        return None
    
    def getGame(self, game_id):
        """Get a game by ID"""
        return self.games.get(game_id)
    
    def removeGame(self, game_id):
        """Remove a game"""
        with self.lock:
            if game_id in self.games:
                del self.games[game_id]
                
    def cleanupInactiveGames(self):
        """Clean up inactive games"""
        with self.lock:
            to_remove = []
            for game_id, game in self.games.items():
                if len(game.players) == 0 or game.game_over:
                    to_remove.append(game_id)
            
            for game_id in to_remove:
                self.removeGame(game_id)