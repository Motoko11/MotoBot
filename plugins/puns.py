from motobot import command, match
from requests import get
from bs4 import BeautifulSoup


@command('joke')
@match(r'(tell|give) (me|us) a joke')
def joke_command(bot, database, nick, channel, message, *args, **kwargs):
    """ Joke command for returning the latest in shit jokes. """
    return get_joke();


@command('pun')
@match(r'(tell|give) (me|us) a pun')
def pun_command(bot, database, nick, channel, message, *args, **kwargs):
    """ These punny one liners sure to lighten up your day. """
    return get_pun()


def get_pun():
    url = 'http://www.punoftheday.com/cgi-bin/randompun.pl'
    bs = BeautifulSoup(get(url).text)
    pun = bs.find('p', recursive=True).text
    return pun


def get_joke():
    url = 'http://www.rinkworks.com/jokes/random.cgi'
    bs = BeautifulSoup(get(url).text)
    joke = bs.find_all('ul', recursive=True)[2].text.replace('\n', ' ').strip()
    return joke
