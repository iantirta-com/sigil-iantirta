# Part of Iantirta.com
# See LICENSE file for full copyright and licensing details.

import uuid
from typing import Any

from sigil import fields, models


class WorkerNotebook(models.Model):
    _name = 'worker.notebook'
    _description = 'Jupyter Notebook'

    name = fields.Char("Notebook Name")

    code = fields.Text(string="Notebook Code")

    language = fields.Selection([("python", "Python")], default="python")

    def to_source_code(self) -> list[str]:
        """
        Method to convert source code str into list[str] of source code.

        :return: list of string of source code
        :rtype: list[str]
        """
        self.ensure_one()
        return [f"{line}\n" for line in (self.code or "").splitlines()]

    def to_metadata_dict(self) -> dict[str, Any]:
        """
        Method to convert source code into a notebook .ipynb metadata.

        :return: dictonary metadata for notebook
        :rtype: dict[str, Any]
        """
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
