# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from sigil import fields, models


class GPUWorker(models.Model):
    _inherit = 'gpu.worker'

    code = fields.Selection(selection_add=[
        ('kaggle', 'Kaggle')
    ], ondelete={'kaggle': 'cascade'})

    # Override

    # -----------------------
    # Abstraction method
    # -----------------------

    def get_worker(self):
        if self.code != 'kaggle':
            return super().get_worker()

        try:
            from iantirta.media import KaggleWorker

        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "Cannot Continue as iantirta-media is not installed"
            )

        return KaggleWorker(
            access_token=self.access_token
        )

    def _process_quota_json(self) -> None:
        """
        Process record quota json into
        ``quota_refresh_time``, ``quota_allowed``, and
        ``quota_used``.

        It could also be used for any necessary checker when
        ``quota_json`` is fetched.

        Since different provider api will give different response.

        Kaggle will actually return different types of
        accelerator quota, 1. GPU, 2. TPU, we're just going to
        be using the GPU quotas for this.
        """
        if self.code != 'kaggle':
            return super()._process_quota_json()

        self.ensure_one()

        if not self.quota_json:
            return

        quota = self.quota_json
        gpu_quota = quota.get('types')[0].get('gpu')

        # Convert str(timedelta) back to timedelta
        for field_name, name in [("quota_allowed", 'time_allowed'), ('quota_used', 'time_used')]:
            value = gpu_quota.get(name)
            if isinstance(value, str):
                terms = value.split(',')
                if len(terms) == 2:
                    days, ts = terms
                    day_num, _ = days.split()
                elif len(terms) == 1:
                    ts = terms[0]
                    day_num = 0
                ts = ts.strip()
                try:
                    dt = datetime.strptime(ts, "%H:%M:%S.%f")
                    usec = dt.microsecond
                except ValueError:
                    dt = datetime.strptime(ts, "%H:%M:%S")
                    usec = 0
                value = timedelta(
                    days=int(day_num),
                    hours=dt.hour,
                    minutes=dt.minute,
                    seconds=dt.second,
                    microseconds=usec
                )
            elif not isinstance(value, timedelta):
                raise TypeError(f"Value needed to be a timedelta or str but got {type(value)}")
            self[field_name] = value.total_seconds()

        self.quota_refresh_time = quota.get('refresh_time')

    # -----------------------
    # Worker run helper and abstraction method
    # -----------------------

    def _prepare_script(self, tmpdir: str, worker_instance) -> tuple[Path, dict]:
        """
        Prepare actual script path that would later be
        sent to the worker instance to run.

        Kaggle expect a notebook, thus we need to prepare
        necessary data for it.

        :param str tmpdir:
        :return: tuple of script path, and run parameters.
        :rtype: tuple[Path, dict]
        """
        if self.code != 'kaggle':
            return super()._prepare_script(tmpdir, worker_instance)

        tmp_script_path = Path(tmpdir) / "worker.ipynb"

        notebook: dict = self.notebook_id.to_metadata_dict()
        notebook_env_param: dict = {
            "cell_type": "code",
            "execution_count": None,
            "id": str(uuid.uuid4())[:8],
            "metadata": {},
            "outputs": [],
            "source": self._prepare_env_source_code(),
        }
        # Append the env param source on first index.
        notebook["cells"].insert(0, notebook_env_param)

        tmp_script_path.write_text(
            json.dumps(notebook, indent=1),
            encoding='utf-8'
        )

        kernel_metadata: dict = {
            "id": "burninfist/kplus-gpu-worker",  # Todo Change it to name?
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

        tmp_metadata_path.write_text(
            json.dumps(kernel_metadata, indent=1),
            encoding='utf-8'
        )

        # kaggle expected a folder to be pushed
        return Path(tmpdir), {}
