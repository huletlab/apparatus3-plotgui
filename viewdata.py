import threading 
import time

from  traits.api import HasTraits, Str, Bool, Float, Instance, String, Button,\
                        List, Enum, Int

from traitsui.api import View, Item, Group, HGroup, VGroup, HSplit, VSplit,\
                         Handler, CheckListEditor, EnumEditor, ListStrEditor,\
                         ArrayEditor, spring, ListEditor, CodeEditor, TextEditor

from traitsui.menu import NoButtons
from traitsui import file_dialog 
from enable.component_editor import ComponentEditor
from chaco.chaco_plot_editor import ChacoPlotItem
from mpl_figure_editor import MPLFigureEditor
from matplotlib.figure import Figure
from scipy import stats

import wx
from random import choice

import numpy
import matplotlib
import copy
import pickle
from configobj import ConfigObj
import os

import qrange
from fitlibrary import Fits

#-------------------------------------------------------------------------------#
#
#  SOME DEFAULT SETTINGS FOR PLOTS
#
#-------------------------------------------------------------------------------#
global colors 
colors = ['#0D8800','#1729E0','#00A779','#D8005F','green','red','magenta','black']
markers = ['.', 's', 'x', 'D', '+', '*', 'o', '2', '1']
default_ms = 10.
default_me = 1.
legsz = 8.


#-------------------------------------------------------------------------------#
#
#  GLOBAL SETTINGS 
#
#-------------------------------------------------------------------------------#

import os
import plotconf
import datetime 
plotconfini, plotgui_path, mainpck, load_pck, use_date =  plotconf.initplotgui()
conf = ConfigObj(plotconfini)
print "Using INI file %s" % plotconfini
print "Plotgui base path is %s" % plotgui_path
print "Main pck file path is %s" % mainpck

# The correct paths are stored in the plotconfini.INI file

#LastAnalyzed is used to control the refreshing of the plot when the autoplot option is 
#selected. 
def LastAnalyzed():
    LASTNUM = conf['DIRECTORIES']['lastnum']
    path_is_relative = LASTNUM[0] != '/' and not ':' in LASTNUM  #works for Win and Linux
    if path_is_relative:
      LASTNUM = plotgui_path + '/' + LASTNUM
    file = open( LASTNUM,'r')

    file.close()
    return lastnum

#DataDir is used in the initialization of a new DataSet.  DataSet are generally created
#by copying them, rather tham from scratch, so this is rarely used.
def DataDir():
    DATADIR = conf['DIRECTORIES']['datadir']
    path_is_relative = DATADIR[0] != '/' and not ':' in DATADIR  #Works for Win and Linux
    if path_is_relative: 
      DATADIR = os.path.join(plotgui_path, DATADIR)
    if use_date:
      today = datetime.date.today()
      date_path = today.strftime('%Y/%y%m/%y%m%d')
      DATADIR  = os.path.join( DATADIR, date_path )
    return DATADIR

