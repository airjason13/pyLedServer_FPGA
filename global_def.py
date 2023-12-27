import os

from version import *

import utils.log_utils

log = utils.log_utils.logging_init(__file__)


Version = (
    "{}{}{}_{}{}{}".format(Version_Year, Version_Month, Version_Date,
                           Version_Major, Version_Minor, Version_Patch))

