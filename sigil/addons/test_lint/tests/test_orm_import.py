
import logging
from pathlib import Path

from sigil.modules import Manifest
from . import lint_case
import re
_logger = logging.getLogger(__name__)

import_orm_re = re.compile(r'^(from|import)\s+sigil\.orm', flags=re.MULTILINE)


class TestDunderinit(lint_case.LintCase):

    def test_addons_orm_import(self):
        """ Test that sigil.orm is not imported in Sigil modules"""

        for manifest in Manifest.all_addon_manifests():
            module_path = Path(manifest.path)
            for path in module_path.rglob("**/*.py"):
                if import_orm_re.search(path.read_text()):
                    self.fail(f"Do not import directly from sigil.orm, use sigil.(api,fields,models): {path}")
