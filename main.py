import typing as t
import argparse as ap
import pathlib as pl


class Params:
    def __init__(self, source: pl.Path = None, destination: pl.Path = None):
        self.source = source
        self.destination = destination


def check_path_dir(path: t.Union[str, pl.Path]) -> pl.Path:
    path = pl.Path(path) if isinstance(path, str) else path
    try:
        if path.exists() and path.is_dir():
            return path.resolve()
        else:
            raise ValueError(f'Несуществующая директория: <{path}>')
    except (OSError, ValueError) as e:
        raise ap.ArgumentTypeError(e)


def make_destination_dir(source: pl.Path, postfix: str) -> pl.Path:
    dest_str = f'{source.resolve()}.{postfix}'
    dest = pl.Path(dest_str)
    dest.mkdir()
    return dest


def parse_args() -> t.Optional[Params]:
    parser = ap.ArgumentParser(prog='e2fn', add_help=True)

    source_dir = parser.add_argument(
        '-s', '--source',
        required=True,
        metavar='DIR_PATH',
        type=check_path_dir)

    postfix = parser.add_argument(
        '-p', '--postfix',
        default='e2fs',
        metavar='POSTFIX'
    )

    args = parser.parse_args()

    try:
        destination = make_destination_dir(args.source, args.postfix)
    except OSError as e:
        parser.error(str(e))
        return

    return Params(
        source=args.source,
        destination=destination
    )


def main():
    params = parse_args()

    print(f'source         {params.source}')
    print(f'destination    {params.destination}')


if __name__ == '__main__':
    main()
