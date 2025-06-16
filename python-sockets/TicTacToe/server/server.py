import socket
import os
import threading
import json
import time
import random
import argparse
import traceback
import sys
from SocketState import SocketState
from GameManager import GameManager, TicTacToeGame

class TicTacToeServer:
    def __init__(self, host='0.0.0.0', port=65432, grid_size=3, max_players=2, difficulty=1):
        self.host = host
        self.port = port
        self.grid_size = grid_size
        self.max_players = max_players
        self.difficulty = difficulty
        self.server_socket = None
        self.barrier = threading.Barrier(max_players)
        self.connections = []
        self.connections_lock = threading.Lock()
        self.game_manager = GameManager()
        self.game_manager.set_config(grid_size, max_players, difficulty)
        self.running = False
        
    def start(self):
        """Start the server"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print(f"Server started on {self.host}:{self.port}")
        print(f"Grid size: {self.grid_size}x{self.grid_size}, Max players: {self.max_players}")
        print(f"Difficulty level: {self.difficulty}")
        
        # Start game processing thread
        threading.Thread(target=self.game_processor, daemon=True).start()
        
        # Start state broadcasting thread
        threading.Thread(target=self.state_broadcaster, daemon=True).start()
        
        try:
            while self.running:
                client_socket, client_addr = self.server_socket.accept()
                print(f"New connection from {client_addr}")
                
                with self.connections_lock:
                    self.connections.append(client_socket)
                
                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_addr, self.barrier),
                    daemon=True
                ).start()
                
        except KeyboardInterrupt:
            print("\nShutting down server...")
        except Exception as e:
            print(f"Server error: {e}")
            traceback.print_exc()
        finally:
            self.stop()
            
    def stop(self):
        """Stop the server"""
        self.running = False
        with self.connections_lock:
            for conn in self.connections:
                try:
                    conn.close()
                except:
                    pass
            self.connections.clear()
            
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
    def broadcast(self, message, exclude=None):
        """Broadcast a message to all clients except the excluded one"""
        with self.connections_lock:
            for conn in self.connections:
                if conn != exclude:
                    try:
                        conn.sendall(json.dumps(message).encode())
                    except Exception as e:
                        print(f"Error broadcasting: {e}")
                        
    def send_message(self, client_socket, message):
        """Send a message to a specific client"""
        try:
            client_socket.sendall(json.dumps(message).encode())
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
            
    def game_processor(self):
        """Process server moves in the game"""
        while self.running:
            try:
                game = self.game_manager.active_game
                if game and not game.game_over and game.current_turn == "server" and not game.server_thinking:
                    # Simulate server thinking
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # Make server move
                    result = game.make_server_move()
                    if result:
                        state = game.get_state()
                        last_move = game.last_move
                        
                        self.broadcast({
                            "type": "move",
                            "player": "Server",
                            "symbol": "O",
                            "row": last_move[0],
                            "col": last_move[1],
                            "game_state": state
                        })
                        
                        if result in ["win", "tie"]:
                            self.handle_game_end(game)
            except Exception as e:
                print(f"Error in game processor: {e}")
                traceback.print_exc()
                
            time.sleep(0.1)
            
    def state_broadcaster(self):
        """Periodically broadcast game state updates"""
        last_state = None
        while self.running:
            try:
                current_state = self.game_manager.get_game_state()
                if current_state:
                    # Compare only relevant parts of the state
                    if last_state is None or self._state_changed(last_state, current_state):
                        self.broadcast({
                            "type": "state_update",
                            "game_state": current_state
                        })
                        last_state = current_state
            except Exception as e:
                print(f"Error in state broadcaster: {e}")
                
            time.sleep(1)
            
    def _state_changed(self, old_state, new_state):
        """Check if game state has changed in a meaningful way"""
        # Check grid changes
        if old_state["grid"] != new_state["grid"]:
            return True
            
        # Check turn changes
        if old_state["current_turn"] != new_state["current_turn"]:
            return True
            
        # Check game over state
        if old_state["game_over"] != new_state["game_over"]:
            return True
            
        # Check player list changes
        if old_state["players"] != new_state["players"]:
            return True
            
        return False
                
    def handle_game_end(self, game):
        """Handle the end of a game"""
        state = game.get_state()
        if state["winner"]:
            message = f"{state['winner']} wins!"
        else:
            message = "Game ended in a tie!"
            
        self.broadcast({
            "type": "game_end",
            "message": message,
            "game_state": state
        })
        
        # Reset game after delay
        time.sleep(3)
        self.game_manager.end_game()
            
        # Notify clients of reset
        self.broadcast({
            "type": "game_reset",
            "message": "New game will start when players join"
        })
        
        print("Game reset, waiting for new players...")
        
    def handle_client(self, client_socket, client_addr, barrier):
        """Handle client connection"""
        socket_state = SocketState(client_socket, client_addr)
        
        try:
            # Get player name
            self.send_message(client_socket, {
                "type": "welcome",
                "message": "Welcome to TicTacToe! Enter your name:"
            })
            
            data = client_socket.recv(1024)
            if not data:
                return
                
            try:
                message = json.loads(data.decode())
                name = message.get("name", f"Player-{client_addr[1]}")
            except:
                name = data.decode().strip() or f"Player-{client_addr[1]}"
                
            socket_state.setPlayerName(name)
            print(f"{name} connected from {client_addr}")
            
            barrier.wait()  # Wait for all players to connect
            # Add player to game
            game = self.game_manager.add_player(socket_state)
            if not game:
                self.send_message(client_socket, {
                    "type": "error",
                    "message": "Game is full"
                })
                return
                
            # Send game start message
            state = game.get_state()
            self.send_message(client_socket, {
                "type": "game_start",
                "message": f"You joined as {name}",
                "game_state": state
            })
            
            # Notify other players
            self.broadcast({
                "type": "player_joined",
                "player": name,
                "game_state": state
            }, exclude=client_socket)
            
            # Main client loop
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                try:
                    request = json.loads(data.decode())
                    if "move" in request:
                        row = request["move"]["row"]
                        col = request["move"]["col"]
                        
                        game = self.game_manager.active_game
                        if not game:
                            self.send_message(client_socket, {
                                "type": "error",
                                "message": "No active game"
                            })
                            continue
                            
                        success, result = game.make_move(socket_state, row, col)
                        if not success:
                            self.send_message(client_socket, {
                                "type": "error",
                                "message": result
                            })
                            continue
                            
                        state = game.get_state()
                        self.broadcast({
                            "type": "move",
                            "player": name,
                            "symbol": "X",
                            "row": row,
                            "col": col,
                            "game_state": state
                        })
                        
                        if result in ["win", "tie"]:
                            self.handle_game_end(game)
                            
                except Exception as e:
                    print(f"Error handling client request: {e}")
                    traceback.print_exc()
                    break
                    
        except Exception as e:
            print(f"Connection error with {client_addr}: {e}")
            traceback.print_exc()
        finally:
            print(f"{socket_state.getPlayerName()} disconnected")
            self.game_manager.remove_player(socket_state)
            with self.connections_lock:
                if client_socket in self.connections:
                    self.connections.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass
                
            # Notify other players
            self.broadcast({
                "type": "player_left",
                "player": socket_state.getPlayerName(),
                "game_state": self.game_manager.get_game_state() or {"players": []}
            })

def main():
    """Main server function"""
    parser = argparse.ArgumentParser(description='TicTacToe Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=65432, help='Server port')
    parser.add_argument('--size', type=int, choices=[3,4,5], default=3, help='Grid size')
    parser.add_argument('--players', type=int, default=2, help='Max players per game')
    parser.add_argument('--difficulty', type=int, choices=[1,2,3], default=1, 
                        help='Server difficulty (1=easy, 2=medium, 3=hard)')
    args = parser.parse_args()
    
    server = TicTacToeServer(
        args.host, 
        args.port, 
        args.size, 
        args.players,
        args.difficulty
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    main()