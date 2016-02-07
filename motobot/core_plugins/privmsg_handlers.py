from motobot import IRCBot, hook, Priority, Modifier, EatModifier, Eat, Notice, match
from time import strftime, localtime
from re import compile


@hook('PRIVMSG')
def handle_privmsg(bot, message):
    """ Handle the privmsg commands.

    Will send messages to each plugin accounting for priority and level.

    """
    nick = message.nick
    channel = message.params[0]
    message = strip_control_codes(transform_action(nick, message.params[-1]))

    break_priority = Priority.min
    for plugin in bot.plugins:
        if break_priority > plugin.priority:
            break
        else:
            responses = handle_plugin(bot, plugin, nick, channel, message)
            target = channel if channel != bot.nick else nick
            responses = [responses] if responses is not None else None
            eat = handle_responses(bot, responses, [target])

            if eat is True:
                break_priority = plugin.priority


def handle_plugin(bot, plugin, nick, channel, message):
    responses = None

    alt = bot.get_userlevel(channel, nick) < plugin.level
    if plugin.type == IRCBot.command_plugin:
        responses = handle_command(plugin, bot, nick, channel, message, alt)
    elif plugin.type == IRCBot.match_plugin:
        responses = handle_match(plugin, bot, nick, channel, message, alt)
    elif plugin.type == IRCBot.sink_plugin:
        responses = handle_sink(plugin, bot, nick, channel, message, alt)

    return responses


def handle_command(plugin, bot, nick, channel, message, alt):
    trigger = bot.command_prefix + plugin.arg.trigger
    test = message.split(' ', 1)[0]

    if trigger == test:
        args = message[len(bot.command_prefix):].split(' ')
        database_entry = bot.database.get_entry(plugin.func.__module__)
        func = plugin.func if not alt else plugin.alt
        if func is not None:
            return func(bot, database_entry, nick, channel, message, args)


def handle_match(plugin, bot, nick, channel, message, alt):
    match = plugin.arg.search(message)
    if match is not None:
        database_entry = bot.database.get_entry(plugin.func.__module__)
        func = plugin.func if not alt else plugin.alt
        if func is not None:
            return func(bot, database_entry, nick, channel, message, match)


def handle_sink(plugin, bot, nick, channel, message, alt):
    database_entry = bot.database.get_entry(plugin.func.__module__)
    func = plugin.func if not alt else plugin.alt
    if func is not None:
        return func(bot, database_entry, nick, channel, message)


def handle_responses(bot, responses, params, command='PRIVMSG'):
    eat = False
    if responses is not None:
        will_eat, modifiers, trailings, iters = extract_responses(responses)
        eat |= will_eat

        for modifier in modifiers:
            command = modifier.modify_command(command)
            params = modifier.modify_params(params)

        if len(trailings) == 0 and len(modifiers) != 0:
            trailings = ['']

        for trailing in trailings:
            for modifier in modifiers:
                trailing = modifier.modify_trailing(trailing)
            message = form_message(command, params, trailing)
            bot.send(message)

        for iter in iters:
            eat |= handle_responses(bot, iter, params, command)

    return eat


def extract_responses(responses):
    will_eat = False
    modifiers = []
    trailings = []
    iters = []

    for x in responses:
        if isinstance(x, EatModifier):
            will_eat = True
        elif isinstance(x, str):
            trailings.append(x)
        elif isinstance(x, Modifier):
            modifiers.append(x)
        else:
            iters.append(x)

    return will_eat, modifiers, trailings, iters


pattern = compile(r'\x03[0-9]{0,2},?[0-9]{0,2}|\x02|\x1D|\x1F|\x16|\x0F+')


def strip_control_codes(input):
    """ Strip the control codes from the input. """
    output = pattern.sub('', input)
    return output


def transform_action(nick, msg):
    """ Transform an action CTCP into a message. """
    if msg.startswith('\x01ACTION ') and msg.endswith('\x01'):
        return '*' + nick + msg[7:-1]
    else:
        return msg


def form_message(command, params, trailing):
    message = command
    message += '' if params == [] else ' ' + ' '.join(params)
    message += '' if trailing == '' else ' :' + trailing
    return message.replace('\n', '').replace('\r', '')


@match(r'\x01(.*)\x01', priority=Priority.max)
def ctcp_match(bot, database, nick, channel, message, match):
    ctcp_req = match.group(1)
    reply = ctcp_response(ctcp_req)
    if reply is not None:
        return reply, Notice(nick), Eat


def ctcp_response(message):
    """ Return the appropriate response to a CTCP request. """
    mapping = {
        'VERSION': 'MotoBot Version 2.0',
        'FINGER': 'Oh you dirty man!',
        'TIME': strftime('%a %b %d %H:%M:%S', localtime()),
        'PING': message
    }
    response = mapping.get(message.split(' ', 1)[0].upper(), None)
    if response is not None:
        return "\x01{}\x01".format(response)
