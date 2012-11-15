import argparse
import os
import sys
import shutil
import tarfile
from abc import ABCMeta, abstractmethod
from zipfile import ZipFile, is_zipfile
from tarfile import TarFile, is_tarfile


class CompressedFile(object):
    """Provide a uniform interface for all kinds of compressed files.

    It normalizes all zip interfaces to the TarFile interface, via
    adapter classes. An adapter should take a filename as its first
    argument and implement the full tarfile interface.

    This abstract class exists mostly as documentation so that you
    know what interface to create, we never actually check that your
    CompressedFile is a subclass of this one.
    """

    __metaclass__= ABCMeta

    @abstractmethod
    def __init__(self, fname):
        self.adaptee = CompressedFile(fname)

    @abstractmethod
    def getnames(self):
        """Return a list of top-level names in the compressed file
        """
        return self.adaptee.getnames()

    @abstractmethod
    def extractall(self):
        """Extract all files, with full paths, into dest
        """
        return self.adaptee.extractall()

    @abstractmethod
    def close(self):
        self.adaptee.close()

CompressedFile.register(TarFile)

class ZipFileAdapter(CompressedFile):

    def __init__(self, fname):
        self.adaptee = ZipFile(fname)

    def getnames(self):
        return self.adaptee.namelist()

    def extractall(self, dest='.'):
        return self.adaptee.extractall(dest)

    def close(self):
        self.adaptee.close()

class Debomber(object):
    """ Cleans up after an archive that's exploded. """

    def __init__(self, fname, rootdir=None, partial=False, preserve_paths=False,
                 Adapter=None):
        """Initialize an Debomber

        fname should be a path to an archive, tar/zip or one that Adaptor can
        handle.

        rootdir is the directory to clean up. Defaults to current directory.

        Adapter is any class that satisfies the CompresedFile api.
        """

        if Adapter is not None:
            self.cfile = Adapter(fname)
        elif is_tarfile(fname):
            self.cfile = tarfile.open(fname)
        elif is_zipfile(fname):
            self.cfile = ZipFileAdapter(fname)
        else:
            root, ext = os.path.splitext(fname)
            raise ValueError(
                "CompressedFile does not know how to deal with {0} files"
                .format(ext)
                )

        if rootdir is None:
            rootdir = os.getcwd()
        self.root = os.path.abspath(rootdir)
        self.names = self.cfile.getnames()
        self.archive_fn = os.path.basename(fname)
        self.preserve_paths = preserve_paths
        self.partial = partial
        if not self.preserve_paths:
            self.names = [n for n in self.rebase_paths()]

    def __del__(self):
        self.cfile.close()

    def _outside_root(self, fn):
        " Returns true if fn is a path lying outside self.root "
        return os.path.join(self.root, fn) == fn

    def rebase_paths(self):
        """ Rewrites filenames in archive so that they refer to a path within
        the self.root directory. Does not change archive file on disk.
        """

        for name in self.names:
            prev_name = name
            while True:
                if self._outside_root(name):
                    # name can't be placed under root
                    _, name = os.path.split(name)
                    if name == prev_name:
                        break
                    prev_name = name
                else:
                    break
            if self._outside_root(name):
                raise Exception(
                    message="Could not strip path prefix from {0}".format(
                        name))
            yield name


    def has_exploded(self):
        """ Returns true if archive appears to have exploded.
        """

        # Check if the root dir contains the files from the archive
        files = self.names[:]
        for fn in files[:]:
            if os.path.exists(os.path.join(self.root, fn)):
                files.remove(fn)
        files_found = len(self.names) - len(files)
        if self.partial and files_found > 0:
            return True
        elif files_found == len(self.names):
            return True
        elif files_found == 0:
            return False
        else:
            return files


    def clean(self):
        """Cleans up the directory.

        Does this by moving all 'sploded files into a dir with the basename of
        the cfile. This new directory will be created in the cwd unless path arg
        is supplied.

        Assumes that has_exploded() is True.
        """

        dest = self._make_extraction_dir()
        p_join = os.path.join
        for name in self.names:
            try:
                shutil.move(p_join(self.root, name), p_join(dest, name))
            except IOError as e:
                if self.partial:
                    pass
                else:
                    raise e

    def _make_extraction_dir(self):
        """ Creates and returns a directory named after the archive file

        If directory already exists then it's just returned.
        """

        dest, ext = os.path.splitext(self.archive_fn)
        dest = os.path.join(self.root, dest)

        if not os.path.exists(dest):
            os.mkdir(dest)
        return dest


def parse_args(arg_list):
    parser = argparse.ArgumentParser(description=""" An archive extractor that
    can sensibly extract zip/tar bombs, and can clean up bomb sites from less
    sensible extraction endeavors.""")

    parser.add_argument('archive', metavar="ARCHIVE",
                        help="The archive file to target.")
    parser.add_argument('-d', '--directory', metavar="DIRECTORY", default=None,
                        help="The directory file to clean up in.")
    parser.add_argument('-f', '--force', action='store_true', default=False,
       help="Clean up even if it's uncertain there was an explosion.")
    parser.add_argument('-P', '--absolute-names', action='store_true',
       help="Do not strip prefixes from absolute/relative filenames")

    return parser.parse_args(arg_list)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    dest = os.getcwd()
    debomb = Debomber(args.archive, args.directory, args.force, args.absolute_names)
    sploded = debomb.has_exploded()
    if sploded is True:
        debomb.clean()
    elif sploded is False:
        print "No bomb appears to have exploded here"
    else:
        print ("*** Partial explosion detected. The following files from the "
               "archive were not found in the directory:")
        print
        for fn in sploded:
            print fn
        print
        print "Rerun with -f to debomb anyway."
