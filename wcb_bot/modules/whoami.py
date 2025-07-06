def config(wcb):
    return {
        'events': [],
        'commands': ['whoami', 'test'],
        'permissions': [],
        'help': "Tells you who the bot thinks you are."
    }


def run(wcb, event):
    if 'test =' in event['text']: # ignore '!test = bla' events.
        return

    rtxt = "you are %s at %s" % (event['nick'], event['nickmask'])

    if event['nickmask'] == wcb.state['bot_ownermask']:
        rtxt += ", and YOU are my owner!"
    else:
        if event['user_info'] and event['user_info']['username']:
            rtxt += ", registered user " + event['user_info']['username']

            if event['user_info']['permissions']['global']:
                rtxt += ", with global perms (%s)" % ", ".join(event['user_info']['permissions']['global'])

            channel = event['channel']
            if channel in event['user_info']['permissions']:
                rtxt += ", with " + channel + " perms (" + ", ".join(event['user_info']['permissions'][channel]) + ")"

        else:
            rtxt += ", unrecognised user"

            db = wcb.db_connect()
            cur = db.cursor()
            sql = "SELECT * FROM wcb_users WHERE username ILIKE %s"
            cur.execute(sql, (event['nick'].lower(),))
            res = cur.fetchone()
            if res:
                rtxt += ", but a user was found in the DB, perhaps you need a merge?"

    return wcb.reply(rtxt)
