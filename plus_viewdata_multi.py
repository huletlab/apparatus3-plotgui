from threading import Thread
from time import sleep
from traits.api import *
from traitsui.api import View, Item, Group, HGroup, VGroup, HSplit, VSplit,Handler, CheckListEditor, EnumEditor, ListStrEditor,ArrayEditor, spring, ListEditor, CodeEditor, TextEditor
from traitsui.menu import NoButtons
from traitsui.file_dialog import save_file,open_file
from chaco.api import Plot, ArrayPlotData
from enable.component_editor import ComponentEditor
from chaco.chaco_plot_editor import ChacoPlotItem
from mpl_figure_editor import MPLFigureEditor
from matplotlib.figure import Figure
from scipy import stats 
from numpy import loadtxt, linspace, sin
import wx
from random import choice
from configobj import ConfigObj

import qrange

import numpy
import matplotlib
import copy
import pickle
from configobj import ConfigObj

from fitlibrary import Fits

global colors 
colors = ['#0D8800','#1729E0','#00A779','#D8005F','green','red','magenta','black']
markers = ['.', 's', 'x', 'D', '+', '*', 'o', '2', '1']
default_ms = 10.
default_me = 1.


#-------------------------------------------------------------------------------#
#
#  HELPER FUNCTIONS
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
def LastAnalyzed():
    LASTNUM = conf['DIRECTORIES']['lastnum']
    path_is_relative = LASTNUM[0] != '/' and not ':' in LASTNUM  #works for Win and Linux
    if path_is_relative:
      LASTNUM = plotgui_path + '/' + LASTNUM
    file = open( LASTNUM,'r')
    lastnum = int( file.readline() )
    file.close()
    return lastnum

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
    loadscan = Button('Load Scan')
  
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
                                   Item('logscaleX'), 
                                   Item('logscaleY'), 
                                   Item('gridlines'),
                                   Item('xticks'),
                                   Item('yticks'),
),
                           HGroup(
                            Item('name',springy=True)),
                           HGroup(Item('descr_label', style='readonly', show_label=False),
                                  Item('descr', show_label=False, springy=True), springy=False),
                           HGroup(
                                  Item('xlabel', show_label=True, springy=True), 
                                  Item('ylabel', show_label=True, springy=True), 
                                  Item('legend', show_label=True, springy=False), 
                                  springy=False ),
 
                           orientation ='vertical', show_border = True,
                          ),
                Group(
                      VGroup( Item('datadir'),
                      Item('range'), ),
                      HGroup( Item('X',springy=True,show_label=True), Item('Xmin',show_label=False), Item('Xmax',show_label=False)), 
                      HGroup( Item('Y',springy=True,show_label=True), Item('Ymin',show_label=False), Item('Ymax',show_label=False)), 
                      show_border = True,
                     ),
                Group(
                      Group( Item('c'),  Item('mfc'), Item('match'), Item('m',width=-30), Item('ms',width=-40), Item('me',width=-40), orientation='horizontal'),
                      show_border = True),
                Group(
                      Item('fit1', style='custom', show_label=False),
                      show_border = True
                     ) ,label='Set', scrollable=True   ),
                            
                    Group(     Item (
                                    'raw_data',show_label=False, springy=True, style='custom' 
                                   ),
                               Item('saveraw',show_label=False),label='Raw Data'),
                    Group(     Item (
                                    'stat',show_label=False, springy=True, style='custom' 
                                   ),
                               label='Stats')
                                   ,dock='tab',  scrollable= True,
              )

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

        sdata=None
        #Obtain statistics from data
        # stats = (mean, standard deviation, pk-pk, standard error of the mean) 
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
 
