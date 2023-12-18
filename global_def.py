from version import *

import utils.log_utils

log = utils.log_utils.logging_init(__file__)
from ui.ui_fpga_list_page import FpgaListPage
from ui.ui_media_files_page import MediaFilesPage
from ui.ui_hdmi_in_page import HDMIInPage
from ui.ui_led_settings_page import LedSettingsPage
from ui.ui_test_page import TestPage

'''List of Page Selector Button Name '''
Page_Select_Btn_Name_List = ["FPGA_List", "Media_Files", "HDMI_In", "Led_Settings", "Test"]
Page_List = [FpgaListPage, MediaFilesPage, HDMIInPage, LedSettingsPage, TestPage]

Page_Map = dict(zip(Page_Select_Btn_Name_List, Page_List))

Version = (
    "{}{}{}_{}{}{}".format(Version_Year, Version_Month, Version_Date,
                           Version_Major, Version_Minor, Version_Patch))
