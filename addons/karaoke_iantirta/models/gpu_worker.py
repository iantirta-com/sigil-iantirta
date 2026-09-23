import logging
import json
import tempfile
import shutil
import base64
import uuid

from pathlib import Path

from sigil.http import request
from sigil import _, api, fields, models
from sigil.exceptions import UserError
from sigil.addons.karaoke_iantirta import utils as karaoke_utils

_logger = logging.getLogger(__name__)


class GpuWorker(models.Model):
    _name = 'gpu.worker'
    _description = 'GPU Worker'

    name = fields.Char(required=True)

    provider = fields.Selection([
        ("kaggle", "Kaggle")
    ], required=True)

    access_token = fields.Char(
        string="API Token", required=True,
    )

    notebook_id = fields.Many2one(comodel_name="worker.notebook", string="Notebook", required=True)
    notebook_code = fields.Text(
        related="notebook_id.code",
        string="Notebook Code",
        readonly=False,
    )

    quota_json = fields.Json(compute="_compute_quotas", store=True)
    gpu_time_used = fields.Datetime()
    gpu_time_allowed = fields.Datetime()
    tpu_time_used = fields.Datetime()
    tpu_time_allowed = fields.Datetime()
    refresh_time = fields.Datetime()

    # Drive Config
    gdrive_credentials = fields.Binary(
        string="Google Drive Credentials as .json", store=False,
    )
    gdrive_client_config = fields.Char(
        string="Google Drive Client Config",
        compute="_compute_gdrive_client_config",
        readonly=False,
        store=True,
    )
    gdrive_access_token_json = fields.Char()
    gdrive_root_folder_id = fields.Char(required=True)

    # Helper
    _worker = None

    def _get_worker_class(self):
        from .kplus_tools import KaggleWorker
        provider_map = {
            "kaggle": KaggleWorker
        }
        return provider_map.get(self.provider, None)

    def _get_worker_instance(self):
        self.ensure_one()
        if instance := self._get_worker_class():
            return instance(self.access_token)
        raise UserError(_("Unsupported provider configuration."))

    # Drive
    @api.onchange('gdrive_credentials')
    def _compute_gdrive_client_config(self):
        for worker in self:
            creds = worker.with_context(bin_size=False).gdrive_credentials
            worker.gdrive_client_config = base64.b64decode(creds) if creds else False
        
    def setup_user_token(self):
        self.ensure_one()
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError:
            raise ImportError("Cannot Continue as google-auth is not installed")

        SCOPES = ['https://www.googleapis.com/auth/drive']

        creds = None
        if self.gdrive_access_token_json:
            user_info = json.loads(self.gdrive_access_token_json)
            creds = Credentials.from_authorized_user_info(user_info)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                client_config = json.loads(self.gdrive_client_config)
                flow = InstalledAppFlow.from_client_config(
                    client_config,
                    SCOPES,
                    redirect_uri=f"{self.get_base_url().rstrip('/')}/google_drive/callback"
                    #redirect_uri="urn:ietf:wg:oauth:2.0:oob",
                )
                from kplus.tools import rich
                # creds = flow.run_local_server()
                auth_url, _ = flow.authorization_url(
                    access_type="offline",
                    include_granted_scopes='true',
                    login_hint='tirtamoto@gmail.com',
                    state=str(self.id)
                )
                print(">> Request redirecting")
                request.redirect(auth_url)
                rich.inspect(self.env)
                rich.inspect(request)
                print(">> After Redieect")
                return {
                    'type': 'ir.actions.act_url',
                    'url': auth_url,
                    'target': 'new',
                }
                # creds = flow.fetch_token()
                # self.gdrive_access_token_json = creds.to_json()

        return creds

    def action_setup_user_token(self):
        self.ensure_one()
        try:
            from . import drive_tools
        except ImportError:
            raise ImportError("Cannot Continue as google-auth is not installed")
        if creds := drive_tools.get_creds(
            self.gdrive_access_token_json
        ):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Google Drive token refreshed successfully.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            auth_uri = drive_tools.setup_create_creds(
                self.gdrive_client_config,
                redirect_uri=f"{self.get_base_url().rstrip('/')}/google_drive/callback",
                state=str(self.id)
            )
            return {
                'type': 'ir.actions.act_url',
                'url': auth_uri,
                'target': 'self',
            }
    
    # Quotas
    def get_quotas(self) -> dict:
        quotas = self._get_worker_instance().get_quota()
        self.quota_json = quotas
        return quotas

    @api.depends("access_token", 'name', "provider")
    def _compute_quotas(self):
        for record in self:
            if record.access_token:
                try:
                    quotas = record.get_quotas()
                    # record.gpu_time_used = quotas["types"][0]
                    # record.gpu_time_allowed = 
                    # record.tpu_time_used = 
                    # record.tpu_time_allowed = 
                    # record.refresh_time = 
                except Exception as e:
                    _logger.error("Failed to fetch quotas for %s: %s", record.name, e)
                    record.quota_json = {
                        "error": "Failed to fetch quotas",
                        "error_str": str(e),
                    }
            else:
                record.quota_json = {}

    def action_get_quotas(self):
        return self.get_quotas()

    # Running
    def action_run(self):
        try:
            from . import drive_tools
        except ImportError:
            raise ImportError("Cannot Continue as google-auth is not installed")

        self.ensure_one()

        worker = self._get_worker_instance()

        new_access_token = karaoke_utils.generate_access_token(
            self.name, self.provider
        )

        if not (drive_creds := drive_tools.get_creds(
            self.gdrive_access_token_json
        )):
            raise UserError(_("Cannot continue as this notebook worker require drive token"))
        notebook: dict = self.notebook_id.to_metadata_dict()
        notebook_param: dict = {
            "cell_type": "code",
            "execution_count": None,
            "id": str(uuid.uuid4())[:8],
            "metadata": {},
            "outputs": [],
            "source": [
                "# Do Not Modified. Generated by iantirta.com\n",
                "import os\n",
                f"os.environ['IANTIRTA_API_KEY'] = '{new_access_token}'\n",
                "\n",
                f'IANTIRTA_URL = "{self.get_base_url()}"\n',
                f'WORKER_NAME = "{self.name}"\n',
                f'WORKER_PROVIDER = "{self.provider}"\n',
                "\n",
                '!pip install -q --upgrade --force-reinstall --no-cache-dir "git+https://github.com/yancovenant/karaokeplus.git"\n',
                '\n',
                'os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"\n',
                'os.environ["HF_XET_HIGH_PERFORMANCE"] = "1"\n',
                '\n',
                f'DRIVE_USER_TOKEN: dict = {drive_creds.to_json()}\n',
                f'SHARED_ROOT_FOLDER_ID = "{self.gdrive_root_folder_id}"\n',
            ],
        }
        notebook["cells"].insert(0, notebook_param)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_script_path = Path(tmpdir) / "worker.ipynb"

            with open(str(tmp_script_path), "w", encoding="utf-8") as f:
                json.dump(notebook, f, indent=1)

            if self.provider == "kaggle":
                kernel_metadata: dict = {
                    "id": "burninfist/kplus-gpu-worker", # Todo Change it to name?
                    "title": "KPlus GPU Worker",
                    "code_file": "worker.ipynb",
                    "language": "python",
                    "kernel_type": "notebook",
                    "is_private": True,
                    "enable_gpu": True,
                    "enable_tpu": False,
                    "enable_internet": True,
                    "machine_shape": "NvidiaTeslaT4",
                    "dataset_sources": [],
                    "competition_sources": [],
                    "kernel_sources": [],
                    "model_sources": []
                }
                tmp_metadata_path = Path(tmpdir) / "kernel-metadata.json"
                with open(str(tmp_metadata_path), "w", encoding="utf-8") as f:
                    json.dump(kernel_metadata, f, indent=1)

            # if kaggle it is a folder
            # if colab it is a file
            folder = tmpdir
            if self.provider == "colab":
                folder = tmp_script_path

            response = worker.run(str(folder))
