import libtorrent as lt
import os
import time
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class P2PServer:
    def __init__(self, file_path, torrent_name, http_port):
        self.file_path = file_path
        self.torrent_name = torrent_name
        self.http_port = http_port
        self.http_server = None

    def _generate_torrent(self):
        fs = lt.file_storage()
        lt.add_files(fs, self.file_path)
        torrent = lt.create_torrent(fs)
        torrent.set_creator("P2P Server")
        if not os.path.exists(self.file_path):
            logger.error(f"File {self.file_path} does not exist.")
            raise FileNotFoundError(f"File {self.file_path} does not exist.")
        lt.set_piece_hashes(torrent, os.path.dirname(self.file_path))
        with open(self.torrent_name, "wb") as f:
            f.write(lt.bencode(torrent.generate()))
        logger.info(f"Torrent file generated: {self.torrent_name}")

    def _start_http_server(self):
        logger.info(f"Starting HTTP server on port {self.http_port} to serve {self.torrent_name}")
        
        torrent_dir = os.path.dirname(self.torrent_name)
        if torrent_dir:
            os.makedirs(torrent_dir, exist_ok=True)
        
        # TODO
        # Change the server address to their IP address or domain name
        self.http_server = HTTPServer(('0.0.0.0', self.http_port), SimpleHTTPRequestHandler)
        threading.Thread(target=self.http_server.serve_forever, daemon=True).start()
        logger.info(f"HTTP server started on port {self.http_port}")

    def _start_seeding(self):
        ses = lt.session()
        params = {
            "save_path": os.path.dirname(self.file_path),
            "ti": lt.torrent_info(self.torrent_name),
        }
        handle = ses.add_torrent(params)
        logger.info(f"Seeding started. Torrent: {self.torrent_name}")
        while True:
            time.sleep(10)

    def run(self):
        self._generate_torrent()
        self._start_http_server()
        self._start_seeding()

if __name__ == "__main__":
    server = P2PServer(
        file_path=os.getenv("FILE_PATH", "file.mp4"),
        torrent_name=os.getenv("TORRENT_NAME", "distribute.torrent"),
        http_port=int(os.getenv("HTTP_PORT", 8000))
    )
    server.run()