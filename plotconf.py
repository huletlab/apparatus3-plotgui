
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


from enthought.traits.api import HasTraits, Str, List, Enum
from enthought.traits.ui.api import View, Item
from enthought.traits.ui.menu import OKButton, CancelButton

class PlotguiConf(HasTraits):
  path =  os.path.realpath(__file__)
  path =  path.rsplit('/',1)[0]
  plotconf_values=List(glob.glob( path + "/plotconf*INI"))

  
  plotconf = Enum(values='plotconf_values')

  view = View(  Item(name='plotconf') , resizable=True, width=600, height=200, title='PLOTGUI :: Configuration',\
                buttons = [OKButton, CancelButton])

def initplotgui():
  conf = PlotguiConf()
  out = conf.configure_traits()
  if out == True: 
     return conf.plotconf, conf.path
  else:
     print "program will be stopped."
     exit(1)
  
  

if __name__ == '__main__':
  print initplotgui()
        

