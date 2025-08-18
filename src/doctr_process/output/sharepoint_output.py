"""SharePoint upload handler."""

import logging
import os
import time
from typing import List, Dict, Any

try:
    from office365.runtime.auth.user_credential import UserCredential
    from office365.sharepoint.client_context import ClientContext
    SHAREPOINT_AVAILABLE = True
except ImportError:
    SHAREPOINT_AVAILABLE = False
    UserCredential = None
    ClientContext = None

from .base import OutputHandler


class SharePointOutput(OutputHandler):
    """Upload images to SharePoint and record URLs with retry logic."""

    def __init__(self, site_url: str, library: str, folder: str, credentials: Dict[str, str] | None = None):
        if not SHAREPOINT_AVAILABLE:
            raise ImportError("SharePoint support requires office365 package")
        
        self.site_url = site_url
        self.library = library
        self.folder = folder
        self.max_retries = 3
        self.retry_delay = 1.0
        
        if credentials:
            creds = UserCredential(credentials.get("username"), credentials.get("password"))
            self.ctx = ClientContext(site_url).with_credentials(creds)
        else:
            self.ctx = ClientContext(site_url)

    def _upload_with_retry(self, file_path: str, target_folder) -> str | None:
        """Upload a file with retry logic."""
        filename = os.path.basename(file_path)
        
        for attempt in range(self.max_retries):
            try:
                with open(file_path, "rb") as f:
                    uploaded = target_folder.upload_file(filename, f.read()).execute_query()
                    logging.info("Uploaded %s to SharePoint (attempt %d)", filename, attempt + 1)
                    return uploaded.serverRelativeUrl
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error("Failed to upload %s to SharePoint after %d attempts: %s", 
                                filename, self.max_retries, str(e))
                    return None
                else:
                    logging.warning("Upload attempt %d failed for %s: %s. Retrying...", 
                                  attempt + 1, filename, str(e))
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        return None

    def write(self, rows: List[Dict[str, Any]], cfg: dict) -> None:
        try:
            target_folder = self.ctx.web.get_folder_by_server_relative_url(f"{self.library}/{self.folder}")
            
            uploaded_count = 0
            failed_count = 0
            
            for row in rows:
                img_path = row.get("image_path")
                if not img_path or not os.path.isfile(img_path):
                    continue
                
                url = self._upload_with_retry(img_path, target_folder)
                if url:
                    row["image_url"] = url
                    uploaded_count += 1
                else:
                    failed_count += 1
            
            self.ctx.execute_query()
            logging.info("SharePoint upload complete: %d uploaded, %d failed", uploaded_count, failed_count)
            
        except Exception as e:
            logging.error("SharePoint upload failed: %s", str(e))
            raise
