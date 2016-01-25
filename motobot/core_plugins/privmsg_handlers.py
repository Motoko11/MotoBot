from motobot import IRCBot, hook, Priority, Modifier, EatModifier
from time import strftime, localtime
import re


@hook('PRIVMSG')
def handle_privmsg(bot, message):
    """ Handle the privmsg commands.

    Will send messages to each plugin accounting for priority and level.

    """
    nick = message.nick
    channel = message.params[0]
    message = strip_control_codes(message.params[-1])

    break_priority = Priority.min
    for plugin in bot.plugins:
        if break_priority > plugin.priority:
            break
        else:
            responses = handle_plugin(bot, plugin, nick, channel, message)
            eat = handle_responses(bot, nick, channel, responses)

            if eat is True:
                break_priority = plugin.priority


def handle_plugin(bot, plugin, nick, channel, message):
    responses = None

    try:
        if bot.get_userlevel(channel, nick) >= plugin.level:
            if plugin.type == IRCBot.command_plugin:
                responses = handle_command(plugin, bot, nick, channel, message)
            elif plugin.type == IRCBot.match_plugin:
                responses = handle_match(plugin, bot, nick, channel, message)
            elif plugin.type == IRCBot.sink_plugin:
                responses = handle_sink(plugin, bot, nick, channel, message)
    finally:
        bot.database.write_database()

    return responses


def handle_command(plugin, bot, nick, channel, message):
    trigger = bot.command_prefix + plugin.arg
    test = message.split(' ', 1)[0]

    if trigger == test:
        args = message[len(bot.command_prefix):].split(' ')
        database_entry = bot.database.get_entry(plugin.func.__module__)
        return plugin.func(bot, database_entry, nick, channel, message, args)


def handle_match(plugin, bot, nick, channel, message):
    match = plugin.arg.search(message)
    if match is not None:
        database_entry = bot.database.get_entry(plugin.func.__module__)
        return plugin.func(bot, database_entry, nick, channel, message, match)


def handle_sink(plugin, bot, nick, channel, message):
    database_entry = bot.database.get_entry(plugin.func.__module__)
    return plugin.func(bot, database_entry, nick, channel, message)


def handle_responses(bot, nick, channel, responses):
    eat = False
    if responses is not None:
        if not isinstance(responses, list):
            responses = [responses]

        for response in responses:
            command = 'PRIVMSG'
            params = [channel if channel != bot.nick else nick]
            trailing, modifiers, eat = extract_response(response)

            for modifier in modifiers:
                command, params, trailing = modifier(command, params, trailing)

            message = form_message(command, params, trailing)
            bot.send(message)
    return eat


def extract_response(response):
    trailing = ''
    modifiers = []
    eat = False

    if not isinstance(response, tuple):
        response = (response,)

    for x in response:
        if isinstance(x, str):
            trailing += x
        elif isinstance(x, Modifier):
            modifiers.append(x)
        elif isinstance(x, EatModifier):
            eat = True

    return trailing, modifiers, eat


pattern = re.compile(r'\x03[0-9]{0,2},?[0-9]{0,2}|\x02|\x1D|\x1F|\x16|\x0F+')


def strip_control_codes(input):
    """ Strip the control codes from the input. """
    output = pattern.sub('', input)
    return output


def form_message(command, params, trailing):
    message = command
    message += '' if params == [] else ' ' + ' '.join(params)
    message += '' if trailing == '' else ' :' + trailing
    return message.replace('\n', '').replace('\r', '')


def ctcp_response(message):
    """ Return the appropriate response to a CTCP request. """
    mapping = {
        'VERSION': 'MotoBot Version 2.0',
        'FINGER': 'Oh you dirty man!',
        'TIME': strftime('%a %b %d %H:%M:%S', localtime()),
        'PING': message
    }
    return mapping.get(message.split(' ')[0].upper(), None)
