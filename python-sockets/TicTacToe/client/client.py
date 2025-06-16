import socket
import threading
import json
import time
import os
import sys

class TicTacToeClient:
    def __init__(self, host='localhost', port=65432):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.name = None
        self.game_state = None
        self.input_allowed = False
        self.waiting_for_game = False
        
    def connect(self):
        """Connect to the server"""
        try:
            print(f"Connecting to {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True
            print("Connected successfully!")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
            
    def receive_messages(self):
        """Receive and process messages from the server"""
        while self.running:
            try:
                data = self.socket.recv(1024)
                if not data:
                    print("\nDisconnected from server")
                    self.running = False
                    break
                    
                try:
                    # Try to parse as JSON
                    message = json.loads(data.decode())
                    self.handle_message(message)
                except json.JSONDecodeError:
                    # Handle as plain text
                    print(f"Server: {data.decode()}")
                    
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.running = False
                break
                
    def handle_message(self, message):
        """Handle a message from the server"""
        if 'type' not in message:
            print(f"Received message: {message}")
            return
            
        message_type = message['type']
        
        if message_type == 'welcome':
            # Server is asking for our name
            print(message.get('message', 'Welcome! Please enter your name:'))
            self.name = input("Enter your name: ")
            self.send({'name': self.name})
            
        elif message_type == 'game_start':
            # We've joined a game
            self.clear_screen()
            self.game_state = message.get('game_state')
            print(message.get('message', f'You joined as {self.name}'))
            self.waiting_for_game = False
            self.print_game()
            self.check_turn()
            
        elif message_type == 'state_update':
            # Game state update
            old_state = self.game_state
            self.game_state = message.get('game_state')
            
            # Only redraw if something important changed
            if old_state is None or self._state_changed(old_state, self.game_state):
                self.clear_screen()
                self.print_game()
                self.check_turn()
                
        elif message_type == 'move':
            # Someone made a move
            self.clear_screen()
            player = message.get('player', 'Unknown')
            symbol = message.get('symbol', '?')
            row = message.get('row', -1)
            col = message.get('col', -1)
            
            print(f"{player} placed {symbol} at position ({row}, {col})")
            
            self.game_state = message.get('game_state')
            self.print_game()
            self.check_turn()
            
        elif message_type == 'error':
            # Error message
            print(f"Error: {message.get('message', 'Unknown error')}")
            if self.input_allowed:
                print("Try again:")
                
        elif message_type == 'game_end':
            # Game ended
            self.clear_screen()
            self.game_state = message.get('game_state')
            self.print_game()
            print(f"\nGame over! {message.get('message', '')}")
            self.input_allowed = False
            print("The server will disconnect you. Reconnect to play again.")
            self.running = False
            self.socket.close()
            sys.exit(0)
            
        elif message_type == 'game_reset':
            # Game reset
            print(f"\n{message.get('message', 'Game reset')}")
            self.waiting_for_game = True
            self.game_state = None
            self.running = False
            self.socket.close()
            sys.exit(0)
            
        elif message_type == 'player_joined':
            # Player joined
            print(f"\n{message.get('player', 'Someone')} joined the game!")
            self.game_state = message.get('game_state')
            
        elif message_type == 'player_left':
            # Player left
            print(f"\n{message.get('player', 'Someone')} left the game!")
            self.game_state = message.get('game_state')

        elif message_type == 'disconnect':
            # Server wants us to disconnect
            print(f"\n{message.get('message', 'The server has disconnected you.')}")
            self.running = False    
        
    def _state_changed(self, old_state, new_state):
        """Check if important aspects of the game state changed"""
        # Check grid changes
        if old_state.get('grid') != new_state.get('grid'):
            return True
            
        # Check turn changes
        if old_state.get('current_turn') != new_state.get('current_turn'):
            return True
            
        # Check game over state
        if old_state.get('game_over') != new_state.get('game_over'):
            return True
            
        # Check player list changes
        if old_state.get('players') != new_state.get('players'):
            return True
            
        return False
            
    def check_turn(self):
        """Check if it's the player's turn and update input_allowed"""
        if not self.game_state:
            self.input_allowed = False
            return
            
        if self.game_state.get("game_over", False):
            self.input_allowed = False
            return
            
        if self.game_state.get("is_player_turn", False):
            self.input_allowed = True
            print("\nYour turn! Enter your move (row,col):")
        else:
            self.input_allowed = False
            print("\nWaiting for the other player's move...")
            
    def print_game(self):
        """Print the current game state"""
        if not self.game_state:
            print("Waiting for game to start...")
            return
            
        grid = self.game_state["grid"]
        size = len(grid)
        
        print("\nCurrent board:")
        print("  " + " ".join(str(i) for i in range(size)))
        for i, row in enumerate(grid):
            print(f"{i} " + "|".join(cell if cell != " " else "_" for cell in row))
            
        print(f"\nPlayers: {', '.join(self.game_state.get('players', []))}")
        
        if self.game_state.get("game_over"):
            if self.game_state.get("winner"):
                print(f"Winner: {self.game_state['winner']}")
            else:
                print("Game ended in a tie!")
                
    def send(self, message):
        """Send a message to the server"""
        try:
            data = json.dumps(message).encode()
            self.socket.sendall(data)
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            self.running = False
            return False
            
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
            
    def run(self):
        """Main client loop"""
        if not self.connect():
            return
            
        # Start receiving messages in a separate thread
        receiver = threading.Thread(target=self.receive_messages)
        receiver.daemon = True
        receiver.start()
        
        # Main input loop
        try:
            while self.running:
                if self.input_allowed:
                    move = input("> ")
                    if move.lower() in ["quit", "exit"]:
                        print("Exiting...")
                        break
                        
                    try:
                        parts = move.split(",")
                        if len(parts) != 2:
                            print("Invalid format. Use row,col (e.g. 1,2)")
                            continue
                            
                        row = int(parts[0].strip())
                        col = int(parts[1].strip())
                        self.send({"move": {"row": row, "col": col}})
                        # Temporarily disable input until we know the result
                        self.input_allowed = False
                    except ValueError:
                        print("Invalid input. Use numbers for row and column.")
                else:
                    # Allow interrupt while waiting
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.running = False
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass

def main():
    """Main function"""
    host = input("Enter server host [localhost]: ") or "localhost"
    try:
        port = int(input("Enter server port [65432]: ") or "65432")
    except ValueError:
        port = 65432
    
    client = TicTacToeClient(host, port)
    client.run()

if __name__ == "__main__":
    main()