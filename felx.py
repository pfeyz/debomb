import argparse
import os
import sys

def parse_args(arg_list):
    parser = argparse.ArgumentParser(description=""" An archive extractor that
    can sensibly extract zip/tar bombs, and can clean up bomb sites from less
    sensible extraction endeavors.""")

    parser.add_argument('archive', metavar="ARCHIVE",
                        help="A zip or tar file to target.")

    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('-x', '--extract', action='store_true', help="""
    Extracts ARCHIVE. Extracts to a new directory if the archive is a bomb. The
    new directory is named after ARCHIVE.""")  # by removing the file extension,
                                               # but what is there is none?
    action.add_argument('-c', '--clean', action='store_true', help=""" Cleans up
    from an explosion of ARCHIVE. Moves all debris files to a new dir named
    after ARCHIVE.""")

    directory = parser.add_mutually_exclusive_group()
    directory.add_argument('-d', '--destination',
                       help="Put files in SOURCE_DIR instead of cwd")

    return parser.parse_args(arg_list)

def clean_bomb_site(archive, destination):
    """ Takes the files that exploded from archive and moves them to a new
    directory in destination.

    archive is a filename and source and destination are both directory names.

    """
    print("Cleaning up after", archive, "moving debris to", destination)
    raise NotImplementedError

def extract(filename, dest):
    print("Extracting", filename, "to", dest)
    raise NotImplementedError

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    dest = os.getcwd()
    if args.destination:
        dest = args.destination
    if args.extract:
        extract(args.archive, dest)
    elif args.clean:
        clean_bomb_site(args.archive, dest)