#-------------------------------------------------------------------------------#
#
#  DATA SET
#
#-------------------------------------------------------------------------------#
class DataSet(HasTraits):
    """ Object that holds the information defining a data set"""
    def _setfitexprs_(self):
        self.fit1._setfitexprs_()

    # Data set tab
    name = Str
    descr = Str( '', label="Description", desc="describe the contents of the data set", editor=TextEditor())
    plotme = Bool(False, label="plot?")
    X2 = Bool(False, label="X2?")
    Y2 = Bool(False, label="Y2?")
    ST = Bool(False,label="stats?")
    logscaleX = Bool(False,label="logX?")
    logscaleY = Bool(False,label="logY?")
    gridlines = Bool(False,label="grid?")
   
    xticks = Bool(True,label='xticks?')
    yticks = Bool(True,label='yticks?')
 
    X = Str('SEQ:Shot', label="X")
    Y = Str('CPP:nfit', label="Y")

    title = Str('', label="Title")
    legend = Str('', label="Leg")
    xlabel = Str('',label="Xl")
    ylabel = Str('',label="Yl")

    Xmin = Float(numpy.nan)
    Xmax = Float(numpy.nan)
    Ymin = Float(numpy.nan)
    Ymax = Float(numpy.nan)
    

    c = Str('green', label="c") 
    mfc = Str('None', label="f")
    match = Bool(True,label="match?")
 
    m = Str('o', label="fmt") 
    ms = Float(default_ms, label="s")
    me = Float(default_me, label="mew")
 
    datadir = Str( DataDir(), label="DataDir")
    range = Str( '', label="Range")
    fit1 = Instance(Fits, ())
    
    # Raw data tab
    raw_data = String()
    saveraw = Button('Save Raw Data')
  
    # Stats tab
    stat = String()

    fitw=350
    descr_label = Str('Description:')
    title_label = Str('Title:')
    view = View( Group(
                Group(
                           HGroup( Item('plotme'), 
                                   Item('X2'), 
                                   Item('Y2'), 
                                   Item('ST'),
                                   Item('gridlines'),),
                           HGroup(
                                   Item('logscaleX'), 
                                   Item('logscaleY'),
                                   Item('xticks'),
                                   Item('yticks'),),
                           VGroup(
                            HGroup(Item('name',springy=True),),
                            #HGroup(Item('descr_label', style='readonly', show_label=False),
                            HGroup(Item('descr', show_label=True, springy=True),), #springy=False),
                            # HGroup(
                            #  springy=False ),
                            ),
 
                           orientation ='vertical', show_border = True,
                          ),
                Group(
                      VGroup( HGroup(Item('datadir',springy=True),),
                              HGroup(Item('range',springy=True), ), ),
                      HGroup( Item('X',springy=True,show_label=True)), 

                      HGroup( Item('Y',springy=True,show_label=True)), 
                      show_border = True,
                     ),
                Group(
                      HGroup( Item('xlabel', show_label=True, springy=True), Item('Xmin',show_label=True), Item('Xmax',show_label=True) ),
                      HGroup( Item('ylabel', show_label=True, springy=True), Item('Ymin',show_label=True), Item('Ymax',show_label=True) ),
                      HGroup( Item('legend', show_label=True, springy=True), ),
                      HGroup( Item('c'),  Item('mfc'), Item('match'),),
                      HGroup( Item('m',width=-30), Item('ms',width=-40), Item('me',width=-40),),
                       orientation='vertical',
                      show_border = True),
                Group(
                      Item('fit1', style='custom', show_label=False),
                      show_border = True, label='Fit' ),
                     label='Set', scrollable=True   ),

                            
                Group(Item('raw_data',show_label=False, springy=True, style='custom'),
                      Item('saveraw',show_label=False),label='Raw Data'),


                Group(Item ('stat',show_label=False, springy=True, style='custom'),
                      label='Stats'),

                dock='tab',  scrollable= True, )

    def getdata_(self):
       	""" Executes qrange to extract data from reports. 
      	"""
        #data, errmsg, rawdat = qrange.qrange(self.datadir, self.range, self.X + " " + self.Y)
        data, errmsg, rawdat = qrange.qrange_eval(self.datadir, self.range, [self.X , self.Y])

        msg=None
        if data.shape == (0,):
            msg =  "Data set yields no valid points:\n\n  RANGE = %s\n      X = %s\n      Y = %s\n"  % (self.range, self.X, self.Y)
            print msg
            return data, msg, False
        self.raw_data = rawdat
        colnames = rawdat.split('\n')[0]
        colnames = colnames[1:].split('\t')[1:]

        #Get basic statistics for all columns in data
        s = ''
        for i in range(data.shape[1]):
          col = data[:,i]
          s00 = numpy.mean( col ) #mean 
          s02 = numpy.std( col ) #standard deviation
          s03 = numpy.max( col ) - numpy.min( col ) # peak to peak value
          s01 = stats.sem( col ) #standard error of the mean 
          #s = s + colnames[i] + ':\n'
          s = s + "Mean                   = %10.6f\n" %  s00
          s = s + "Std. deviation         = %10.6f\n" %  s02
          s = s + "Std. error of the mean = %10.6f\n" %  s01
          s = s + "Pk-Pk                  = %10.6f\n" %  s03
          s = s + '\n'
        self.stat = s

        #Get data that is reduced statistically. This means that if there is more 
        #than 1 point for a given value of X,then the average and error will be used
        #The results of this operation are stored in a list called sdata:
        #
        #	sdata = (mean, standard deviation, pk-pk, standard error of the mean) 
        sdata=None
        if self.X == "SEQ:shot" and self.ST: 
            s = [ numpy.mean( data[:,1] ), \
                  numpy.std( data[:,1]), \
                  stats.sem( data[:,1]), \
                  numpy.max( data[:,1]) - numpy.min(data[:,1]) \
                ]
            a = []
            for val in s:
              a.append( [ val for i in range( data[:,1].size ) ] )
            sdata = numpy.c_[ data[:,0],  numpy.transpose(numpy.array(a)) ]
        elif self.ST:
            import statdat
            sdata = statdat.statdat( data, 0, 1)

        return data, sdata, msg, True
 
    def _saveraw_changed(self):
        """ Save raw data to choosen location"""
      
        file_name =  savefile_dialog("Save raw data","dat")
        if file_name != None:
            file_raw=open(file_name,"w+b")
            file_raw.write('#dir:'+self.datadir+'\n')
            file_raw.write('#range:'+self.range+'\n')
            file_raw.write(self.raw_data)
            file_raw.close()


