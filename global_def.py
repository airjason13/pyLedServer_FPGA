from version import *
import utils.log_utils
log = utils.log_utils.logging_init(__file__)

'''List of Page Selector Button Name '''
Page_Select_Btn_Name_List = ["FPGA_List", "Media_Files", "HDMI_In", "Led_Settings", "Test"]


Version = (
    "{}{}{}_{}{}{}".format(Version_Year, Version_Month, Version_Date,
                           Version_Major, Version_Minor, Version_Patch))

