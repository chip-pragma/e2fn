import typing as t
import argparse as ap
import pathlib as pl
import datetime as dt
import shutil

import exifread
import tqdm


class Params:
    def __init__(self, source: pl.Path = None, destination: pl.Path = None, datetime_format: str = None, verbose=False):
        self.source = source
        self.datetime_format = datetime_format
        self.destination = destination
        self.verbose = verbose


class Report:
    def __init__(self):
        self.no_exif = []
        self.same = []
        self.not_copy = []
        self.not_file = []


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

    if dest.exists():
        dest.rmdir()
    dest.mkdir()

    return dest


def parse_args() -> t.Optional[Params]:
    parser = ap.ArgumentParser(prog='e2fn', add_help=True)

    parser.add_argument('-s', '--source',
                        required=True,
                        metavar='DIR_PATH',
                        type=check_path_dir,
                        help='Директория с изображениями')
    parser.add_argument('-f', '--format',
                        required=True,
                        metavar='FORMAT',
                        help='Формат имен целевых файлов')
    parser.add_argument('-p', '--postfix',
                        default='e2fs',
                        metavar='POSTFIX',
                        help='Суффикс названия целевой дирректории')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Выводить подробный отчет')

    args = parser.parse_args()

    try:
        destination = make_destination_dir(args.source, args.postfix)
    except OSError as e:
        parser.error(str(e))
        return

    return Params(
        source=args.source,
        destination=destination,
        datetime_format=args.format,
        verbose=args.verbose
    )


def work(params: Params) -> Report:
    images = (
        *params.source.glob('*.jpg'),
        *params.source.glob('*.jpeg')
    )

    report = Report()

    with tqdm.tqdm(images, unit='image', ascii=True) as progress:
        for file in progress:
            if file.is_file():
                # extract metadata
                progress.set_postfix_str(f'{file.name} ==> EXIF...')
                with file.open('rb') as image:
                    tags = exifread.process_file(image)

                # parse datetime
                exif_datetime = tags.get("Image DateTime")
                if not exif_datetime:
                    report.no_exif.append(file.name)
                    continue

                image_datetime = dt.datetime.strptime(exif_datetime.values, '%Y:%m:%d %H:%M:%S')

                # new file name
                new_stem = image_datetime.strftime(params.datetime_format)

                idx = 0
                number = ''
                while True:
                    new_file_name = new_stem + number + file.suffix
                    new_file_path = params.destination / new_file_name

                    if new_file_path.exists():
                        idx += 1
                        number = f'_{idx:02}'
                    else:
                        if idx != 0:
                            report.same.append(new_file_path.name)
                        break

                # copy
                progress.set_postfix_str(f'{file.name} ==> {new_file_name}')
                shutil.copy2(str(file), str(new_file_path))

                # check
                if not new_file_path.exists():
                    report.not_copy.append(file.name)
            else:
                report.not_file.append(file.name)

    return report


def main():
    params = parse_args()

    print(f'source         {params.source}')
    print(f'destination    {params.destination}')

    report = work(params)

    if params.verbose:
        tab = '\n    '
        report_no_exif = tab + tab.join(report.no_exif)
        report_same = tab + tab.join(report.same)
        report_not_copy = tab + tab.join(report.not_copy)
        report_not_file = tab + tab.join(report.not_file)
    else:
        report_no_exif = len(report.no_exif)
        report_same = len(report.same)
        report_not_copy = len(report.not_copy)
        report_not_file = len(report.not_file)

    print(f'Without EXIF: {report_no_exif}')
    print(f'With same datetime: {report_same}')
    print(f'Unable to copy: {report_not_copy}')
    print(f'Is not file: {report_not_file}')


if __name__ == '__main__':
    main()
