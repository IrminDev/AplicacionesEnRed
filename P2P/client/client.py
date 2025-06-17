import libtorrent as lt
import requests
import os
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class P2PClient:
    def __init__(self):
        self.server_url = os.getenv("SERVER_URL", "http://server:8000/distribute.torrent")
        self.download_dir = os.getenv("DOWNLOAD_DIR", "./downloads")
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
                logger.info(f"Torrent file downloaded from {self.server_url}")
                return True
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries}: {e}")
                time.sleep(5)
        raise RuntimeError(f"Failed to download torrent after {max_retries} attempts")

    def download(self):
        """Download with auto-seeding and timing"""
        self.start_time = datetime.now()
        
        # 1. Fetch torrent file
        self._fetch_torrent()
        
        # 2. Configure session
        ses = lt.session()
        settings = ses.get_settings()
        settings["enable_upnp"] = True
        settings["enable_natpmp"] = True
        ses.apply_settings(settings)  # Fixed: Changed from set_settings to apply_settings
        
        # 3. Start download
        params = {
            "save_path": self.download_dir,
            "ti": lt.torrent_info(self.torrent_path),
            "storage_mode": lt.storage_mode_t.storage_mode_sparse
        }
        handle = ses.add_torrent(params)
        
        logger.info("Starting download...")
        while not handle.is_seed():
            status = handle.status()
            elapsed = (datetime.now() - self.start_time).total_seconds()
            logger.info(
                f"[{elapsed:.1f}s] Progress: {status.progress * 100:.1f}% | "
                f"DL: {status.download_rate / 1024:.1f} KB/s | "
                f"Peers: {status.num_peers}"
            )
            time.sleep(0.5)
        
        total_time = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"Download completed in {total_time:.1f} seconds")
        
        # Continue seeding indefinitely
        logger.info("Now seeding... Press Ctrl+C to stop")
        while True:
            time.sleep(10)

if __name__ == "__main__":
    client = P2PClient()
    client.download()