#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Torrent Factory V1.0.1 - Moteur Réel Intégré
"""

import os
import sys
import subprocess
import platform
import string
import json
import re
import time
import threading
import uuid
import logging
import random
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify, send_from_directory

# ... (reste du code identique)