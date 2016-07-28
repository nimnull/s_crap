import asyncio

import click
import injections
import trafaret as t

from motor.motor_asyncio import AsyncIOMotorClient
from yaml import load

from crap.db import Storage
from crap.twi.spyder import Spyder
from crap.twi.client import Client

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


configuration = t.Dict({
    'twitter': Client.trafaret,
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

    inj['twitter'] = Client(conf_data['twitter'])
    inj['storage'] = Storage(conf_data['mongo'])
    twi_spyder = inj.inject(Spyder())

    loop.run_until_complete(twi_spyder.store_twitts())

if __name__ == '__main__':
    main()

