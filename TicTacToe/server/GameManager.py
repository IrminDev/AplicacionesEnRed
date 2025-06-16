import random
import threading
import logging # Added

class GameManager:
    def __init__(self, size=3):
        self.size = size
        self.grid = None
        self.players = {} # {client_socket: player_name} - Server manages this now primarily
        self.turn = "X" # 'X' for clients, 'O' for server
        self.game_over = False
        self.winner = None
        self.lock = threading.Lock() # Internal lock for game state
        self.reset_game()

    def reset_game(self):
        with self.lock:
            self.grid = [[" " for _ in range(self.size)] for _ in range(self.size)]
            self.turn = "X"
            self.game_over = False
            self.winner = None
            logging.info(f"GameManager reset: Size {self.size}x{self.size}")

    # Server now manages the clients dictionary primarily
    def add_player(self, client_socket, player_name):
         # This might not be needed if server handles the main dict
         pass

    def remove_player(self, client_socket):
         # This might not be needed if server handles the main dict
         pass

    def get_current_state_summary(self): # Example if needed, but server sends specific updates
        with self.lock:
            return {
                "turn": self.turn,
                "game_over": self.game_over,
                "winner": self.winner
            }

    def make_player_move(self, player_name, row, col):
        with self.lock:
            if self.game_over:
                return False, "Game is over."
            if self.turn != "X":
                return False, "Not clients' turn."
            if not (0 <= row < self.size and 0 <= col < self.size):
                return False, "Move out of bounds."
            if self.grid[row][col] != " ":
                return False, "Cell already occupied."

            self.grid[row][col] = "X"
            logging.debug(f"GameManager: Player '{player_name}' moved to ({row},{col})")

            if self._check_win("X"):
                self.game_over = True
                self.winner = "Clients" # Or use player_name if only one client plays 'X'
                logging.info("GameManager: Clients win.")
                return True, None # Move successful, game ended

            if self._check_tie():
                self.game_over = True
                self.winner = "Tie"
                logging.info("GameManager: Tie.")
                return True, None # Move successful, game ended

            self.turn = "O"
            return True, None # Move successful, game continues

    def make_server_move(self):
        with self.lock:
            if self.game_over or self.turn != "O":
                return None # Should not happen in normal flow

            empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == " "]

            if not empty_cells: # Should be caught by tie check earlier
                logging.warning("GameManager: Server move called with no empty cells.")
                return None

            row, col = random.choice(empty_cells)
            self.grid[row][col] = "O"
            logging.debug(f"GameManager: Server moved to ({row},{col})")

            if self._check_win("O"):
                self.game_over = True
                self.winner = "Server"
                logging.info("GameManager: Server wins.")
                return row, col # Return move even if game ends

            if self._check_tie(): # Check tie after server move
                self.game_over = True
                self.winner = "Tie"
                logging.info("GameManager: Tie.")
                return row, col # Return move even if game ends

            self.turn = "X"
            return row, col # Return the move made

    def _check_win(self, symbol):
        # Check rows, columns, diagonals (same as before)
        for r in range(self.size):
            if all(self.grid[r][c] == symbol for c in range(self.size)): return True
        for c in range(self.size):
            if all(self.grid[r][c] == symbol for r in range(self.size)): return True
        if all(self.grid[i][i] == symbol for i in range(self.size)): return True
        if all(self.grid[i][self.size - 1 - i] == symbol for i in range(self.size)): return True
        return False

    def _check_tie(self):
        return all(self.grid[r][c] != " " for r in range(self.size) for c in range(self.size))

    def is_game_over(self):
        with self.lock:
            return self.game_over

    def end_game_prematurely(self, reason="Unknown"):
         """Force the game to end."""
         with self.lock:
             if not self.game_over:
                 self.game_over = True
                 # Decide winner based on context, or set to None/Draw
                 self.winner = f"Game Ended ({reason})"
                 logging.warning(f"Game ended prematurely by GameManager due to: {reason}")
