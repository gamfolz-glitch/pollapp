# polls/views/__init__.py
from .public import *
from .dashboard import *
from .questions import *
from .choices import *
from .analytics import *
from .live import *
from .auth import *

# Специально для AJAX вьюхи
from .choices import choice_new, choice_edit, choice_delete
from .analytics import project_stats, project_responses
from .live import live_vote_count
from .auth import signup