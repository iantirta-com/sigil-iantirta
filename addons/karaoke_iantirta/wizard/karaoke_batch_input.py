import re

from sigil import _, api, models, fields, Command
from sigil.exceptions import ValidationError
from sigil.tools.float_utils import float_is_zero, float_round


class KaraokeBatchInputWizard(models.TransientModel):
    _name = 'karaoke.batch.input.wizard'
    _description = 'Karaoke Batch Input'

    youtube_urls = fields.Text("URL'S", required=True, help="split by `,`")
    karaoke_type = fields.Selection([
        ("basic", "Basic"),
        ("plus", "Plus (Lyrics Subtitle)"),
    ], required=True, string="Karaoke Generation Type")

    def action_on_click_create(self):
        self.ensure_one()
        
        to_create: list[dict] = [
            {"source_url": url.strip(), "karaoke_type": self.karaoke_type}
            for url in re.split(r'[,;]', self.youtube_urls)
            if url.strip()
        ]
        karaokes = self.env["karaoke.karaoke"].create(to_create)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _(f'Successfully created karaoke task total of {len(karaokes)}.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }