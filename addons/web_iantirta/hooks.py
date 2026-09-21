from pathlib import Path
from sigil.tools import file_path


def apply_hook(env):
    """ Update Menu Icons """
    icon_dir = file_path("web_iantirta/static/description/icons")
    available_icons = {
        d.stem: d.name
        for d in Path(icon_dir).iterdir()
        if d.is_dir()
    }
    for icon in available_icons:
        print("Available", icon)
    all_apps = env["ir.ui.menu"].search([
        ("parent_id", "=", False),
    ])
    for app in all_apps:
        print("Searching for: ", app.name.lower())
        if app.name.lower() in available_icons:
            icon_file = f"web_iantirta,static/description/icons/{app.name.lower()}/icon.png"
            app.write({
                "web_icon": icon_file
            })
    all_mods = env["ir.module.module"].search([
        ("icon", "!=", False)
    ])
    for mod in all_mods:
        if mod.name.startswith("test"): continue
        print("Mod Searching for: ", mod.name.lower(), "==", mod.display_name.lower())
        if mod.name.lower() in available_icons:
            icon_file = f"/web_iantirta/static/description/icons/{mod.name.lower()}/icon.png"
            mod.write({
                "icon": icon_file
            })
        elif mod.display_name.lower() in available_icons:
            icon_file = f"/web_iantirta/static/description/icons/{mod.display_name.lower()}/icon.png"
            mod.write({
                "icon": icon_file
            })
