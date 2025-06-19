import libtorrent as lt
import requests
import os
import time
import logging
import argparse
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class P2PClient:
    def __init__(self, server_url, download_dir, client_id):
        self.server_url = server_url
        self.download_dir = download_dir
        self.client_id = client_id
        self.torrent_path = "/tmp/distribute.torrent"
        self.start_time = None

    def _fetch_torrent(self):
        """Download torrent file from HTTP server with retries"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.get(self.server_url, timeout=10)
                response.raise_for_status()
                with open(self.torrent_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"[{self.client_id}] Torrent file downloaded from {self.server_url}")
                return True
            except Exception as e:
                logger.warning(f"[{self.client_id}] Attempt {attempt + 1}/{max_retries}: {e}")
                time.sleep(5)
        raise RuntimeError(f"Failed to download torrent after {max_retries} attempts")

    def download(self):
        """Download with auto-seeding and timing"""
        self.start_time = datetime.now()
        
        self._fetch_torrent()
        
        ses = lt.session()
        settings = ses.get_settings()
        settings["enable_upnp"] = True
        settings["enable_natpmp"] = True
        ses.apply_settings(settings)
        
        params = {
            "save_path": self.download_dir,
            "ti": lt.torrent_info(self.torrent_path),
            "storage_mode": lt.storage_mode_t.storage_mode_sparse
        }
        handle = ses.add_torrent(params)
        
        logger.info(f"[{self.client_id}] Starting download...")
        while not handle.is_seed():
            status = handle.status()
            elapsed = (datetime.now() - self.start_time).total_seconds()
            logger.info(
                f"[{self.client_id}] [{elapsed:.1f}s] Progress: {status.progress * 100:.1f}% | "
                f"DL: {status.download_rate / 1024:.1f} KB/s | "
                f"Peers: {status.num_peers}"
            )
            time.sleep(0.5)
        
        total_time = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"[{self.client_id}] Download completed in {total_time:.1f} seconds")
        
        logger.info(f"[{self.client_id}] Now seeding... Press Ctrl+C to stop")
        while True:
            time.sleep(10)

def main():
    parser = argparse.ArgumentParser(description='P2P Client for downloading files')
    parser.add_argument('--server-url', '-u',
                       required=True,
                       help='URL to download the torrent file from (e.g., http://192.168.0.0:8000/distribute.torrent)')
    parser.add_argument('--download-dir', '-d',
                       default='./downloads',
                       help='Directory to save downloaded files (default: ./downloads)')
    parser.add_argument('--client-id', '-i',
                       default='client-1',
                       help='Client identifier for logging (default: client-1)')
    
    args = parser.parse_args()
    
    os.makedirs(args.download_dir, exist_ok=True)
    
    client = P2PClient(
        server_url=args.server_url,
        download_dir=args.download_dir,
        client_id=args.client_id
    )
    
    try:
        client.download()
    except KeyboardInterrupt:
        logger.info(f"[{args.client_id}] Download interrupted by user")
    except Exception as e:
        logger.error(f"[{args.client_id}] Download failed: {e}")

if __name__ == "__main__":
    main()