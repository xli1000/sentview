import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from sentview.tweet import models
from sentview.shared import Base,engine

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


Base.metadata.create_all(engine)
