import time
import os
import requests
from typing import Dict, Any, List

APPEEARS_BASE = "https://appeears.earthdatacloud.nasa.gov/api"

class AppEEARSClient:
    """Minimal AppEEARS area request client.
    Requires Earthdata credentials (basic auth) set as env vars.
    """
    def __init__(self, username: str | None = None, password: str | None = None):
        self.username = username or os.getenv("NASA_EARTHDATA_USERNAME")
        self.password = password or os.getenv("NASA_EARTHDATA_PASSWORD")
        if not (self.username and self.password):
            raise ValueError("Earthdata credentials missing. Set NASA_EARTHDATA_USERNAME and NASA_EARTHDATA_PASSWORD")
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

    def create_task(self, task_def: Dict[str, Any]) -> str:
        r = self.session.post(f"{APPEEARS_BASE}/task", json=task_def, timeout=40)
        r.raise_for_status()
        return r.json()["task_id"]

    def wait_task(self, task_id: str, poll: int = 30, timeout: int = 1800) -> Dict[str, Any]:
        start = time.time()
        while True:
            r = self.session.get(f"{APPEEARS_BASE}/status/{task_id}", timeout=30)
            r.raise_for_status()
            status = r.json()
            if status.get("status") in ("done", "error"):
                return status
            if time.time() - start > timeout:
                raise TimeoutError("AppEEARS task timeout")
            time.sleep(poll)

    def list_bundle(self, task_id: str) -> Dict[str, Any]:
        r = self.session.get(f"{APPEEARS_BASE}/bundle/{task_id}", timeout=40)
        r.raise_for_status()
        return r.json()

    def download_csv_files(self, task_id: str, out_dir: str) -> List[str]:
        os.makedirs(out_dir, exist_ok=True)
        bundle = self.list_bundle(task_id)
        saved = []
        for f in bundle.get("files", []):
            if f.get("file_type") == "csv":
                url = f"{APPEEARS_BASE}/bundle/{task_id}/{f['file_id']}"
                resp = self.session.get(url, timeout=60)
                resp.raise_for_status()
                path = os.path.join(out_dir, f["file_name"])  # use original name
                with open(path, "wb") as fh:
                    fh.write(resp.content)
                saved.append(path)
        return saved
