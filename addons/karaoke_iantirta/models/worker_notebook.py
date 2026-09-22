import logging
import json
import tempfile
import shutil
import uuid

from pathlib import Path

from sigil import _, api, fields, models
from sigil.exceptions import UserError
from sigil.addons.karaoke_iantirta import utils as karaoke_utils

_logger = logging.getLogger(__name__)


class WorkerNotebook(models.Model):
    _name = 'worker.notebook'
    _description = 'Jupyter Notebook'

    name = fields.Char("Notebook Name")

    code = fields.Text(string="Notebook Code")

    language = fields.Selection([("python", "Python")], default="python")

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
                    "source": [f"{line}\n" for line in (self.code or "").splitlines()],
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
