import numpy
from scipy import stats

def statdat( dataset , Xcol, Ycol,  **kwargs):
  """Set is a numpy array of data.  This function looks for rows
     that have Xcol in common and for each different value of Xcol
     gives out the mean and standard error of the maean.  
     
     The result is returned as a numpy array.   
  """
  #print dataset
  #print Xcol
  #print Ycol
  out =[]
  # This loop handles rows in the array one by one
  ndiscarded = 0 
  while dataset.shape[0] != 0: 
    #print "# of rows in array = %d" % set.shape[0]
    #print set

    if Xcol >= dataset.shape[1] :
      print "Column index for stat dat is larger than data columns available!"
      exit(1)
    
    Xval = dataset [0, Xcol]
    Yval = []

    to_delete = []
    if numpy.isnan(Xval):
      to_delete.append(0)
      dataset = numpy.delete( dataset, to_delete , 0)
      continue

    for i in range( dataset.shape[0] ) :
      row = dataset[i,:]
      if row[Xcol] == Xval:
        to_delete.append(i)

        yvalue = row[Ycol] 
        discard = kwargs.get('discard',None)
        if discard is not None:
            use = True
            if 'y>' in discard.keys():
                if yvalue > discard['y>']:
                    use = False 
            if 'y<' in discard.keys():
                if yvalue < discard['y<']:
                    use = False
        else:  
            use = True
                 
        if use :
            Yval.append( yvalue ) 
        else:
            ndiscarded +=1 

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
  out = numpy.array(out) 
  try:
      out = out[ out[:,0].argsort() ] 
  except:
      print "\n...Error in statdat.py"
      print "\tXcol=%d  Ycol=%d"%(Xcol,Ycol) 
      print "\tinput dataset:"
      print "\t",dataset

  if ndiscarded > 0:
      print "\tATTENTION: statdat discarded %d shots" % ndiscarded
  return numpy.array( out )


