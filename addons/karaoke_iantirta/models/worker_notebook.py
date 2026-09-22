import logging
import json
import tempfile
import shutil

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

    