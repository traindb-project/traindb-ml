
from etrimlclient.io import filereader

import os

class GetXY:
    def __init__(self, backend='None'):
        self.backend = backend
        self.freader = None

    def read(self, file, y, x):
        if self.backend == 'None':
            self.freader = filereader.CsvReader()
            return self.freader.read(file, y, x)[0:2]
        else:
            print("Other backend server is not currently supported.")
            return 9999,9999

    def get_n_points(self):
        return self.freader.n_row



if __name__ == "__main__":
    reader = GetXY(backend=None)
    # print(reader.read("../../resources/pm25.csv", y='pm25', x='PRES'))

    # get current path
    currentPath = os.getcwd()
    print(f'# current path: {currentPath}')

    newPath = currentPath + '/9-approximate_query_processing/ETRIMLClient/'
    os.chdir(newPath)

    print(f'# changed path: {os.getcwd()}')

    
    filepath = os.getcwd() + '/etrimlwarehouse/pm25.csv'

    print(filepath)

    print(reader.read(filepath, y='pm25', x='PRES'))

