"""
    A modded version of the glob module found in Python 3.10
    Modified and optimized for JREP
"""

# import contextlib
import os
import re
import fnmatch
# import itertools
import stat
import sys
# import string

__all__ = ["glob", "iglob", "escape"]

def glob(pathname, *, root_dir=None, dir_fd=None, recursive=False):
    """Return a list of paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la
    fnmatch. However, unlike fnmatch, filenames starting with a
    dot are special cases that are not matched by '*' and '?'
    patterns.

    If recursive is true, the pattern '**' will match any files and
    zero or more directories and subdirectories.
    """
    return list(iglob(pathname, root_dir=root_dir, dir_fd=dir_fd, recursive=recursive))

def iglob(pathname, *, root_dir=None, dir_fd=None, recursive=False):
    """Return an iterator which yields the paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la
    fnmatch. However, unlike fnmatch, filenames starting with a
    dot are special cases that are not matched by '*' and '?'
    patterns.

    If recursive is true, the pattern '**' will match any files and
    zero or more directories and subdirectories.
    """
    sys.audit("glob.glob", pathname, recursive)
    sys.audit("glob.glob/2", pathname, recursive, root_dir, dir_fd)
    if root_dir is not None:
        root_dir = os.fspath(root_dir)
    else:
        root_dir = pathname[:0]
    it = _iglob(pathname, root_dir, dir_fd, recursive, False)
    if not pathname or recursive and _isrecursive(pathname[:2]):
        # try:
        #     s = next(it)  # skip empty string
        #     if s:
        #         it = itertools.chain((s,), it)
        # except StopIteration:
        #     pass
        return filter(bool, it)
    return it

def _iglob(pathname, root_dir, dir_fd, recursive, dironly):
    dirname, basename = os.path.split(pathname)
    if not has_magic(pathname):
        #assert not dironly
        if basename:
            if _lexists(_join(root_dir, pathname), dir_fd):
                yield pathname
        elif _isdir(_join(root_dir, dirname), dir_fd):
            # Patterns ending with a slash should match only directories
            yield pathname
        return
    if not dirname:
        if recursive and _isrecursive(basename):
            yield from _glob2(root_dir, basename, dir_fd, dironly)
        else:
            yield from _glob1(root_dir, basename, dir_fd, dironly)
        return
    # `os.path.split()` returns the argument itself as a dirname if it is a
    # drive or UNC path.  Prevent an infinite recursion if a drive or UNC path
    # contains magic characters (i.e. r'\\?\C:').
    if dirname != pathname and has_magic(dirname):
        dirs = _iglob(dirname, root_dir, dir_fd, recursive, True)
    else:
        dirs = [dirname]
    if has_magic(basename):
        if recursive and _isrecursive(basename):
            glob_in_dir = _glob2
        else:
            glob_in_dir = _glob1
    else:
        glob_in_dir = _glob0
    for dirname in dirs:
        for name in glob_in_dir(_join(root_dir, dirname), basename, dir_fd, dironly):
            yield os.path.join(dirname, name)

# These 2 helper functions non-recursively glob inside a literal directory.
# They return a list of basenames.  _glob1 accepts a pattern while _glob0
# takes a literal basename (so it only has to check for its existence).

def _glob1(dirname, pattern, dir_fd, dironly):
    names = _iterdir(dirname, dir_fd, dironly)
    if not _ishidden(pattern):
        names = (x for x in names if not _ishidden(x))
    return fnmatch.filter(names, pattern)

def _glob0(dirname, basename, dir_fd, dironly):
    if basename:
        if _lexists(_join(dirname, basename), dir_fd):
            return [basename]
    elif _isdir(dirname, dir_fd):
        # `os.path.split()` returns an empty basename for paths ending with a
        # directory separator.  'q*x/' should match only directories.
        return [basename]
    return []

# Following functions are not public but can be used by third-party code.

