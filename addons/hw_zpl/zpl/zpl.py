# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six
from abc import ABCMeta, abstractmethod


@six.add_metaclass(ABCMeta)
class Zpl:
    """ ZPL Printer object

    This class is the abstract base class for an esc/pos-printer. The printer implementations are children of this
    class.
    """

    pass
