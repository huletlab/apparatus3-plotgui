
import os
import glob
# Check the OS and give correct path dependency
#if os.name == "posix":
    #Change this to the mount point for atomcool/lab. When using Linuax.
#    atomcool_lab_path = os.environ['HOME']+'/atomcool_lab/'
#    atomcool_lab_path = '/lab/'
#else:
    #Change this to the map drive for atomcool/lab. When using Windows.
#    atomcool_lab_path = 'L:/'


from enthought.traits.api import HasTraits, Str, List, Enum, Bool
from enthought.traits.ui.api import View, Item
from enthought.traits.ui.menu import OKButton, CancelButton

import os

class PlotguiConf(HasTraits):
  confpath =  os.path.realpath(__file__)
  confpath =  os.path.split(confpath)[0]
  plotguipath = confpath
  confpath =  confpath = os.path.join( confpath, "conf/" )
  plotconf_values=List(glob.glob( confpath + "plotconf*INI"))

  
  plotconf = Enum(values='plotconf_values')
  load_pck = Bool()
  use_date = Bool() 

  view = View(  Item(name='plotconf') , 
                Item(name='load_pck'),
                Item(name='use_date'), 
                resizable=True, width=600, height=200, 
                title='PLOTGUI :: Configuration',\
                buttons = [OKButton, CancelButton])

def initplotgui():
  conf = PlotguiConf()
  out = conf.configure_traits()
  if out == True: 
     plotguipath =  os.path.split(conf.confpath)[0]
     mainpck =   conf.plotconf.split('.')[0] + '.pck'
     return conf.plotconf, conf.plotguipath, mainpck, conf.load_pck, conf.use_date
  else:
     print "program will be stopped."
     exit(1)
  
  

if __name__ == '__main__':
  print initplotgui()
        

