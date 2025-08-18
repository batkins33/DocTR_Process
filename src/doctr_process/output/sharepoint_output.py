"""SharePoint upload handler."""

import logging
import os
from typing import List, Dict, Any

try:
    from office365.runtime.auth.user_credential import UserCredential
    from office365.sharepoint.client_context import ClientContext
    HAS_SHAREPOINT = True
except ImportError:
    HAS_SHAREPOINT = False
    UserCredential = None
    ClientContext = None

from .base import OutputHandler


class SharePointOutput(OutputHandler):
    """Upload images to SharePoint and record URLs."""

    def __init__(self, site_url: str, library: str, folder: str, credentials: Dict[str, str] | None = None):
        if not HAS_SHAREPOINT:
            raise ImportError("SharePoint functionality requires the 'office365' package. Install it with: pip install office365")
        
        if credentials:
            creds = UserCredential(credentials.get("username"), credentials.get("password"))
            self.ctx = ClientContext(site_url).with_credentials(creds)
        else:
            self.ctx = ClientContext(site_url)
        self.library = library
        self.folder = folder

    def write(self, rows: List[Dict[str, Any]], cfg: dict) -> None:
        target_folder = self.ctx.web.get_folder_by_server_relative_url(f"{self.library}/{self.folder}")
        for row in rows:
            img_path = row.get("image_path")
            if not img_path or not os.path.isfile(img_path):
                continue
            with open(img_path, "rb") as f:
                name = os.path.basename(img_path)
                uploaded = target_folder.upload_file(name, f.read()).execute_query()
                row["image_url"] = uploaded.serverRelativeUrl
                logging.info("Uploaded %s to SharePoint", name)
        self.ctx.execute_query()
