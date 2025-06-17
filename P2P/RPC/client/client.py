import requests
import os
import time
from tqdm import tqdm

def download_file(url, filename):
    start_time = time.time()
    
    # Stream download with progress
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))
    
    return time.time() - start_time

if __name__ == '__main__':
    server_url = os.getenv("SERVER_URL", "http://server:8000/download")
    dl_time = download_file(server_url, "archlinux.iso")
    print(f"Download completed in {dl_time:.2f} seconds")