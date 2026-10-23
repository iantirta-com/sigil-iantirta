import json
from pathlib import Path

from sigil import fields, models


class GPUWorker(models.Model):
    _inherit = 'gpu.worker'

    code = fields.Selection(selection_add=[
        ('kaggle', 'Kaggle')
    ], ondelete={'kaggle': 'set default'})

    kaggle_access_token = fields.Char(
        copy=False,
        required_if_provider='kaggle',
    )

    def get_worker(self):
        if self.provider != 'kaggle':
            return super().get_worker()

        try:
            from iantirta.media import KaggleWorker
        except ModuleNotFoundError:
            raise ModuleNotFoundError("Cannot Continue as iantirta-media is not installed")

        return KaggleWorker(access_token=self.access_token)

    def _prepare_folder(self, tmpdir: str, tmp_script_path: Path) -> str:
        if self.provider != 'kaggle':
            return super()._prepare_folder(tmpdir, tmp_script_path)

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
        return tmpdir
