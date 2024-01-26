import os
import sys
from version import *

import utils.log_utils

log = utils.log_utils.logging_init(__file__)

root_dir = os.path.dirname(sys.modules['__main__'].__file__)

Version = (
    "{}{}{}_{}{}{}".format(Version_Year, Version_Month, Version_Date,
                           Version_Major, Version_Minor, Version_Patch))

