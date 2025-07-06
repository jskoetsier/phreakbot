def config(bot):
    return {
        "events": [],
        "commands": ["help"],
        "permissions": ["user"],
        "help": "Shows this help text for modules.",
    }


def run(bot, event):
    module = event["command_args"]
    if not module in bot.modules:
        bot.add_response(
            "A module named '%s' was not found loaded! Try the 'avail' command!"
            % module
        )
        return
    helptxt = bot.modules[module]["help"]
    helpcmds = ", ".join(bot.modules[module]["commands"])
    helpperm = ", ".join(bot.modules[module]["permissions"])

    bot.add_response("%s" % (helptxt))
    bot.add_response("Provides commands: %s" % (helpcmds))
    bot.add_response("Needs permissions: %s" % (helpperm))
    return