#-------------------------------------------------------------------------------#
#
#  SUBPLOT - SubPlots are made of DataSets
#
#-------------------------------------------------------------------------------#
class SubPlot(HasTraits):
    """ Object that holds all the datasets that define a subplot in the figure"""
    datasets = List([ DataSet(name='Data1') ])
    name = Str
    descr = Str( '', label="Description", desc="describe the contents of the data set")
    plotme = Bool(False, label="plot me ?")
    
    grids = List([1,2,3,4])
    gridR = Enum(values ='grids')  
    gridC = Enum(values ='grids')  
    selected = Instance(DataSet)
    index = Int
    addset = Button("Add data set")
    view = View(HGroup(Item( 'plotme', show_label=False), 
                       Item('gridR',show_label=False),
                       Item('gridC',show_label=False),
                       Item('descr',show_label=False, springy=True),
                       Item('addset', show_label=False)),
                       Item('datasets', style='custom', show_label=False,
                                                         editor = ListEditor( use_notebook=True,
                                                                              selected='selected',
                                                                              deletable=True,
                                                                              dock_style='tab', 
                                                                              page_name='.name')),
               )
    def _selected_changed(self,selected):
        self.index = self.datasets.index(selected)

    def _addset_fired(self):
        new = copy.deepcopy( self.datasets[ self.index ] ) 
        new.name = 'Data%s' % (1+len(self.datasets)) 
        self.datasets.append( new )
        if len(self.datasets) > 4:
          self.grids= [ i+1 for i in range(len(self.datasets))]
        #The newly added dataset is selected
        self.selected = self.datasets[-1]

    def _setfitexprs_(self):
        for set in self.datasets:
          set._setfitexprs_()

    def _descr_changed(self):
        self.name = self.descr



#-------------------------------------------------------------------------------#
#
#  PROCESSING THREAD
#
#-------------------------------------------------------------------------------#
class ProcessThread(threading.Thread):
    """ This is the worker thread that retrieves the data from the reports, 
    makes the plots and performs the fits. 
    """
    wants_abort = False
    autoplot = False

    def run(self):
        """ Runs the plotting loop. """
        i=0
        while not self.wants_abort:
            print "autoplot is %d\n" %self.autoplot
            process( self.subplots, self.image_clear, self.figure, self.gridR, self.gridC, self.export)
            if i==0:
                self.wants_abort = not self.autoplot
            if i>0 and not self.wants_abort: 
                p0= LastAnalyzed()
                while p0 == LastAnalyzed() and not self.wants_abort:
                    time.sleep(2)
            i = i+1

    def image_clear(self):
        """ Clears canvas 
        """
        for ax in self.figure.get_axes(): 
            ax.cla()
        self.figure.clear()
        wx.CallAfter(self.figure.canvas.draw)



#-------------------------------------------------------------------------------#
#
#  RAW PROCESING FUNCTIONS, process is called by the ProcessingThread. 
#  Other functions in this section are helper functions for process. 
#
#-------------------------------------------------------------------------------#