# def glob0(dirname, pattern):
#     return _glob0(dirname, pattern, None, False)

# def glob1(dirname, pattern):
#     return _glob1(dirname, pattern, None, False)

# This helper function recursively yields relative pathnames inside a literal
# directory.

def _glob2(dirname, pattern, dir_fd, dironly):
    #assert _isrecursive(pattern)
    yield pattern[:0]
    yield from _rlistdir(dirname, dir_fd, dironly)

# If dironly is false, yields all file names inside a directory.
# If dironly is true, yields only directory names.
def _iterdir(dirname, dir_fd, dironly):
    try:
        dirs=[]
        fd = None
        fsencode = None
        if dir_fd is not None:
            if dirname:
                fd = arg = os.open(dirname, _dir_open_flags, dir_fd=dir_fd)
            else:
                arg = dir_fd
            if isinstance(dirname, bytes):
                fsencode = os.fsencode
        elif dirname:
            arg = dirname
        elif isinstance(dirname, bytes):
            arg = bytes(os.curdir, 'ASCII')
        else:
            arg = os.curdir
        try:
            with os.scandir(arg) as it:
                for entry in it:
                    try:
                        entryIsDir=entry.is_dir()
                        if not dironly or entryIsDir:
                            entry=entry.name
                            if fsencode is not None:
                                entry=fsencode(entry)
                            if not entryIsDir or dironly:
                                yield entry
                            else:
                                dirs.append(entry)
                    except OSError:
                        pass
            yield from dirs
        finally:
            if fd is not None:
                os.close(fd)
    except OSError:
        return

# def _listdir(dirname, dir_fd, dironly):
#     return list(_iterdir(dirname, dir_fd, dironly))
    # with contextlib.closing(_iterdir(dirname, dir_fd, dironly)) as it:
    #     return list(it)

# Recursively yields relative pathnames inside a literal directory.
def _rlistdir(dirname, dir_fd, dironly):
    names = _iterdir(dirname, dir_fd, dironly)
    for x in names:
        if not _ishidden(x):
            yield x
            #path = _join(dirname, x) if dirname else x
            #for y in _rlistdir(path, dir_fd, dironly):
            for y in _rlistdir(_join(dirname, x), dir_fd, dironly):
                yield _join(x, y)

def _lexists(pathname, dir_fd):
    # Same as os.path.lexists(), but with dir_fd
    if dir_fd is None:
        return os.path.lexists(pathname)
    try:
        os.lstat(pathname, dir_fd=dir_fd)
    except (OSError, ValueError):
        return False
    else:
        return True

def _isdir(pathname, dir_fd):
    # Same as os.path.isdir(), but with dir_fd
    if dir_fd is None:
        return os.path.isdir(pathname)
    try:
        st = os.stat(pathname, dir_fd=dir_fd)
    except (OSError, ValueError):
        return False
    else:
        return stat.S_ISDIR(st.st_mode)

def _join(dirname, basename):
    # It is common if dirname or basename is empty
    if not dirname or not basename:
        return dirname or basename
    return os.path.join(dirname, basename)

magic_check = re.compile('([*?[])')
magic_check_bytes = re.compile(b'([*?[])')

def has_magic(s):
    # Can actually just return the results as all 3 calls will conver them to bool anyway
    if isinstance(s, bytes):
        return magic_check_bytes.search(s)# is not None
    return magic_check.search(s)# is not None

def _ishidden(path):
    return path[0] in ('.', 46)

def _isrecursive(pattern):
    return pattern in ("**", b"**")

def escape(pathname):
    """Escape all special characters.
    """
    # Escaping is done by wrapping any of "*?[" between square brackets.
    # Metacharacters do not work in the drive part and shouldn't be escaped.
    if isinstance(pathname, bytes):
        return magic_check_bytes.sub(br'[\1]', pathname)
    return magic_check.sub(r'[\1]', pathname)

_dir_open_flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)
