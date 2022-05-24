# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from markupsafe import Markup

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.safe_eval import safe_eval, time
from odoo.tools.misc import find_in_path
from odoo.tools import config, is_html_empty
from odoo.sql_db import TestCursor
from odoo.http import request
from odoo.osv.expression import NEGATIVE_TERM_OPERATORS, FALSE_DOMAIN

import base64
import io
import logging
import os
import lxml.html
import tempfile
import subprocess
import re
import json

from lxml import etree
from contextlib import closing
from distutils.version import LooseVersion
from reportlab.graphics.barcode import createBarcodeDrawing
from PyPDF2 import PdfFileWriter, PdfFileReader, utils
from collections import OrderedDict
from collections.abc import Iterable
from PIL import Image, ImageFile
# Allow truncated images

import csv, os, json

ImageFile.LOAD_TRUNCATED_IMAGES = True


_logger = logging.getLogger(__name__)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'
    
    def _prepare_html(self, html):
        
    #     file = 'data/html.csv'
    #     with open(file, 'a') as file:
    #         writer = csv.writer(file)
    #         writer.writerow(html)
        
        _logger.info(html)
        
        return super()._prepare_html(html)