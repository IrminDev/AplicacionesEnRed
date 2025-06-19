import libtorrent as lt
import os
import time
import logging
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class P2PServer:
    def __init__(self, file_path, torrent_name, chunk_size_kb, http_port, server_ip):
        self.file_path = file_path
        self.torrent_name = torrent_name
        self.chunk_size_kb = chunk_size_kb
        self.http_port = http_port
        self.server_ip = server_ip
        self.start_time = None

    def _generate_torrent(self):
        """Create torrent with custom chunk size"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File {self.file_path} not found")

        fs = lt.file_storage()
        lt.add_files(fs, self.file_path)
        torrent = lt.create_torrent(fs, piece_size=self.chunk_size_kb * 1024)
        torrent.set_creator("P2P Server")
        lt.set_piece_hashes(torrent, ".")
        with open(self.torrent_name, "wb") as f:
            f.write(lt.bencode(torrent.generate()))
        logger.info(f"Created torrent {self.torrent_name} with {self.chunk_size_kb}KB chunks")

    def _start_http_server(self):
        """Serve torrent file via HTTP on custom port"""
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=os.getcwd(), **kwargs)

        self.http_server = HTTPServer((self.server_ip, self.http_port), Handler)
        threading.Thread(target=self.http_server.serve_forever, daemon=True).start()
        logger.info(f"Serving torrent on http://{self.server_ip}:{self.http_port}/{self.torrent_name}")

    def _start_seeding(self):
        """Start BitTorrent seeding with performance tracking"""
        self.start_time = datetime.now()
        ses = lt.session()
        params = {
            "save_path": ".",
            "ti": lt.torrent_info(self.torrent_name),
        }
        handle = ses.add_torrent(params)
        
        handle.set_upload_mode(True)

        while True:
            status = handle.status()
            elapsed = (datetime.now() - self.start_time).total_seconds()
            logger.info(
                f"[{elapsed:.1f}s] Seeding to {status.num_peers} peers | "
                f"UL: {status.upload_rate / 1024:.1f} KB/s"
            )
            time.sleep(5)

    def run(self):
        self._generate_torrent()
        self._start_http_server()
        self._start_seeding()

def main():
    parser = argparse.ArgumentParser(description='P2P Server for file sharing')
    parser.add_argument('--file-path', '-f', 
                       required=True,
                       help='Path to the file to share')
    parser.add_argument('--torrent-name', '-t',
                       default='distribute.torrent',
                       help='Name of the torrent file to create (default: distribute.torrent)')
    parser.add_argument('--chunk-size-kb', '-c',
                       type=int,
                       default=2048,
                       help='Chunk size in KB (default: 2048)')
    parser.add_argument('--http-port', '-p',
                       type=int,
                       default=8000,
                       help='HTTP server port (default: 8000)')
    parser.add_argument('--server-ip', '-s',
                       default='0.0.0.0',
                       help='Server IP address (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    server = P2PServer(
        file_path=args.file_path,
        torrent_name=args.torrent_name,
        chunk_size_kb=args.chunk_size_kb,
        http_port=args.http_port,
        server_ip=args.server_ip
    )
    
    server.run()

if __name__ == "__main__":
    main()