#!/usr/bin/python

import sys
from configobj import ConfigObj
import numpy

from StringIO import StringIO

import argparse
import os

#Comment

def evalstr( report, string):
  try:
    tokens = string.split()
    report = ConfigObj(report)
  except:
    return numpy.nan
  valid = True
  for i,tok in enumerate(tokens):
    if ':' in tok:
      try:
        sec = tok.split(':')[0]
        key = tok.split(':')[1]
        tokens[i] = report[sec][key]
      except:
        valid = False
  if valid:
    return eval( " ".join(tokens) )
  else:
    return numpy.nan 
    
     

def parse_range(rangestr):
  shots=[]
  l = rangestr.split(',')
  for token in l:
    if token.find(':') > -1: 
      sh0 = int(token.split(':')[0])
      shf = int(token.split(':')[1])
      if shf < sh0:
        sys.stderr.write("\n --->  RANGE ERROR: end of range is smaller than start of range\n\n")
        return
      for num in range(sh0,shf+1):
        numstr = "%04d" %num
        shots.append(numstr)
    elif token.find('-') == 0:
      l2 = token.split('-')[1:]
      for shot in l2:
        numstr = "%04d" % int(shot)
        if numstr in shots:
          shots.remove(shot)

  return shots

def qrange_eval( dir, range, keys):
  np = numpy
  fakefile=""
  shots=parse_range(range)
  errmsg=''
  #rawdat='#%s%s\n' % ('SEQ:shot\t','\"'+'\t'.join(keys)+'\"')
  rawdat = '#\n# Column index\n#  0  %s\n' % 'SEQ:shot'
  for i,Y in enumerate( keys ):
      rawdat = rawdat + '#  %d  %s\n' % ( i+1, Y )
  if shots is None:
    errmsg = "Range did not contain any valid shots."
    print errmsg
    return numpy.array([]), errmsg, rawdat
     
  for shot in shots:
    #report = dir + 'report' + shot + '.INI'
    report = os.path.join(dir ,  'report' + shot + '.INI')
    report = ConfigObj(report)
    if report == {}:
      errmsg=errmsg + "...Report #%s does not exist in %s!\n" % (shot,dir)
      continue
    fakefile = fakefile + '\n'
    rawdat = rawdat + '\n%s\t\t' % shot
    line=''
    line_=''
    err=False
    for s in keys:
      try:
        val = evalstr(report, s)
        if numpy.isnan(val):
            raise KeyError
        line = line + str(val) + '\t'
        fval = float(val)
        if fval > 1e5 or fval < -1e5:
          lstr = '%.3e\t\t' % fval
        else: 
          lstr = '%.4f\t\t' % fval
        line_ = line_ + lstr
      except KeyError:
        err= True
        errstr = '...Failed to get %s from #%s\n' % (s, shot)
        errmsg = errmsg + errstr
    if not err:
      fakefile = fakefile + line
      rawdat = rawdat + line_
   
  a = numpy.loadtxt(StringIO(fakefile))
  if errmsg != '':
      print errmsg
  return a, errmsg, rawdat

def qrange(dir,range,keys):
  fakefile=""
  shots=parse_range(range)
  errmsg=''
  rawdat='#%s%s\n' % ('SEQ:shot\t',keys.replace(' ','\t'))

  for shot in shots:
    report = os.path.join(dir ,  'report' + shot + '.INI')
    report = ConfigObj(report)
    if report == {}:
      errmsg=errmsg + "...Report #%s does not exist in %s!\n" % (shot,dir)
      continue
    fakefile = fakefile + '\n'
    rawdat = rawdat + '\n%s\t\t' % shot
    line=''
    line_=''
    err=False
    for pair in keys.split(' '):
      sec = pair.split(':')[0]
      key = pair.split(':')[1]
      try:
        val = report[sec][key]
        line = line + val + '\t'
        fval = float(val)
        if fval > 1e5 or fval < -1e5:
          lstr = '%.3e\t\t' % fval
        else: 
          lstr = '%.4f\t\t' % fval
        line_ = line_ + lstr
      except KeyError:
        err= True
        errstr = '...Failed to get %s:%s from #%s\n' % (sec, key, shot)
        errmsg = errmsg + errstr
    if not err:
      fakefile = fakefile + line
      rawdat = rawdat + line_
   
  a = numpy.loadtxt(StringIO(fakefile))
  print errmsg
  return a, errmsg, rawdat
 
 

# --------------------- MAIN CODE  --------------------#


if __name__ == "__main__":
  linux = True
  Windows = False
  if linux:
    prefix = "/lab/"
  elif Windows:
    prefix = "L:/"
  else:
    print " ---> Unrecognized operating system!!"  
    exit(1)
  
  parser = argparse.ArgumentParser('qrange.py')

  parser.add_argument('range', action = "store", \
         help="range of shots to be used.")

  parser.add_argument('KEYS', action="store", nargs='*',\
         help='print all keys in this list')
  
  parser.add_argument('--histo',\
        help='shows a histogram of the specified column')


  args = parser.parse_args()

   
  a, errmsg, rawdat = qrange_eval( os.getcwd(), args.range, args.KEYS) 
  print rawdat

  if args.histo != None:
      import numpy as np
      import matplotlib.pyplot as plt
      import matplotlib.mlab as mlab


      fig = plt.figure()
      ax = fig.add_subplot(111)

      col = int(args.histo) - 1
      # the histogram of the data
      n, bins, patches = ax.hist( a[:,col] , 50, normed=False, facecolor='green', alpha=0.75)
      plt.show()