#    def _name_changed(self):
#        if '_' in self.name: 
#          self.name = self.descr.split('_')[0]
#        else: 
#          self.name = self.descr[:4]

    def saverawfile(self,file_name):
        if file_name != '':
            file_raw=open(file_name,"w+b")
            file_raw.write('#dir:'+self.datadir+'\n')
            file_raw.write('#range:'+self.range+'\n')
            file_raw.write(self.raw_data)
            file_raw.close()
	
    def _saveraw_changed(self):
        """ Save raw data to choosen location"""
      
        file_name = save_file()
    	self.saverawfile(file_name)

    def _loadscan_changed ( self ):
        """ Handles the user clicking the 'Loadscan...' button. Load the sweep config file
        """
        INFO = conf['DIRECTORIES']['infofile']
        infofile = open(INFO,'r')
        self.datadir =  infofile.readline()
        self.range = infofile.readline()
        self.X = infofile.readline()
        self.Y = infofile.readline()

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
    view = View(       HGroup(Item( 'plotme', show_label=False), 
                         Item('gridR',show_label=False),
                         Item('gridC',show_label=False),
                       Item('descr',show_label=False, springy=True),
                       Item('addset', show_label=False)),
                       Item( 'datasets', style='custom', show_label=False,
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

class ProcessThread(Thread):
    """ Fitting loop. This is the worker thread that retrieves the 
    data from the reports, and performs the fits. 
    """
    wants_abort = False
    autoplot = False

    def process(self, dataset_array, image_clear, figure, gridR, gridC):
        """ Spawns the processing job. """
        try:
            if self.processing_job.isAlive():
                print "Processing too slow" + '\n'
                return
        except AttributeError:
            pass
	print "Starting a thread!\n"
        self.processing_job = Thread(target=process, args=(dataset_array, image_clear, figure, gridR, gridC, self.export))
        self.processing_job.start()

    def run(self):
        """ Runs the plotting loop. """
        i=0
        while not self.wants_abort:
            print "autoplot is %d\n" %self.autoplot
            self.process(self.subplots, self.image_clear, self.figure, self.gridR, self.gridC)
            if i==0:
                self.wants_abort = not self.autoplot
            if i>0 and not self.wants_abort: 
                p0= LastAnalyzed()
                while p0 == LastAnalyzed() and not self.wants_abort:
                    sleep(2)
            i = i+1

    def image_clear(self):
        """ Clears canvas 
        """
        for ax in self.figure.get_axes(): 
            ax.cla()
        self.figure.clear()
        
        wx.CallAfter(self.figure.canvas.draw)

def plotset( ax, set, export):
    data, sdata, msg, success = set.getdata_()
    if not success:
      if msg!=None: 
        ax.text(0,0.1,msg)
      else:
        ax.text(0,0.1,"getdata_ FAILED!!")
      return ax

    if export[0] == True:
      with open( export[1], "a") as pyscript:
          pyscript.write('#Dataset : %s, %s\n' % (set.name, set.legend))
          pyscript.write(r'data, errmsg, rawdat = qrange.qrange_eval("%s","%s", ["%s","%s"])' % (set.datadir, set.range, set.X , set.Y) )
          pyscript.write("\n")
          pyscript.write(r'sdata = statdat.statdat( data, 0, 1)')
          pyscript.write("\n\n\n")


    datX, datY = (data[:,0], data[:,1])
    ax.plot(datX,datY,'.',markersize=set.ms, mec=set.c, mew=set.me, marker=set.m, mfc=set.mfc, label=set.legend)
    try:
      fitX, fitY =  set.fit1.fit(data)  if set.fit1.dofit or set.fit1.doplot else (None,None)
      if fitX != None:
        ax.plot(fitX,fitY,'-', color=set.c)
    except:
      print "Error in getting fit results."
    if sdata != None:
      #Sort sdata by the 0th column
      sdata = sdata[sdata[:,0].argsort()]
      #Plot
      ax.plot( sdata[:,0], sdata[:,1], '-', color=set.c)
      ax.fill_between( sdata[:,0], sdata[:,1] + sdata[:,2], sdata[:,1] - sdata[:,2], facecolor= set.c, alpha=0.3 )
      ax.fill_between( sdata[:,0], sdata[:,1] + sdata[:,3], sdata[:,1] - sdata[:,3], facecolor= set.c, alpha=0.3 )
      ax.fill_between( sdata[:,0], sdata[:,1] + sdata[:,4]/2., sdata[:,1] - sdata[:,4]/2., facecolor= set.c, alpha=0.1 )
    return ax

legsz = 8.
    
def process(subplot_array, image_clear, figure, gridR, gridC, export):
    """ Function called to do the processing """
    global colors
    image_clear()


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
    

            
    outer_grid = matplotlib.gridspec.GridSpec( gridR, gridC )
    

    ny2 = 0
    iy2=0

    i=0
    subplot_counter = 0
    if nplots > 0:
        for q,subplot in enumerate(subplot_array):
            if subplot.plotme == True:
                dataset_counter = 0
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
                                ax1.legend(loc='best',numpoints=1, prop={'size':legsz})
                                figure.add_subplot( ax1)
                                if x2 == 'yes': 
                                  x2='none'
                                if y2 == 'yes':
                                  ax2.legend(loc='best',numpoints=1, prop={'size':legsz})
                                  ax2.set_zorder(ax1.get_zorder()+1) # put ax2 in front of ax1
                                  ax2.patch.set_visible(False) # hide the 'canvas'
                                  y2='none'
                            
                            print "  Creating axes..."
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
                                  
                            if not set.xticks:
                              ax1.xaxis.set_ticklabels([])
                            if not set.yticks:
                              ax1.yaxis.set_ticklabels([])
                                
                           
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
                    ax1.legend(loc='best',numpoints=1, prop={'size':legsz})
                    figure.add_subplot( ax1)
                    if y2 == 'yes':
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
                sleep(0.1)
            wx.Yield()
        print 'i am closing down'
        try:
            info.object._pck_(action='save')
        except:
            pass
        return True



class MainWindow(HasTraits):
    """ The main window. """
    def _pck_(self,action,f=mainpck):
        if action == 'load':
            try:
                fpck=open(f,"rb")
                print 'Loading panel from %s' % f
		for item in pickle.load(fpck):
                	self.subplots.append(item)
            except :
		print 'Loading Fail!!'
                return
        if action == 'save':
            print 'Saving panel to %s' % f
            fpck=open(f,"w+b")
            pickle.dump(self.subplots,fpck)
        fpck.close()
    

    #---- The figure that is shown on the left----#
    figure = Figure()

    #---- Objects that go in the CONTROL tab ----#
    clear = Button("clear")
    replot = Button("replot")
    savepck = Button("save pck")
    loadpck = Button("load pck")
    loadscan = Button("load scan")
    autoplot = Bool(False, desc="autoplotting: Check box to autplot", label="auto ")
    gridR = Enum([1,2,3,4] )  
    gridC = Enum([1,2,3,4] )  
    subplots = List([ SubPlot(name='SubPlot1') ])
    selected = Instance(SubPlot)
    index = Int
    savefigure = Button("Save Current Figure")
    exportpy = Bool(False, label=".py?")
    
    addplot = Button("Add subplot")
    results_string = String()
    process_thread = Instance(ProcessThread)

    #---- Objects that go in the REPORT tab ----#
    repshot = Int(label='report shotnum')
    getreport = Button('get report')
    report =  String()

    #---- The view of the right pane is defined ----#
    control_group = Group(  
                  HGroup(Item('replot', show_label=False),
                         Item('exportpy',show_label=True),
                         #Item('clear', show_label=False ),
                         #Item('autoplot', show_label=True ),
                         spring, 
                         Item('gridR',show_label=False),
                         Item('gridC',show_label=False),
                         spring,
                         Item('addplot', show_label=False),
                         spring,
                         Item('savepck', show_label=False ),
                         Item('loadpck', show_label=False )),           
                  Item( '_' ),  
                  VGroup(                       
                       Item( 'subplots', style='custom', show_label=False,
                                                         editor = ListEditor( use_notebook=True,
                                                                              selected='selected',
                                                                              deletable=True,
                                                                              dock_style='tab', 
                                                                              page_name='.name')),
                       Item('savefigure', show_label=False),
                        ),
               )


    # The main view of the application is divided in two.  
    # A matplotlib plot is on the left and and the control_group is on the right
    view = View(HSplit(Item('figure', editor=MPLFigureEditor(), dock='vertical'),
                       control_group,
                       show_labels=False,
                      ),
                title = 'PLOTGUI :: Plot and Fit',
                resizable=True,
                height=0.75, width=0.5,
                handler=MainWindowHandler(),
                buttons=NoButtons)

    # Below are the callback definitions
    def _selected_changed(self,selected):
        self.index = self.subplots.index(selected)

    def _addplot_fired(self):
        new = copy.deepcopy( self.subplots[ self.index ] ) 
        new.name = 'SubPlot%s' % (1+len(self.subplots)) 
        self.subplots.append( new )
    
    def _savefigure_fired(self):
	
	filename = ""
	rawfile =[]
	ds = []
        for j,subplot in enumerate(self.subplots):
	  	for i,dataset in enumerate(subplot.datasets):
			if(dataset.plotme): 
				folder = dataset.datadir+"plots/" # Use the folder of the last dataset
				ds.append(dataset)

		for dataset in ds:
			fn = dataset.descr + "_" if dataset.descr else ""
			fn = fn+ dataset.X.replace(":","_")
			fn = fn+ "_"+ dataset.Y.replace(":","_")
			fn = fn+ "_"+ dataset.range.replace(":","_").replace(",","_").replace("-","m")
			if not os.path.exists(folder):os.makedirs(folder)
			dataset.saverawfile(os.path.join(folder,fn+".dat"))
			if(filename!=""): filename = filename +"_AND_"
			filename = filename + fn 

	filename = os.path.join(folder,filename+".png")
	self.figure.savefig(filename)


    def _clear_fired(self):
        """Callback of the "clear" button.  This stops the fitting thread if necessary
        and then clears the plot
        """
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = True
        else: 
            sleep(1)
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
              pyscript = save_file()
              if pyscript == '':
                self.exportpy = False
 
            self._setfitexprs_()
            self.process_thread = ProcessThread()
            self.process_thread.autoplot = self.autoplot           # Pass autoplot
            self.process_thread.export = (self.exportpy,pyscript)  # Pass exportpy bool and the output file as a tuple
            self.process_thread.figure = self.figure               # Pass the figure
            self.process_thread.subplots = self.subplots
            self.process_thread.gridR = self.gridR
            self.process_thread.gridC = self.gridC
            self.process_thread.start()                            # Start the fitting thread


    def _savepck_changed ( self ):
        """ Handles the user clicking the 'save pck...' button. Save the pck file to desired directory
        """ 
        file_name = save_file()
        if file_name != '':
            self._pck_('save',f=file_name)



    def _loadpck_changed ( self ):
        """ Handles the user clicking the 'Open...' button. Load the pck file from desired directory
        """
        file_name = open_file()
        if file_name != '':
            self._pck_('load',file_name)
    

if __name__ == '__main__':
    MainWindow().configure_traits()


	
	
	
