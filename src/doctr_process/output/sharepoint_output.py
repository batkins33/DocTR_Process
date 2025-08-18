"""SharePoint upload handler."""

import logging
import os
from typing import List, Dict, Any

try:
    from office365.runtime.auth.user_credential import UserCredential
    from office365.sharepoint.client_context import ClientContext
    SHAREPOINT_AVAILABLE = True
except ImportError:
    SHAREPOINT_AVAILABLE = False

from .base import OutputHandler


if SHAREPOINT_AVAILABLE:
    class SharePointOutput(OutputHandler):
        """Upload images to SharePoint and record URLs."""

        def __init__(self, site_url: str, library: str, folder: str, credentials: Dict[str, str] | None = None):
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

else:
    # Dummy SharePoint class when office365 is not available
    class SharePointOutput(OutputHandler):
        def __init__(self, *args, **kwargs):
            raise RuntimeError("SharePoint output requires office365 package, but it's not available")
        
        def write(self, rows: List[Dict[str, Any]], cfg: dict) -> None:
            raise RuntimeError("SharePoint output requires office365 package, but it's not available")
