#! /usr/bin/env python

'''
Created on May 19, 2010

@author: sbaker
'''

import threading
import Queue
import sys, os

try:
    jobFileString = sys.argv[1] ; numberProcs = int(sys.argv[2])
except:
    print "Usage:",sys.argv[0], "run_raw2slc numberOfProcessors" ; sys.exit(1)

jobFile = open(jobFileString)
runJobs = jobFile.readlines()
jobFile.close()

class Worker(threading.Thread):

    def __init__(self, queue):
        self.__queue = queue
        threading.Thread.__init__(self)

    def run(self):
        while 1:
            job = self.__queue.get()
            if job is None:
                break # reached end of queue
            # RUN THE COMMAND
            os.system(job)
            #print "Finished ", job

# run with limited queue
queue = Queue.Queue(1)
for i in range(numberProcs): Worker(queue).start() # start a worker
for job in runJobs: queue.put(job.rstrip())
for i in range(numberProcs): queue.put(None) # add end-of-queue markers
