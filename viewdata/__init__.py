from .viewdata_core import set_default_curve_date
from .viewdata_core import Curve, Subplot, PlotData
from .viewdata_core import help_table, Curve_setup_dict_type_default, Subplot_setup_dict_type_default
from .viewdata_GUI import run_GUI

def use_ggplot():
    from .viewdata_core import plt
    plt.style.use("ggplot")

if __name__ == "__main__":
    run_GUI()