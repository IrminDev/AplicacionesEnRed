import random
import time
import threading
import uuid

class TicTacToeGame:
    def __init__(self, size=3, max_players=5, difficulty=1):
        self.id = str(uuid.uuid4())[:8]
        self.size = size
        self.max_players = max_players
        self.difficulty = difficulty
        self.grid = [[" " for _ in range(size)] for _ in range(size)]
        self.players = []
        self.game_over = False
        self.winner = None
        self.current_turn = "player"  # "player" or "server"
        self.last_move = None
        self.server_thinking = False
        self.lock = threading.RLock()  # Use RLock instead of Lock to allow recursive locking

    def add_player(self, player_state):
        """Add player to the game"""
        with self.lock:
            # Check if player is already in game
            for player in self.players:
                if player.getPlayerName() == player_state.getPlayerName():
                    return True
                    
            # Check if game is full
            if len(self.players) >= self.max_players:
                return False
                
            # Add player
            player_state.setState(player_state.state.RUNNING)
            player_state.setGameId(self.id)
            player_state.setPlayerSymbol("X")
            self.players.append(player_state)
            print(f"Added player {player_state.getPlayerName()} to game {self.id}")
            return True

    def make_move(self, player_state, row, col):
        """Process a player's move"""
        with self.lock:
            # Game state validation
            if self.game_over:
                return False, "Game is already over"
                
            if self.current_turn != "player":
                return False, "It's not your turn"
                
            # Move validation
            if not (0 <= row < self.size and 0 <= col < self.size):
                return False, "Invalid coordinates"
                
            if self.grid[row][col] != " ":
                return False, "Cell already occupied"
                
            # Make the move
            self.grid[row][col] = "X"
            self.last_move = (row, col)
            
            # Check for win
            if self._check_win("X"):
                self.game_over = True
                self.winner = player_state.getPlayerName()
                return True, "win"
                
            # Check for tie
            if self._check_tie():
                self.game_over = True
                return True, "tie"
                
            # Switch turn
            self.current_turn = "server"
            return True, "valid"

    def make_server_move(self):
        """Make a move for the server"""
        with self.lock:
            if self.game_over or self.current_turn != "server":
                return None
                
            self.server_thinking = True
            
            # Find a move based on difficulty
            if self.difficulty == 1:
                # Easy - random
                row, col = self._make_random_move()
            elif self.difficulty == 2:
                # Medium - try to win, otherwise random
                row, col = self._make_medium_move()
            else:
                # Hard - try to win, try to block, otherwise best move
                row, col = self._make_hard_move()
                
            self.server_thinking = False
            
            if row is None or col is None:
                # No move available
                if self._check_tie():
                    self.game_over = True
                    return "tie"
                return None
                
            # Make the move
            self.grid[row][col] = "O"
            self.last_move = (row, col)
            
            # Check for win
            if self._check_win("O"):
                self.game_over = True
                self.winner = "Server"
                return "win"
                
            # Check for tie
            if self._check_tie():
                self.game_over = True
                return "tie"
                
            # Switch turn
            self.current_turn = "player"
            return "valid"
    
    def _make_random_move(self):
        """Make a random move"""
        empty_cells = []
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == " ":
                    empty_cells.append((i, j))
                    
        if not empty_cells:
            return None, None
            
        return random.choice(empty_cells)
    
    def _make_medium_move(self):
        """Try to win, otherwise random"""
        # First, check if we can win
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == " ":
                    # Try the move
                    self.grid[i][j] = "O"
                    if self._check_win("O"):
                        self.grid[i][j] = " "  # Undo test move
                        return i, j
                    self.grid[i][j] = " "  # Undo test move
                    
        # No winning move, make a random one
        return self._make_random_move()
    
    def _make_hard_move(self):
        """Try to win, block opponent, or make best move"""
        # First, check if we can win
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == " ":
                    # Try the move
                    self.grid[i][j] = "O"
                    if self._check_win("O"):
                        self.grid[i][j] = " "  # Undo test move
                        return i, j
                    self.grid[i][j] = " "  # Undo test move
                    
        # Next, check if we need to block opponent
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == " ":
                    # Try opponent's move
                    self.grid[i][j] = "X"
                    if self._check_win("X"):
                        self.grid[i][j] = " "  # Undo test move
                        return i, j
                    self.grid[i][j] = " "  # Undo test move
                    
        # For 3x3 grids, prefer center, then corners, then sides
        if self.size == 3:
            # Try center
            if self.grid[1][1] == " ":
                return 1, 1
                
            # Try corners
            corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
            random.shuffle(corners)
            for i, j in corners:
                if self.grid[i][j] == " ":
                    return i, j
                    
            # Try sides
            sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
            random.shuffle(sides)
            for i, j in sides:
                if self.grid[i][j] == " ":
                    return i, j
        
        # Fallback to random move
        return self._make_random_move()

    def _check_win(self, symbol):
        """Check if player with given symbol has won"""
        # Check rows
        for i in range(self.size):
            if all(self.grid[i][j] == symbol for j in range(self.size)):
                return True
                
        # Check columns
        for j in range(self.size):
            if all(self.grid[i][j] == symbol for i in range(self.size)):
                return True
                
        # Check diagonals
        if all(self.grid[i][i] == symbol for i in range(self.size)):
            return True
            
        if all(self.grid[i][self.size-1-i] == symbol for i in range(self.size)):
            return True
            
        return False

    def _check_tie(self):
        """Check if game is tied (no empty cells)"""
        return all(self.grid[i][j] != " " for i in range(self.size) for j in range(self.size))

    def get_state(self):
        """Get the current game state"""
        with self.lock:
            state = {
                "id": self.id,
                "grid": [row[:] for row in self.grid],  # Make a deep copy
                "size": self.size,
                "players": [p.getPlayerName() for p in self.players],
                "current_turn": self.current_turn,
                "is_player_turn": self.current_turn == "player",
                "game_over": self.game_over,
                "winner": self.winner,
                "is_tie": self.game_over and not self.winner,
                "timestamp": time.time()
            }
            return state

    def remove_player(self, player_state):
        """Remove a player from the game"""
        with self.lock:
            for i, player in enumerate(self.players):
                if player.getPlayerName() == player_state.getPlayerName():
                    self.players.pop(i)
                    break
            # Return True if no players left, False otherwise
            return len(self.players) == 0


