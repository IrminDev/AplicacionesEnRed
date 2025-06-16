import libtorrent as lt
import requests
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BitTorrentClient:
    def __init__(self, server_url, download_dir):
        self.server_url = server_url
        self.download_dir = download_dir
        self.torrent_path = "/tmp/distribute.torrent"

    def _fetch_torrent(self):
        response = requests.get(self.server_url)
        with open(self.torrent_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Torrent file downloaded from {self.server_url}")

    def _verify_download(self, handle):
        os.makedirs(self.download_dir, exist_ok=True)
        torrent_info = handle.torrent_file()
        
        for i in range(torrent_info.num_files()):
            file_info = torrent_info.file_at(i)
            file_path = os.path.join(self.download_dir, file_info.path)
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                expected_size = file_info.size
                logger.info(f"File: {file_path}")
                logger.info(f"Size: {file_size} bytes (expected: {expected_size} bytes)")
                
                if file_size == expected_size:
                    logger.info("✓ File size matches!")
                    return True
                else:
                    logger.error("✗ File size mismatch!")
                    return False
            else:
                logger.error(f"✗ File not found: {file_path}")
                return False
        
        return False

    def start_download(self):
        """Start P2P download."""
        self._fetch_torrent()
        ses = lt.session()
        params = {
            "save_path": self.download_dir,
            "ti": lt.torrent_info(self.torrent_path),
        }
        handle = ses.add_torrent(params)
        
        torrent_info = handle.torrent_file()
        logger.info(f"Download started: {torrent_info.name()}")
        
        while not handle.status().is_seeding:
            s = handle.status()
            logger.info(
                f"Progress: {s.progress * 100:.2f}% | "
                f"Peers: {s.num_peers} | "
                f"DL: {s.download_rate / 1024:.2f} KB/s | "
                f"UL: {s.upload_rate / 1024:.2f} KB/s"
            )
            
            if s.progress >= 1.0:
                break
                
            time.sleep(5)
        
        logger.info("Download complete!")
        
        if self._verify_download(handle):
            logger.info("✓ Download verification successful!")
        else:
            logger.error("✗ Download verification failed!")

if __name__ == "__main__":
    client = BitTorrentClient(
        server_url=os.getenv("SERVER_URL"),
        download_dir=os.getenv("DOWNLOAD_DIR", "./downloads"))
    client.start_download()