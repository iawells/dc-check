import click
import logging
import dc_check.server


@click.command()
@click.option('--db', type=click.Path(dir_okay=False,
                                      file_okay=True,
                                      writable=True,
                                      readable=True),
              help='JSON datastore to read and write',
              required=True)
@click.option('--port', type=click.IntRange(min=1, max=65535),
              default=10101,
              help='REST server port')
def main(db: str, port: int) -> None:
    LOG = logging.getLogger(__name__)

    dc_check.server.run(db, port)

    LOG.info('server finished')


if __name__ == '__main__':
    main()
