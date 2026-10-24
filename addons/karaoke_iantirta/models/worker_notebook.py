import json
import logging
import shutil
import tempfile
import uuid
from pathlib import Path

from sigil.addons.karaoke_iantirta import utils as karaoke_utils

from sigil import _, api, fields, models
from sigil.exceptions import UserError

_logger = logging.getLogger(__name__)


class WorkerNotebook(models.Model):
    _name = 'worker.notebook'
    _description = 'Jupyter Notebook'

    name = fields.Char("Notebook Name")

    code = fields.Text(string="Notebook Code")

    language = fields.Selection([("python", "Python")], default="python")

    def to_source_code(self) -> list[str]:
        return [f"{line}\n" for line in (self.code or "").splitlines()]

    def to_metadata_dict(self) -> dict:
        self.ensure_one()
        return {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "id": str(uuid.uuid4())[:8],
                    "metadata": {},
                    "outputs": [],
                    "source": self.to_source_code(),
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {
                    "name": self.language or "python",
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
