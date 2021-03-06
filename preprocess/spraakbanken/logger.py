'''
Custom logger class, that can be used for minor logging during batch jobs on the DTU hpc.
'''
import os
import uuid

class Logger:
    '''
    Logger class for saving text logs from data preprocessing steps
    '''
    def __init__(self):
        self.dir = 'logs'
        self.id = uuid.uuid4()

        #Create log dir if not exists
        if not os.path.isdir(self.dir):
            os.mkdir(self.dir)

        #Write info file for latest run
        with open(os.path.join(self.dir, 'log_history.txt'), 'a+') as history:
            history.write(f'Created logger with log path: {os.path.join(self.dir, str(self.id))}\n')

    def write_line(self, content:str, verbose:bool=False):
        if verbose: 
            print(content)
        with open(f'{os.path.join(self.dir, str(self.id))}.md', 'a+') as f:
            f.write(f'{content}\n')

    def write(self, content:str, verbose:bool=False):
        if verbose:
            print(content)
        with open(f'{os.path.join(self.dir, str(self.id))}.md', 'a+') as f:
            f.write(content)
