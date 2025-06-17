import libtorrent as lt
import os
import time
import logging
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class P2PServer:
    def __init__(self):
        self.file_path = os.getenv("FILE_PATH", "large_file.bin")
        self.torrent_name = os.getenv("TORRENT_NAME", "distribute.torrent")
        self.chunk_size_kb = int(os.getenv("CHUNK_SIZE_KB", "2048"))  # Default: 2MB
        self.http_port = int(os.getenv("HTTP_PORT", "8000"))
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

        self.http_server = HTTPServer(('0.0.0.0', self.http_port), Handler)
        threading.Thread(target=self.http_server.serve_forever, daemon=True).start()
        logger.info(f"Serving torrent on http://0.0.0.0:{self.http_port}/{self.torrent_name}")

    def _start_seeding(self):
        """Start BitTorrent seeding with performance tracking"""
        self.start_time = datetime.now()
        ses = lt.session()
        params = {
            "save_path": ".",
            "ti": lt.torrent_info(self.torrent_name),
            # Removed invalid 'upload_mode' parameter
        }
        handle = ses.add_torrent(params)
        
        # Enable upload mode AFTER adding torrent
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

if __name__ == "__main__":
    server = P2PServer()
    server.run()