

"""

Object for maintaining a groundwater series iterator

T.J. de Meij januari 2020

""" 


class GwList():
    """
        Groundwater series list container for iterating groundwate rseries
    """

    def __repr__(self):
        return (f'{self.__class__.__name__}()')


    def __init__(self,sourcedir=None,sourcetype=None):
        self.value = 0


    def __iter__(self):
        return self


    def __next__(self):
        next_value = self.value
        self.value += 2
        return next_value


    @classmethod
    def from_dinofiles(cls,filedir=None,fileplist=None):
        """ 
        read tno dinoloket csvfiles

        parameters
        ----------
        filedir : str
        filelist : list


        returns
        -------
        result : dinofiles iterator

        """

        return cls()
