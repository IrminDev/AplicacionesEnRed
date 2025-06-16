import socket
import threading
import json
import logging
import sys
import os
import time
import select
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Default settings
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 54321

class TicTacToeClient:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        
        # Connection
        self.socket = None
        self.running = False
        
        # Game state
        self.grid = []
        self.grid_size = 3
        self.my_symbol = 'X'
        self.player_name = "Player"
        
        # Synchronization
        self.lock = threading.Lock()
        self.my_turn = threading.Event()
        self.game_over = threading.Event()
        self.connection_lost = threading.Event()
        
        # Listener thread
        self.listener = None
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logging.info(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return False
    
    def start(self):
        if not self.connect():
            return False
            
        self.running = True
        
        # Start listener thread
        self.listener = threading.Thread(target=self.listen_for_messages, name="Listener")
        self.listener.daemon = True
        self.listener.start()
        
        # Main game loop
        try:
            self.play_game()
        except KeyboardInterrupt:
            logging.info("Client interrupted by user")
        finally:
            self.disconnect()
            
        return True
    
    def disconnect(self):
        self.running = False
        
        # Signal threads to exit
        self.my_turn.set()
        self.game_over.set()
        self.connection_lost.set()
        
        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            
        logging.info("Disconnected from server")
    
    def listen_for_messages(self):
        try:
            # Wait for initial name prompt
            raw_data = self.socket.recv(1024).decode('utf-8').strip()
            if "Enter your name" in raw_data:
                logging.info("Received name prompt")
                
                # Get name from user
                name = input("Enter your name: ").strip()
                self.player_name = name if name else f"Player_{int(time.time() % 1000)}"
                
                # Send name to server
                self.socket.sendall(f"{self.player_name}\n".encode('utf-8'))
                logging.info(f"Sent player name: {self.player_name}")
            
            # Main message loop
            while self.running:
                # Use select for non-blocking socket read
                ready, _, _ = select.select([self.socket], [], [], 0.1)
                
                if not ready:
                    continue
                    
                data = self.socket.recv(4096)
                if not data:
                    logging.warning("Connection closed by server")
                    self.connection_lost.set()
                    self.running = False
                    break
                
                # Process messages (may be multiple messages)
                messages = data.decode('utf-8').strip().split('\n')
                for msg in messages:
                    if not msg:
                        continue
                        
                    try:
                        message = json.loads(msg)
                        self.process_message(message)
                    except json.JSONDecodeError:
                        logging.warning(f"Received non-JSON message: {msg}")
                        
        except Exception as e:
            if self.running:
                logging.error(f"Listener error: {e}")
                self.connection_lost.set()
                self.running = False
    
    def process_message(self, message):
        msg_type = message.get("type")
        
        with self.lock:
            if msg_type == "info":
                info_msg = message.get("message", "")
                print(f"\n[INFO] {info_msg}")
                logging.info(f"Server info: {info_msg}")
                
            elif msg_type == "error":
                error_msg = message.get("message", "")
                print(f"\n[ERROR] {error_msg}")
                logging.error(f"Server error: {error_msg}")
                
            elif msg_type == "game_setup":
                self.grid_size = message.get("grid_size", 3)
                self.my_symbol = message.get("symbol", "X")
                self.grid = [[" " for _ in range(self.grid_size)] for _ in range(self.grid_size)]
                logging.info(f"Game setup: size={self.grid_size}x{self.grid_size}, symbol={self.my_symbol}")
                self.print_grid()
                
            elif msg_type == "game_update":
                status = message.get("status")
                if status == "start":
                    self.game_over.clear()
                    print("\n*** Game Starting! ***")
                    self.print_grid()
                elif status == "clients_turn":
                    self.my_turn.set()
                    print("\n>>> Your Turn! <<<")
                elif status in ["server_turn", "opponent_turn"]:
                    self.my_turn.clear()
                    print("\n--- Opponent's Turn ---")
            
            elif msg_type == "move_ack":
                symbol = message.get("symbol")
                row, col = message.get("row"), message.get("col")
                player = message.get("player")
                
                # Update grid
                self.update_grid(row, col, symbol)
                self.print_grid()
                
                if player == self.player_name:
                    print(f"\nYou placed {symbol} at ({row},{col})")
                else:
                    print(f"\nPlayer {player} placed {symbol} at ({row},{col})")
            
            elif msg_type == "opponent_move":
                symbol = message.get("symbol")
                row, col = message.get("row"), message.get("col")
                
                # Update grid
                self.update_grid(row, col, symbol)
                self.print_grid()
                print(f"\nOpponent placed {symbol} at ({row},{col})")
            
            elif msg_type == "game_over":
                winner = message.get("winner")
                
                self.print_grid()
                print("\n========== GAME OVER ==========")
                
                if winner == "Tie":
                    print("It's a tie!")
                elif winner == self.player_name:
                    print("You win!")
                elif winner == "Server":
                    print("Server wins!")
                else:
                    print(f"Winner: {winner}")
                    
                print("================================")
                
                # Set both flags to terminate
                self.my_turn.clear()
                self.game_over.set()  # This will trigger exit from the play_game loop
                self.running = False  # Also set running to false to exit all loops
                
                # Print final message
                print("\nGame ended. Exiting client...")

            elif msg_type == "disconnect":
                # Handle explicit disconnect message from server
                print(f"\n[INFO] {message.get('message', 'Disconnected from server.')}")
                self.running = False
                self.connection_lost.set()
    
    def play_game(self):
        while self.running:
            if self.connection_lost.is_set() or self.game_over.is_set():
                break
                
            # Wait for our turn with timeout
            if self.my_turn.wait(timeout=0.5):
                if not self.running:
                    break
                    
                # Get move
                try:
                    print("\nEnter your move (row,col) or 'quit': ", end="", flush=True)
                    
                    # Non-blocking input using select
                    ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                    
                    if not ready:
                        # No input yet, check if turn was revoked
                        if not self.my_turn.is_set():
                            continue
                            
                        # Keep checking for input
                        while not ready and self.my_turn.is_set() and self.running:
                            time.sleep(0.1)
                            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                    
                    if not ready:
                        continue
                        
                    move = sys.stdin.readline().strip()
                    
                    if move.lower() in ['q', 'quit', 'exit']:
                        logging.info("User quit requested")
                        break
                        
                    try:
                        row, col = map(int, move.split(','))
                        
                        # Send move to server
                        self.send_move(row, col)
                        self.my_turn.clear()  # Clear turn until server confirms
                        
                    except ValueError:
                        print("Invalid format! Use 'row,col' (e.g., '0,1')")
                        
                except KeyboardInterrupt:
                    break
    
    def send_move(self, row, col):
        if not self.socket or not self.running:
            return
            
        try:
            move = {"type": "move", "row": row, "col": col}
            move_json = json.dumps(move) + "\n"
            self.socket.sendall(move_json.encode('utf-8'))
            logging.info(f"Sent move: ({row},{col})")
        except Exception as e:
            logging.error(f"Error sending move: {e}")
            self.connection_lost.set()
    
    def update_grid(self, row, col, symbol):
        if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
            self.grid[row][col] = symbol
    
    def print_grid(self):
        if not self.grid:
            return
            
        self.clear_screen()
        
        print("\n===== Tic Tac Toe =====")
        print(f"Player: {self.player_name} ({self.my_symbol})")
        print("======================")
        
        # Print column headers
        print("   " + " ".join(str(i) for i in range(self.grid_size)))
        
        # Print rows
        for r in range(self.grid_size):
            print(f"{r} |", end="")
            for c in range(self.grid_size):
                print(f"{self.grid[r][c]}|", end="")
            print()
            
        print("======================")
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

def main():
    parser = argparse.ArgumentParser(description="Tic Tac Toe Client")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Server host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    
    args = parser.parse_args()
    
    # Start client - no retry loop
    client = TicTacToeClient(host=args.host, port=args.port)
    
    try:
        # Run once, no reconnect
        client.start()
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
    
    print("Client terminated.")

if __name__ == "__main__":
    main()