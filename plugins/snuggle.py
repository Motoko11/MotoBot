from motobot import command, Action


@command('snuggle')
def snuggle_command(bot, database, nick, channel, message, args):
    response = ''
    if len(args) > 1:
        response = 'snuggles ' + ' '.join(args[1:])
    else:
        response = 'snuggles ' + nick

    return response, Action


@command('unsnuggle')
def unsnuggle_command(bot, database, nick, channel, message, args):
    return "Go ahead and call the cops... You can't be unsnuggled!"


@command('pat')
def pat_command(bot, database, nick, channel, message, args):
    response = ''
    if len(args) > 1:
        response = 'pat pats ' + ' '.join(args[1:])
    else:
        response = 'pat pats ' + nick

    return response, Action


@command('pet')
def pet_command(bot, database, nick, channel, message, args):
    response = ''
    if len(args) > 1:
        response = 'pets ' + ' '.join(args[1:])
    else:
        response = 'pets ' + nick

    return response, Action
