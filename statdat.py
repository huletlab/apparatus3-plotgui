import numpy
from scipy import stats

def statdat( dataset , Xcol, Ycol):
  """Set is a numpy array of data.  This fuction looks for rows
     that have Xcol in common and for each different value of Xcol
     gives out the mean and standard error of the maean.  
     
     The result is returned as a numpy array.   
  """
  #print dataset
  #print Xcol
  #print Ycol
  out =[]
  while dataset.shape[0] != 0: 
    #print "# of rows in array = %d" % set.shape[0]
    #print set
    
    Xval = dataset [0, Xcol]
    Yval = []

    to_delete = []
    if numpy.isnan(Xval):
      to_delete.append(0)
      dataset = numpy.delete( dataset, to_delete , 0)
      continue

    if Xcol >= dataset.shape[1] :
      print "Column index for stat dat is larger than data columns available!"
      exit(1)
 
    for i in range( dataset.shape[0] ) :
      row = dataset[i,:]
      if row[Xcol] == Xval:
        to_delete.append(i)
        Yval.append( row[Ycol]) 
    dataset = numpy.delete( dataset, to_delete , 0)
    #print "# of rows in array = %d" % set.shape[0]
    #print set 
    Yarray = numpy.array( Yval)
    mean = numpy.mean(Yarray)
    stddev = numpy.std(Yarray)
    serror = stats.sem(Yarray)
    pkpk = numpy.max( Yarray) - numpy.min( Yarray )
    #print Yval
    out.append( [Xval, mean, stddev, serror, pkpk] ) 
  return numpy.array( out )


