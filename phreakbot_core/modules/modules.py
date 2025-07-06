def config(bot):
    return {
        "events": [],
        "commands": ["load", "reload", "unload", "avail"],
        "permissions": ["user", "modules"],
        "help": "Provides load, reload, unload functionality for modules",
    }


def run(bot, event):
    if event["command"] == "avail":
        mlist = ", ".join(sorted(bot.modules.keys()))
        bot.add_response(f"Modules loaded: {mlist}")
        return

    # Commands below require owner / modules permissions.
    if not bot._check_permissions(event, ["modules"]):
        bot.add_response("I can't let you do that, Dave.")
        return

    # Commands below require param to be set.
    if event["command_args"] == "":
        bot.reply("this command requires at least one argument (module name)")
        return

    if event["command"] == "load" or event["command"] == "reload":
        result = bot.load_module(event["command_args"])
        bot.add_response(result)
        return

    if event["command"] == "unload":
        bot.unload_module(event["command_args"])
        bot.add_response(f"Unloaded module '{event['command_args']}'")
        return