def savefile_dialog(prompt,ext):
    style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    dialog = wx.FileDialog(None, prompt, "", "",
                               "%s files (*.%s)|*.%s" % (ext,ext,ext), wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
    if dialog.ShowModal() == wx.ID_OK:
        path = dialog.GetPath()
    else:
        path = None
    return path

def openfile_dialog(prompt,ext):
    dialog = wx.FileDialog(None, prompt, "", "",
                                       "%s files (*.%s)|*.%s" % (ext,ext,ext), wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

    if dialog.ShowModal() == wx.ID_OK:
        path = dialog.GetPath()
    else:
        path = None
    return path

def exportpy( export, lines):
    if export[0] == True:
      with open( export[1], "a") as pyscript:
        for l in lines:
          pyscript.write( l ) 
          pyscript.write('\n')

def exportdat( export, dat, stat, set): 
    if export[0] == True:
       
       datrange = set.range
       datrange = datrange.replace('-','m')
       datrange = datrange.replace(':','-')
       datrange = datrange.replace(',','_')
      
       xkey = set.X
       xkey = xkey.replace(' ','')
       xkey = xkey.replace(':','-')
       xkey = xkey.replace('/','D')

       ykey = set.Y
       ykey = ykey.replace(' ','')
       ykey = ykey.replace(':','-')
       ykey = ykey.replace('/','D')
 
       datfile = os.path.splitext(export[1])[0] + '_' + os.path.split(set.datadir)[1] + '_' + datrange + '_' + xkey + '_' + ykey
       statfile = datfile + '.stat'
       datfile = datfile + '.dat' 
       exportpy( export, [ \
          r"#Dataset : %s, %s\n" % (set.name, set.legend) ,\
          r"#data, errmsg, rawdat = qrange.qrange_eval('%s','%s', ['%s','%s'])" % (set.datadir, set.range, set.X , set.Y),\
          r"#sdata = statdat.statdat( data, 0, 1)" ])
       numpy.savetxt(datfile, dat )
       exportpy( export, [ \
          r"data = numpy.loadtxt('%s')" % datfile ])
       if stat != None:
         numpy.savetxt(statfile, stat )
         exportpy( export, [ \
            r"sdata = numpy.loadtxt('%s')" % statfile ])
       else:
         exportpy( export, [r"sdata = None"])
    return
   

def plotset( ax, set, export):
    data, sdata, msg, success = set.getdata_()
    if not success:
      if msg!=None: 
        ax.text(0,0.1,msg)
      else:
        ax.text(0,0.1,"getdata_ FAILED!!")
      return ax
   
          #r"sdata = statdat.statdat( data, 0, 1)",\
    exportdat( export, data, sdata, set)
    exportpy( export, [ \
          r"datX, datY = (data[:,0], data[:,1])",\
          r"ax.plot(datX,datY,'.',markersize=%d, mec='%s', mew=%d, marker='%s', mfc='%s', label='%s')" % \
                          (set.ms, set.c, set.me, set.m, set.mfc, set.legend) ,\
          r"if sdata != None and %d:" % set.ST,\
          r"  sdata = sdata[sdata[:,0].argsort()]",\
          r"  ax.plot( sdata[:,0], sdata[:,1], '-', color='%s')" % set.c,\
          r"  ax.fill_between( sdata[:,0], sdata[:,1] + sdata[:,2], sdata[:,1] - sdata[:,2], facecolor='%s', alpha=0.3 )" % set.c ,\
          r"  ax.fill_between( sdata[:,0], sdata[:,1] + sdata[:,3], sdata[:,1] - sdata[:,3], facecolor='%s', alpha=0.3 )" % set.c ,\
          r"  ax.fill_between( sdata[:,0], sdata[:,1] + sdata[:,4]/2., sdata[:,1] - sdata[:,4]/2., facecolor='%s', alpha=0.1 )" % set.c ,\
          "\n" ])

    datX, datY = (data[:,0], data[:,1])
    ax.plot(datX,datY,'.',markersize=set.ms, mec=set.c, mew=set.me, marker=set.m, mfc=set.mfc, label=set.legend)
    #try:
    fitX, fitY =  set.fit1.fit(data)  if set.fit1.dofit or set.fit1.doplot else (None,None)
    if fitX != None:
      ax.plot(fitX,fitY,'-', color=set.c)
    #except:
    #  print "Error in getting fit results."
    if sdata != None:
      #Sort sdata by the 0th column
      sdata = sdata[sdata[:,0].argsort()]
      #Plot
      ax.plot( sdata[:,0], sdata[:,1], '-', color=set.c)
      ax.fill_between( sdata[:,0], sdata[:,1] + sdata[:,2], sdata[:,1] - sdata[:,2], facecolor= set.c, alpha=0.3 )
      ax.fill_between( sdata[:,0], sdata[:,1] + sdata[:,3], sdata[:,1] - sdata[:,3], facecolor= set.c, alpha=0.3 )
      ax.fill_between( sdata[:,0], sdata[:,1] + sdata[:,4]/2., sdata[:,1] - sdata[:,4]/2., facecolor= set.c, alpha=0.1 )
    return ax

    
def process(subplot_array, image_clear, figure, gridR, gridC, export):
    """ Function called to do the processing """
    global colors
    image_clear()

    #Write all the preamble stuff to the py export file 
    exportpy( export, [r"import sys"])
    exportpy( export, [r"import numpy"])
    exportpy( export, [r"import matplotlib.pyplot as plt"])
    exportpy( export, [r"import matplotlib"])
    thispath =  r"sys.path.append('" +  os.path.split(os.path.realpath(__file__))[0] + r"')"
    exportpy( export, [ thispath ]) 
    #exportpy( export, [r"sys.path.append('/lab/software/apparatus3/py')"])
    exportpy( export, [r"figure = plt.figure()"])
    exportpy( export, [r"import qrange, statdat"])

    #Setup the grid for all the plots 
    nplots = 0
    nsubplots=[]
    
    mGridX = 0
    mGridY = 0
    for q,subplot in enumerate(subplot_array):
      if subplot.plotme == True:
        nplots = nplots + 1
        nsubplots = 0
        for set in subplot.datasets:
          if set.plotme == True and (not set.X2 and not set.Y2):
            nsubplots = nsubplots + 1
        if nsubplots > subplot.gridR * subplot.gridC:
          if (subplot.gridR * subplot.gridC) != 1:
            subplot.gridR = 1
            subplot.gridC = nsubplots

    if nplots > gridR * gridC:
        gridR = nplots
        gridC = 1
    

    exportpy(export,['outer_grid = matplotlib.gridspec.GridSpec( %d, %d)' % (gridR, gridC)]) 
    outer_grid = matplotlib.gridspec.GridSpec( gridR, gridC )
    

    ny2 = 0
    iy2=0

    i=0
    subplot_counter = 0
    if nplots > 0:
        for q,subplot in enumerate(subplot_array):
            if subplot.plotme == True:
                dataset_counter = 0

                exportpy(export, [\
                'inner_grid = matplotlib.gridspec.GridSpecFromSubplotSpec( %d, %d, subplot_spec= outer_grid[%d] )' % \
                              ( subplot.gridR, subplot.gridC, subplot_counter )  ] )
                inner_grid = matplotlib.gridspec.GridSpecFromSubplotSpec( subplot.gridR, subplot.gridC, subplot_spec= outer_grid[subplot_counter] )

                subplot_counter = subplot_counter + 1

                y2 = 'none'
                x2 = 'none'
                
                for s,set in enumerate(subplot.datasets):
            
                    if set.match == True:
                        set.mfc = set.c
                    if set.c == '':
                        set.c = colors[i % len(colors)]
                    if set.m == '':
                        set.m = markers[i % len(colors)]
                    
                    if set.plotme == True and set.range != '':

                        print "Adding subplot: %d.%d" % (subplot_counter, dataset_counter)

                            
                        if not set.X2 and not set.Y2:

                            #End ax2 plot if there is one
                            if x2 == 'yes' or y2 == 'yes':
                                exportpy( export,["ax1.legend(loc='best',numpoints=1, prop={'size':%d})" % legsz ])
                                exportpy( export,["figure.add_subplot(ax1)" ])
                                ax1.legend(loc='best',numpoints=1, prop={'size':legsz})
                                figure.add_subplot( ax1)

                                if x2 == 'yes': 
                                  x2='none'
                                if y2 == 'yes':
                                  exportpy( export,["ax1.legend(loc='best',numpoints=1, prop={'size':%d})" % legsz ])
                                  exportpy( export,["ax2.set_zorder(ax1.get_zorder()+1)"])
                                  exportpy( export,["ax2.patch.set_visible(False)"])

                                  ax2.legend(loc='best',numpoints=1, prop={'size':legsz})
                                  ax2.set_zorder(ax1.get_zorder()+1) # put ax2 in front of ax1
                                  ax2.patch.set_visible(False) # hide the 'canvas'
                                  y2='none'
                            
                            print "  Creating axes..."
                            exportpy( export,["ax1= matplotlib.pyplot.Subplot( figure, inner_grid[%d] )" % dataset_counter])
                            exportpy( export,["ax= ax1"])
                            ax1= matplotlib.pyplot.Subplot( figure, inner_grid[dataset_counter] ) 
                            dataset_counter = dataset_counter+1

 
                            i = i + 1
                            if set.xlabel != '':
                              ax1.set_xlabel(set.xlabel)
                            else:
                              ax1.set_xlabel(set.X,color=set.c)
                            if set.ylabel != '':
                              ax1.set_ylabel(set.ylabel)
                            else:
                              ax1.set_ylabel(set.Y,color=set.c)
    

                            print "  Plotting data..."
                            ax1 = plotset( ax1, set, export)
                                  
                                
                           
                            if not numpy.isnan(set.Xmin):
                                ax1.set_xlim(left=set.Xmin) 
                            if not numpy.isnan(set.Xmax):
                                ax1.set_xlim(right=set.Xmax) 
                            if not numpy.isnan(set.Ymin):
                                ax1.set_ylim(bottom=set.Ymin) 
                            if not numpy.isnan(set.Ymax):
                                ax1.set_ylim(top=set.Ymax)

                            if set.logscaleX:
                                ax1.set_xscale('log')
                            if set.logscaleY:
                                ax1.set_yscale('log')

                            if set.gridlines:
                                ax1.grid(True)

                            if not set.xticks:
                              ax1.xaxis.set_ticklabels([])
                            if not set.yticks:
                              ax1.yaxis.set_ticklabels([])
                            
                            if s+1 == len(subplot.datasets):
                              print "  Closing subplot ax1"
                              ax1.legend(loc='best',numpoints=1, prop={'size':legsz})
                              figure.add_subplot( ax1)
                                 
         
                            #If next plot needs this ax, leave it open
                            else:
                              nextset =  subplot.datasets[s+1]
                              if not nextset.X2 and not nextset.Y2:
                                print "  Closing subplot ax1"
                                ax1.legend(loc='best',numpoints=1, prop={'size':legsz})
                                figure.add_subplot( ax1)
        
                        if  set.X2 and not set.Y2:
                            x2='yes'
                            #xl = ax1.get_xlabel()
                            #yl = ax1.get_ylabel()
                              
                            #if xl == '':
                            #  ax1.set_xlabel(xl+', '+set.X,color=set.c)
                            #if yl == '':
                            #  ax1.set_ylabel(yl+', '+set.Y,color=set.c)

                            print "  Plotting data on x2..."
                            ax1 = plotset( ax1, set, export)
                                    
                        if not set.X2 and set.Y2:
                            if y2 =='none':
                                print "  Creating y2 axes..."
                              	ax2 = ax1.twinx()
                                exportpy( export,["ax2= ax1.twinx()"])
                                exportpy( export,["ax= ax2"])
               			y2 ='yes'
                            if set.ylabel != '': 
                              ax2.set_ylabel(set.ylabel)
                            else:
                              ax2.set_ylabel(set.Y,color=set.c)
                            if not success:
                              if msg!=None: 
                                ax2.text(0,0.1,msg)
                            else: 
                              i = i + 1
                              print "  Plotting data on y2..."
                              ax2 = plotset( ax2, set, export)
                              if fitX != None:
                                ax2.plot(fitX,fitY,'-', color=set.c)

                if x2 == 'yes' or y2 == 'yes':
                    print "  Closing subplot ax1"
                    exportpy( export,["ax1.legend(loc='best',numpoints=1, prop={'size':%d})" % legsz ])
                    exportpy( export,["figure.add_subplot(ax1)" ])
                    ax1.legend(loc='best',numpoints=1, prop={'size':legsz})
                    figure.add_subplot( ax1)
                    if y2 == 'yes':
                      exportpy( export,["ax1.legend(loc='best',numpoints=1, prop={'size':%d})" % legsz ])
                      exportpy( export,["ax2.set_zorder(ax1.get_zorder()+1)"])
                      exportpy( export,["ax2.patch.set_visible(False)"])
                      ax2.legend(loc='best',numpoints=1, prop={'size':legsz})
                      ax2.set_zorder(ax1.get_zorder()+1) # put ax2 in front of ax1
                      ax2.patch.set_visible(False) # hide the 'canvas'
   
    #if x2y2 != 'none':
    #    figure.subplots_adjust(left=0.18, right=0.82, bottom=0.1, top=0.95, wspace=0.22, hspace=0.2) 
    #else:
    #    figure.subplots_adjust(left=0.18, right=0.92, bottom=0.1, top=0.95, wspace=0.22, hspace=0.2)
 
    for a in figure.axes:
        xlim = a.get_xlim()
        extra = (xlim[1]-xlim[0])*0.1
        a.set_xlim( xlim[0]-extra, xlim[1]+extra )
        if a.get_yscale() != 'log':
          if a.yaxis.get_data_interval()[-1] > 1e3:
             a.yaxis.set_major_formatter( matplotlib.ticker.FormatStrFormatter('%.1e'))
          else:
             a.yaxis.set_major_formatter( matplotlib.ticker.FormatStrFormatter('%3g'))
        
    #figure.tight_layout()
    # figure.tight_layout()
    
    exportpy( export, [r"plt.show()"]) 
    wx.CallAfter(figure.canvas.draw)



#-------------------------------------------------------------------------------#
#
#  MAIN WINDOW
#
#-------------------------------------------------------------------------------#
class MainWindowHandler(Handler):
    ## This handler is just graciously taking care of closing 
    ## the application when it is in the middle of doing a plot or a fit
    def init(self, info):
        if load_pck: 
            info.object._pck_(action='load')
            info.object._setfitexprs_()
    
    def close(self, info, is_OK):
        if ( info.object.process_thread
            and info.object.process_thread.isAlive() ):
            info.object.process_thread.wants_abort = True
            while info.object.process_thread.isAlive():
                time.sleep(0.1)
            wx.Yield()
        print 'i am closing down'
        try:
            info.object._pck_(action='save')
        except:
            pass
        return True


class MainWindow(HasTraits):
    """ The main window. """

    

    #---- The figure that is shown on the left----#
    figure = Figure()

    #---- Objects that go on the top pane ----#
    status_string = String()

    clear = Button("clear")
    replot = Button("replot")

    savepck = Button("save pck")
    loadpck = Button("load pck")
    savetab = Button("save tab")
    loadtab = Button("load tab")

    autoplot = Bool(False, desc="autoplotting: Check box to autplot", label="auto ")
    gridR = Enum([1,2,3,4,5,6,7,8,9,10,11,12] )  
    gridC = Enum([1,2,3,4,5,6,7,8,9,10,11,12] )  
    subplots = List([ SubPlot(name='SubPlot1') ])
    selected = Instance(SubPlot)
    index = Int
    exportpy = Bool(False, label=".py?")
    
    addplot = Button("Add subplot")

    #This thread is going to take care of plotting and fitting
    #in the background
    process_thread = Instance(ProcessThread)

    #---- The view of the top pane is defined ----#
    control_group = VSplit( 
                  Group(
                  HGroup(Item('replot', show_label=False),
                         Item('exportpy',show_label=True),
                         spring, 
                         Item('gridR',show_label=False),
                         Item('gridC',show_label=False),
                         spring,
                         Item('addplot', show_label=False),
                         spring,
                         Item('savepck', show_label=False ),
                         Item('loadpck', show_label=False )),       
                  HGroup(spring,
                         Item('savetab', show_label=False ),
                         Item('loadtab', show_label=False )),    
                  Item( '_' ),  
                  VGroup(                       
                       Item( 'subplots', style='custom', show_label=False,
                                                         editor = ListEditor( use_notebook=True,
                                                                              selected='selected',
                                                                              deletable=True,
                                                                              dock_style='tab', 
                                                                              page_name='.name')),
                        ),
               ),
                  Item('status_string', show_label=False, springy=False,style='custom', resizable=True,height = 50),
               )


    
# The main view of the application is divided in two.  
    # A matplotlib plot is on the left and and the control_group is on the right
    view = View(HSplit(Item('figure', editor=MPLFigureEditor(), dock='vertical', width=0.55),
                       control_group,
                       show_labels=False,
                      ),
                title = 'PLOTGUI :: Plot and Fit',
                resizable=True,
                height=0.75, width=0.75,
                handler=MainWindowHandler(),
                buttons=NoButtons)




    #####
    # Below are the callback definitions for the MainWindow
    #####

    def _selected_changed(self,selected):
        """Whenever selection changes, the index of the selected tab is 
        stored in self.index """
        self.index = self.subplots.index(selected)

    def _addplot_fired(self):
        """A new subplot tab is added to the list."""
        new = copy.deepcopy( self.subplots[ self.index ] ) 
        new.name = 'SubPlot%s' % (1+len(self.subplots)) 
        self.subplots.append( new )
        #The newly added plot is selected
        self.selected = self.subplots[-1]    

    def _clear_fired(self):
        """Callback of the "clear" button.  This stops the plotting thread if necessary
        and then clears the plot
        """
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = True
        else: 
            time.sleep(1)
            for ax in self.figure.get_axes(): 
              ax.cla()
            if not self.autoplot:
              self.figure.clear()
            print 'canvas cleared\n'
           
    def _setfitexprs_(self):
        for subplot in self.subplots:
          subplot._setfitexprs_()

    def _autoplot_changed(self):
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = not self.autoplot

    def _replot_fired(self):
        """ Callback of the "replot" button. This starts
        the fitting thread, or kills it.
        """
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = True
        else:

            #---- The ProcessingThread is set up by giving it functions that
            #---- can alter the state of the Control Panel

            pyscript = ''
            if self.exportpy:
              pyscript =  savefile_dialog("Save .py script for current plot","py")
              if pyscript == None:
                self.exportpy = False
            export = (self.exportpy, pyscript) 
 
            self._setfitexprs_()
            self.process_thread = ProcessThread()
            self.process_thread.autoplot = self.autoplot           # Pass autoplot
            self.process_thread.export = export                    # Pass export
            self.process_thread.figure = self.figure               # Pass the figure
            self.process_thread.subplots = self.subplots
            self.process_thread.gridR = self.gridR
            self.process_thread.gridC = self.gridC
            self.process_thread.start()                            # Start the fitting thread


    #####
    # Below are general functionality functions for the MainWindow
    #####

    def update_status(self, string):
        """Adds a line to the top of the status box"""
        now = time.strftime("[%Y/%m/%d  %H:%M:%S]  ", time.gmtime())
        self.status_string = (now + string + "\n" + self.status_string)[0:1000]
        print string

    #The _pck_ function is used to load and save tabs to a pck file
    def _pck_(self,action,f=mainpck):
        if action == 'load':
            with open(f,"rb") as fpck:
                print 'Loading panel from %s' % f
                try:
                    for item in pickle.load(fpck):
                        self.subplots.append(item)
                except:
		    print 'Loading Fail!!'
                    return
        if action == 'save':
            print 'Saving panel to %s' % f
            with open(f,"w+b") as fpck:
                pickle.dump(self.subplots,fpck)

    def _savepck_changed ( self ):
        """ Handles the user clicking the 'save pck...' button. Save the pck file to desired directory
        """ 
        file_name = savefile_dialog("Save pck file","pck")
        if file_name != '':
            self._pck_('save',f=file_name)
        self.update_status( "Saved pck to %s" % path )


    def _loadpck_changed ( self ):
        """ Handles the user clicking the 'Open...' button. Load the pck file from desired directory
        """
        file_name = openfile_dialog("Load pck file","pck")
        if file_name != None:
            self._pck_('load',file_name)
        self.update_status( "Loaded pck from %s" % path )

    def _savetab_changed ( self ):
        """ Handles the user clicking the savetab button
        """
        path =  savefile_dialog("Save subplot tab","spt")
        if path != None:
           with open(path,"w+b") as fpck:
               pickle.dump(self.selected,fpck)
           self.update_status( "Saved selected tab to %s" % path )
  
    def _loadtab_changed ( self ):
        """ Handles the user clicking the loadtab button
        """
        path =  openfile_dialog("Load subplot tab","spt")
        if path != None: 
           with open(path,"rb") as fpck:
               item = pickle.load(fpck)
               self.subplots.append(item)
           self.update_status( "Loaded tab from %s" % path )
    

    

if __name__ == '__main__':
    MainWindow().configure_traits()


	
	
	