class GameManager:
    def __init__(self):
        self.active_game = None
        self.lock = threading.RLock()  # Use RLock for recursive locking
        self.grid_size = 3
        self.max_players = 5
        self.difficulty = 1
        
    def set_config(self, grid_size=3, max_players=5, difficulty=1):
        """Set game configuration"""
        with self.lock:
            if grid_size not in [3, 4, 5]:
                grid_size = 3
            self.grid_size = grid_size
            self.max_players = max_players
            self.difficulty = difficulty
        
    def add_player(self, player_state):
        """Add a player to the active game"""
        with self.lock:
            # Create game if it doesn't exist
            if not self.active_game:
                print(f"Creating new game with size {self.grid_size}")
                self.active_game = TicTacToeGame(
                    size=self.grid_size,
                    max_players=self.max_players,
                    difficulty=self.difficulty
                )
                
            # Add player to game
            success = self.active_game.add_player(player_state)
            if success:
                return self.active_game
            return None
    
    def remove_player(self, player_state):
        """Remove a player from the active game"""
        with self.lock:
            if self.active_game:
                # Remove player and check if game is empty
                if self.active_game.remove_player(player_state):
                    print("All players left, ending game")
                    self.active_game = None
                return True
            return False
    
    def get_game_state(self):
        """Get the state of the active game"""
        with self.lock:
            if self.active_game:
                return self.active_game.get_state()
            return None
    
    def end_game(self):
        """End the current game"""
        with self.lock:
            if self.active_game:
                print(f"Ending game {self.active_game.id}")
                self.active_game = None
                return True
            return False