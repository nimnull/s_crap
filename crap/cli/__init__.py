import asyncio

import click
import injections
import trafaret as t

from yaml import load

from crap.db import Storage
from crap.logs import logger
from crap.twi.spyder import StreamingSpyder
from crap.twi.streaming import StreamingClient

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


configuration = t.Dict({
    'twitter': StreamingClient.trafaret,
    'mongo': t.String,
}).ignore_extra('*')


@click.command()
@click.option('--config', '-c', help="Configuration path")
def main(config):
    with open(config, 'rb') as fp:
        conf_data = load(fp.read(), Loader=Loader)

    conf_data = configuration.check(conf_data)
    loop = asyncio.get_event_loop()

    inj = injections.Container()

    inj['client'] = StreamingClient(conf_data['twitter'])
    logger.debug("Created twitter client")
    inj['storage'] = Storage(conf_data['mongo'])
    inj['config'] = conf_data
    logger.debug("Created storage")
    twi_spyder = inj.inject(StreamingSpyder())
    logger.debug("Created spyder")

    loop.run_until_complete(twi_spyder.get_twitts())

if __name__ == '__main__':
    main()

