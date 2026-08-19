import base64
from sigil.tools import misc
import logging
_logger = logging.getLogger(__name__)

def _update_menu_icons(cr, menu_icons):
    menu_item = cr['ir.ui.menu'].search([('parent_id', '=', False)])
    for menu in menu_item:
        icon_file = menu_icons.get(menu.name)
        if icon_file:
            img_path = misc.file_path(
                f'web_enterprise_iantirta/static/description/{icon_file}/icon.png')
            if img_path:
                try:
                    menu.write({
                        'web_icon_data': base64.b64encode(open(img_path, "rb").read())
                    })
                    _logger.info(f"Updated icon for menu: {menu.name}")
                except Exception as e:
                    _logger.warning(f"Failed to update icon for menu '{menu.name}': {e}")
            else:
                _logger.warning(f"Icon file not found for menu '{menu.name}': {icon_file}")
        if menu.name == "Discuss":
            menu.write({
                'name': "Chat"
            })
        if menu.name == "Apps":
            menu.write({
                'name': "Plugins"
            })

def update_menu_icons(cr):
    menu_icons = {
        "Discuss": "mail",
        "Chat" : "mail", # another name,
        "Website": "website",
        "Apps": "apps",
        "Plugins": "apps", # another name,
        "Link Tracker": "utm",
        "Settings": "settings",
        "Attendances": "attendance",
        "Contacts": "contacts",
        "Employees": "employee",
        "Logistics": "logistics",
        "Email Marketing": "marketing",
    }
    _update_menu_icons(cr, menu_icons)

def pre_init_hook(cr):
    update_menu_icons(cr)
    _logger.error("Icons updated successfully in pre_init_hook")

def post_init_hook(cr):
    update_menu_icons(cr)
    _logger.error("Icons updated successfully in post_init_hook")
