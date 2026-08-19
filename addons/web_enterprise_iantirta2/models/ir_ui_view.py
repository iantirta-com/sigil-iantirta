
from sigil import models
from markupsafe import Markup

CUSTOM_VIEW_ICONS = {
    "list": '<svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>',
    "kanban": '<svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="5" height="18" rx="1"></rect><rect x="10" y="3" width="5" height="12" rx="1"></rect><rect x="17" y="3" width="5" height="8" rx="1"></rect></svg>'
}

class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    def get_view_info(self):
        _view_info = self._get_view_info()
        return {
            type_: {
                'display_name': display_name,
                'icon': _view_info[type_]['icon'],
                'multi_record': _view_info[type_].get('multi_record', True),
            }
            for (type_, display_name)
            in self.fields_get(['type'], ['selection'])['type']['selection']
            if type_ != 'qweb' and type_ in _view_info
        }

    def _get_view_info(self):
        view_info = super()._get_view_info()
        views_to_update = view_info.keys() & CUSTOM_VIEW_ICONS.keys()
        for view_name in views_to_update:
            view_info[view_name]['icon'] = CUSTOM_VIEW_ICONS[Markup(view_name)]
        return view_info
    
    