import socket
import threading
import json
import random
import logging
import sys
import time
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Game configuration
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 54321
DEFAULT_GRID_SIZE = 3
MIN_PLAYERS = 2
MAX_PLAYERS = 5

class GameManager:
    def __init__(self, size=3):
        self.size = size
        self.grid = [[" " for _ in range(size)] for _ in range(size)]
        self.turn = "X"  # X for player, O for server
        self.game_over = False
        self.winner = None
        self.lock = threading.Lock()
        self.players = {}  # Socket -> player name
        
    def reset(self):
        with self.lock:
            self.grid = [[" " for _ in range(self.size)] for _ in range(self.size)]
            self.turn = "X"
            self.game_over = False
            self.winner = None
            logging.info("Game reset")
    
    def make_move(self, player, row, col):
        with self.lock:
            if self.game_over or not self.is_valid_move(row, col):
                return False
            
            self.grid[row][col] = self.turn
            
            # Check for win
            if self._check_win(self.turn):
                self.game_over = True
                self.winner = player if self.turn == "X" else "Server"
                return True
                
            # Check for tie
            if self._check_tie():
                self.game_over = True
                self.winner = "Tie"
                return True
                
            # Switch turn
            self.turn = "O" if self.turn == "X" else "X"
            return True
    
    def make_server_move(self):
        with self.lock:
            if self.game_over or self.turn != "O":
                return None
                
            # Find empty cells
            empty_cells = []
            for r in range(self.size):
                for c in range(self.size):
                    if self.grid[r][c] == " ":
                        empty_cells.append((r, c))
            
            if not empty_cells:
                return None
                
            # Make random move
            row, col = random.choice(empty_cells)
            self.grid[row][col] = "O"
            
            # Check for win
            if self._check_win("O"):
                self.game_over = True
                self.winner = "Server"
                return row, col
                
            # Check for tie
            if self._check_tie():
                self.game_over = True
                self.winner = "Tie"
                return row, col
                
            # Switch turn
            self.turn = "X"
            return row, col
    
    # Fix for is_valid_move method
    def is_valid_move(self, row, col):
        # No lock needed since caller should hold the lock
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        return self.grid[row][col] == " "

    # Fix for check_win method
    def _check_win(self, symbol):
        # No lock needed since caller should hold the lock
        # Check rows
        for r in range(self.size):
            if all(self.grid[r][c] == symbol for c in range(self.size)):
                return True
        
        # Check columns
        for c in range(self.size):
            if all(self.grid[r][c] == symbol for r in range(self.size)):
                return True
        
        # Check diagonals
        if all(self.grid[i][i] == symbol for i in range(self.size)):
            return True
            
        if all(self.grid[i][self.size-1-i] == symbol for i in range(self.size)):
            return True
            
        return False

    # Fix for check_tie method
    def _check_tie(self):
        # No lock needed since caller should hold the lock
        return all(self.grid[r][c] != " " for r in range(self.size) for c in range(self.size))

class TicTacToeServer:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, grid_size=DEFAULT_GRID_SIZE):
        self.host = host
        self.port = port
        self.grid_size = grid_size
        
        # Synchronization primitives
        self.clients_lock = threading.Lock()
        self.clients = {}  # Socket -> player name
        self.game_manager = GameManager(size=grid_size)
        
        # Start/stop control
        self.running = False
        self.server_socket = None
        
        # Game state control
        self.game_state_cond = threading.Condition()
        self.game_active = False
        self.game_over_event = threading.Event()
        self.game_over_event.set()  # Initially no game is running
        
        # Player management
        self.player_semaphore = threading.Semaphore(MAX_PLAYERS)
        self.player_barrier = threading.Barrier(
            MIN_PLAYERS, 
            action=lambda: logging.info("Barrier passed! Game starting."),
            timeout=300.0  # Increase timeout to 5 minutes (was likely 60 seconds)
        )
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logging.info(f"Server listening on {self.host}:{self.port}")
            logging.info(f"Grid size: {self.grid_size}x{self.grid_size}")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    logging.info(f"Connection from {client_addr}")
                    
                    # Start client handler thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_addr),
                        name=f"Client-{client_addr[1]}"
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    logging.error(f"Error accepting connection: {e}")
                    
        except KeyboardInterrupt:
            logging.info("Server shutting down...")
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        self.running = False
        
        # Notify clients
        with self.clients_lock:
            for sock in list(self.clients.keys()):
                try:
                    self.send_message(sock, {"type": "info", "message": "Server shutting down"})
                    sock.close()
                except:
                    pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        logging.info("Server shutdown complete")
    
    def send_message(self, client_socket, message):
        try:
            message_json = json.dumps(message) + "\n"
            client_socket.sendall(message_json.encode('utf-8'))
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            self.remove_client(client_socket)
    
    def broadcast(self, message, exclude=None):
        with self.clients_lock:
            sockets = list(self.clients.keys())
        
        for sock in sockets:
            if sock != exclude:
                self.send_message(sock, message)
    
    def remove_client(self, client_socket):
        player_name = None
        with self.clients_lock:
            if client_socket in self.clients:
                player_name = self.clients.pop(client_socket)
        
        if not player_name:
            return
            
        logging.info(f"Client {player_name} disconnected")
        
        # Handle game state changes if necessary
        with self.game_state_cond:
            if self.game_active:
                # Game was active, handle premature end
                self.game_active = False
                self.game_over_event.set()
                self.broadcast({"type": "game_over", "winner": "Opponent Disconnected"})
                self.game_state_cond.notify_all()
            
            # Check if barrier needs to be aborted
            remaining = len(self.clients)
            if remaining < MIN_PLAYERS:
                try:
                    self.player_barrier.abort()
                    logging.info("Barrier aborted due to player disconnect")
                except:
                    pass
        
        # Release player semaphore
        self.player_semaphore.release()
        
        # Notify remaining players
        self.broadcast({"type": "info", "message": f"Player {player_name} disconnected"})
        
        try:
            client_socket.close()
        except:
            pass
    
    def reset_game(self):
        with self.game_state_cond:
            logging.info("Game reset")
            
            # Reset the game state
            self.game_manager.reset()
            self.game_active = False
            self.game_over_event.set()
            
            # Close all client connections - new behavior
            with self.clients_lock:
                # Send game over notification to all clients (already sent in the game loop)
                # Now also send a disconnect message
                for sock in list(self.clients.keys()):
                    try:
                        self.send_message(sock, {
                            "type": "disconnect",
                            "message": "Game ended. Please restart client to play again."
                        })
                        # Don't close the sockets here - let the clients disconnect naturally
                        # The threads will clean up
                    except:
                        pass
                
            self.game_state_cond.notify_all()
    
    def handle_client(self, client_socket, client_addr):
        player_name = None
        acquired_semaphore = False
        
        try:
            # Try to acquire player slot
            if not self.player_semaphore.acquire(blocking=False):
                self.send_message(client_socket, {"type": "error", "message": "Server full"})
                client_socket.close()
                return
                
            acquired_semaphore = True
            
            # Get player name
            client_socket.sendall(b"Enter your name: \n")
            name_data = client_socket.recv(1024).decode('utf-8').strip()
            
            if not name_data:
                self.send_message(client_socket, {"type": "error", "message": "Invalid name"})
                return
                
            player_name = name_data
            logging.info(f"Player {player_name} connected from {client_addr}")
            
            # Add to client list
            with self.clients_lock:
                self.clients[client_socket] = player_name
            
            # Send welcome messages
            self.send_message(client_socket, {
                "type": "info", 
                "message": f"Welcome, {player_name}!"
            })
            
            self.send_message(client_socket, {
                "type": "game_setup", 
                "grid_size": self.grid_size,
                "symbol": "X"
            })
            
            self.broadcast({
                "type": "info", 
                "message": f"Player {player_name} has joined"
            }, exclude=client_socket)
            
            # Wait if game in progress
            with self.game_state_cond:
                if self.game_active:
                    self.send_message(client_socket, {
                        "type": "info", 
                        "message": "Game in progress. Please wait..."
                    })
                    
                    self.game_state_cond.wait_for(lambda: not self.game_active)
                    
            # Wait for minimum players
            self.send_message(client_socket, {
                "type": "info", 
                "message": f"Waiting for players ({len(self.clients)}/{MIN_PLAYERS})"
            })
            
            # Wait at barrier
            try:
                result = self.player_barrier.wait()
                logging.info(f"Player {player_name} passed barrier (result={result})")
                
                # First thread through barrier starts game
                if result == 0:
                    with self.game_state_cond:
                        self.game_active = True
                        self.game_over_event.clear()
                        self.broadcast({
                            "type": "game_update",
                            "status": "start",
                            "message": "Game starting!"
                        })
                        
                        # Short delay to ensure all clients receive the start message
                        time.sleep(0.1)
                        
                        self.broadcast({
                            "type": "game_update",
                            "status": "clients_turn"
                        })
                        
                        logging.info(f"Game starting with {len(self.clients)} players")
                else:
                    # Non-initializing clients need to wait briefly for game setup
                    logging.info(f"Player {player_name} waiting for game setup")
                    time.sleep(0.2)  # Give the initializing thread time to set up
            except threading.BrokenBarrierError as e:
                # Instead of disconnecting the client immediately, diagnose the issue
                logging.warning(f"Barrier broken for {player_name}: {str(e)}")
                
                # Check if we still have clients to start a game
                client_count = 0
                with self.clients_lock:
                    client_count = len(self.clients)
                    # Important: Check if this is the only player now
                    is_only_player = client_count == 1 and client_socket in self.clients
                
                # If we have exactly the minimum number needed or we JUST reached minimum, try to create a new barrier
                # and start a game immediately
                if client_count >= MIN_PLAYERS:
                    logging.info(f"We have {client_count} players, which is enough to start a game")
                    try:
                        # Reset the barrier
                        with self.game_state_cond:
                            # Create fresh barrier since the previous one broke
                            self.player_barrier = threading.Barrier(
                                MIN_PLAYERS, 
                                action=lambda: logging.info("New barrier passed! Game starting."),
                                timeout=300.0
                            )
                        
                        # Since we have enough players, start the game immediately
                        logging.info(f"Starting game immediately with {client_count} players")
                        with self.game_state_cond:
                            self.game_active = True
                            self.game_over_event.clear()
                            self.broadcast({
                                "type": "game_update",
                                "status": "start",
                                "message": "Game starting!"
                            })
                            
                            # Short delay to ensure all clients receive messages
                            time.sleep(0.1)
                            
                            # Let clients know it's their turn
                            self.broadcast({
                                "type": "game_update",
                                "status": "clients_turn"
                            })
                        
                        # Continue to game loop
                        logging.info(f"Player {player_name} entering game loop after barrier reset")
                            
                    except Exception as reset_error:
                        logging.error(f"Error starting game after barrier reset: {reset_error}")
                        self.send_message(client_socket, {
                            "type": "error",
                            "message": "Game start failed - internal error"
                        })
                        return
                elif is_only_player:
                    # This is the only player, wait for more
                    self.send_message(client_socket, {
                        "type": "info",
                        "message": f"Waiting for more players... (1/{MIN_PLAYERS})"
                    })
                    
                    # Continue to game loop which will handle waiting
                else:
                    # Something else went wrong
                    self.send_message(client_socket, {
                        "type": "error",
                        "message": "Game start failed - please try again later"
                    })
                    return  # Exit the function
                        
            # Log entry to game loop
            logging.info(f"Player {player_name} entering game loop")
            
            # Game loop
            while self.running and client_socket in self.clients:
                try:
                    # Check for game over - but we need to distinguish between "game ended" and "waiting for game to start"
                    waiting_for_players = False
                    with self.clients_lock:
                        waiting_for_players = len(self.clients) < MIN_PLAYERS
                    
                    if self.game_over_event.is_set() and not waiting_for_players:
                        # This is a true game over condition, not just waiting for players
                        logging.info(f"Game over detected, {player_name} exiting game loop")
                        # Break out of the loop - game is actually over
                        break
                    elif self.game_over_event.is_set() and waiting_for_players:
                        # We're just waiting for more players to join
                        # Sleep a bit to avoid busy-waiting and then continue
                        time.sleep(1.0)
                        continue
                    
                    # Only try to receive data if it's the client's turn
                    with self.game_manager.lock:
                        is_clients_turn = self.game_manager.turn == "X"
                    
                    if not is_clients_turn:
                        # If it's not the client's turn, just wait a bit and check again
                        time.sleep(0.1)
                        continue
                    
                    # Set a timeout for receiving data
                    client_socket.settimeout(0.5)
                    
                    # Try to receive data - handle timeout properly
                    try:
                        data = client_socket.recv(1024)
                        if not data:
                            logging.info(f"No data from {player_name}, disconnecting")
                            break
                        
                        message = data.decode('utf-8').strip()
                        if not message:
                            continue
                        
                        # Process the received message
                        logging.info(f"Received from {player_name}: {message}")
                        
                        # Try to parse as JSON
                        try:
                            move_data = json.loads(message)
                            logging.info(f"Processing move from {player_name}: {move_data}")
                            
                            if move_data.get("type") == "move":
                                row, col = move_data.get("row"), move_data.get("col")
                                
                                # Use a single lock acquisition for the entire operation
                                with self.game_manager.lock:
                                    logging.info(f"Current turn: {self.game_manager.turn}")
                                    
                                    if self.game_manager.turn != "X":
                                        logging.warning(f"Not {player_name}'s turn")
                                        self.send_message(client_socket, {
                                            "type": "error",
                                            "message": "Not your turn"
                                        })
                                        continue
                                    
                                    # Check move validity directly within the same lock
                                    if not (0 <= row < self.game_manager.size and 
                                            0 <= col < self.game_manager.size and 
                                            self.game_manager.grid[row][col] == " "):
                                        logging.warning(f"Invalid move by {player_name}: ({row},{col})")
                                        self.send_message(client_socket, {
                                            "type": "error",
                                            "message": "Invalid move"
                                        })
                                        continue
                                    
                                    logging.info(f"Valid move by {player_name}: ({row},{col})")
                                    
                                    # Make move directly without nested lock
                                    self.game_manager.grid[row][col] = "X"
                                    
                                    # Check for win (directly, no nested lock)
                                    game_over = False
                                    winner = None
                                    
                                    # Check win (inline)
                                    if self.game_manager._check_win("X"):
                                        self.game_manager.game_over = True
                                        self.game_manager.winner = player_name
                                        game_over = True
                                        winner = player_name
                                    # Check tie (inline)
                                    elif self.game_manager._check_tie():
                                        self.game_manager.game_over = True
                                        self.game_manager.winner = "Tie"
                                        game_over = True
                                        winner = "Tie"
                                    else:
                                        # Switch turn
                                        self.game_manager.turn = "O"
                                
                                # Broadcast move (outside the lock)
                                move_msg = {
                                    "type": "move_ack",
                                    "symbol": "X",
                                    "row": row,
                                    "col": col,
                                    "player": player_name
                                }
                                logging.info(f"Broadcasting move: {move_msg}")
                                self.broadcast(move_msg)
                                
                                # Check for game over
                                if game_over:
                                    logging.info(f"Game over after player move. Winner: {winner}")
                                    self.broadcast({
                                        "type": "game_over",
                                        "winner": winner
                                    })
                                    self.reset_game()
                                    continue
                                
                                # Server's turn
                                logging.info("Server making move...")
                                server_move = None
                                
                                # Get server move with single lock acquisition
                                with self.game_manager.lock:
                                    if self.game_manager.turn == "O":
                                        # Find empty cells
                                        empty_cells = []
                                        for r in range(self.game_manager.size):
                                            for c in range(self.game_manager.size):
                                                if self.game_manager.grid[r][c] == " ":
                                                    empty_cells.append((r, c))
                                        
                                        if empty_cells:
                                            # Make random move
                                            s_row, s_col = random.choice(empty_cells)
                                            self.game_manager.grid[s_row][s_col] = "O"
                                            server_move = (s_row, s_col)
                                            
                                            # Check for win
                                            if self.game_manager._check_win("O"):
                                                self.game_manager.game_over = True
                                                self.game_manager.winner = "Server"
                                                game_over = True
                                                winner = "Server"
                                            # Check for tie
                                            elif self.game_manager._check_tie():
                                                self.game_manager.game_over = True
                                                self.game_manager.winner = "Tie"
                                                game_over = True
                                                winner = "Tie"
                                            else:
                                                # Switch turn
                                                self.game_manager.turn = "X"
                                
                                # Process server move results outside lock
                                if server_move:
                                    s_row, s_col = server_move
                                    logging.info(f"Server moved: ({s_row},{s_col})")
                                    self.broadcast({
                                        "type": "opponent_move",
                                        "symbol": "O",
                                        "row": s_row,
                                        "col": s_col
                                    })
                                    
                                    # Check for game over
                                    if game_over:
                                        logging.info(f"Game over after server move. Winner: {winner}")
                                        self.broadcast({
                                            "type": "game_over",
                                            "winner": winner
                                        })
                                        self.reset_game()
                                    else:
                                        # Back to clients
                                        logging.info("Back to clients' turn")
                                        self.broadcast({
                                            "type": "game_update",
                                            "status": "clients_turn"
                                        })
                        except json.JSONDecodeError:
                            # Try plain text format
                            logging.info(f"Non-JSON message, trying plain text format: {message}")
                            if "," in message:
                                try:
                                    parts = message.split(",")
                                    if len(parts) == 2:
                                        row, col = int(parts[0].strip()), int(parts[1].strip())
                                        logging.info(f"Parsed plain text move: ({row},{col})")
                                        
                                        # Process move (similar logic as JSON version)
                                        with self.game_manager.lock:
                                            if self.game_manager.turn != "X":
                                                self.send_message(client_socket, {
                                                    "type": "error",
                                                    "message": "Not your turn"
                                                })
                                                continue
                                            
                                            # Rest of move processing same as above
                                    else:
                                        logging.warning(f"Invalid format: {message}")
                                        self.send_message(client_socket, {
                                            "type": "error",
                                            "message": "Invalid format"
                                        })
                                except ValueError as ve:
                                    logging.warning(f"Invalid format: {message} - {ve}")
                                    self.send_message(client_socket, {
                                        "type": "error",
                                        "message": "Invalid format"
                                    })
                            else:
                                logging.warning(f"Unknown message format: {message}")
                                self.send_message(client_socket, {
                                    "type": "error",
                                    "message": "Unknown message format"
                                })
                    except socket.timeout:
                        # This is normal - just continue the loop
                        continue
                    
                except Exception as e:
                    logging.error(f"Error processing client message: {e}")
                    break
        
        except Exception as e:
            logging.error(f"Error handling client {player_name}: {e}")
        finally:
            # Clean up
            if player_name:
                self.remove_client(client_socket)
            elif acquired_semaphore:
                self.player_semaphore.release()
                try:
                    client_socket.close()
                except:
                    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tic Tac Toe Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port number")
    parser.add_argument("--grid-size", type=int, default=DEFAULT_GRID_SIZE, help="Grid size")
    
    args = parser.parse_args()
    
    server = TicTacToeServer(
        host=args.host,
        port=args.port,
        grid_size=args.grid_size
    )
    
    server.start()