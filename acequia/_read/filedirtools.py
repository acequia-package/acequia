""" Funtions for working with files and directories """
import warnings
import os.path
import errno
import os


def listdir(dirpath,filetype=None):
    """Return list of full path of all files in a directory

    Parameters
    ----------
    dirpath : str
        path to directory

    filetype : str, optionally
        list files of type <filetype> only

    Returns
    -------
    list
    """
    if not os.path.isdir(dirpath):
        msg = f'directory {dirpath} not found'
        raise ValueError(msg)

    ##filelist = [f for f in os.listdir(dirpath)
    ##if os.path.isfile(os.path.join(dirpath,f))]
    filelist = [f.path for f in os.scandir(dirpath) if f.is_file()]

    if filetype is not None:
        filelist = [f for f in filelist if f.endswith(filetype)]

    return filelist


def cleardir(dirpath,filetype=None):
    """ delete all existing files in directory 

    Parameters
    ----------
    dirpath : str
        path to directory with files

    filetype : str, optional
        type of files to delete

    """
    for filename in os.listdir(dirpath):

        fpath = os.path.join(dirpath, filename)
        try:
            if os.path.isfile(fpath) or os.path.islink(fpath):
                if filetype is None:
                    os.unlink(fpath)
                elif filetype in os.path.splitext(filename)[1]:
                    os.unlink(fpath)
            #elif os.path.isdir(fpath):
            #    shutil.rmtree(fpath)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

