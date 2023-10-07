#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script:
    boe_borme_downloader.py
Description:
    This script download all BOE/BORME documents from a specififed date.
Author:
    Jose Miguel Rios Rubio
Creation date:
    07/10/2023
Last modified date:
    07/10/2023
Version:
    1.0.0
'''

###############################################################################
### Script Name & Version

NAME = __file__
VERSION = "1.0.0"
DATE = "07/10/2023"

###############################################################################
### Imported modules

# Argument Parser Library
from argparse import ArgumentParser

# Logging Library
import logging

# Operating System Library
from os import path as os_path
from os import makedirs as os_makedirs

# System Signals Library
from platform import system as os_system
from signal import signal, SIGTERM, SIGINT
if os_system() != "Windows":
    from signal import SIGUSR1

# System Library
from sys import argv as sys_argv
from sys import exit as sys_exit

# Error Traceback Library
from traceback import format_exc

# Third-Party Libraries
from request3 import get as requests_get
import bs4 as bs

###############################################################################
### Constants

BOE_URL = "https://boe.es"

BOE_SUMMARY_URL = f"{BOE_URL}/diario_boe/xml.php?id=BOE-S-"
BOE_SUMMARY_EMITER = "departamento"
BOE_DOC_TYPE = "XML"
BOE_DATA_DIR = "boe"

BORME_SUMMARY_URL = f"{BOE_URL}/diario_borme/xml.php?id=BORME-S-"
BORME_SUMMARY_EMITER = "emisor"
BORME_DOC_TYPE = "PDF"
BORME_DATA_DIR = "borme"

###############################################################################
### Logger Setup

logging.basicConfig(
    #format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    format="%(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

###############################################################################
### Texts

class TEXT():

    ARG_DATE = \
        "Specify the date to download the BOE documents (in format yyyymmdd)"

    ARG_TYPE = \
        "Specify type of bulletin to request (BOE or BORME)"

    ARG_OUT_DIR = \
        "Specify output directory path to store the downloaded documents."

###############################################################################
### Auxiliary Application Functions

def is_int(element):
    '''
    Check if the string is an integer number.
    '''
    try:
        int(element)
        return True
    except ValueError:
        return False


def mkdirs(dir_path: str):
    '''
    Create all parents directories from specififed full path
    (mkdir -p $dir_path).
    '''
    try:
        if not os_path.exists(dir_path):
            os_makedirs(dir_path, 0o775)
    except Exception:
        logger.error(format_exc())
        logger.error("Can't create parents directories of %s.", dir_path)
        return False
    return True


def http_get(url):
    HTTP_RESPONSE_OK = 200
    logger.info("Downloading summary - %s", url)
    response = requests_get(url)
    if response.status_code != HTTP_RESPONSE_OK:
        logger.error(
            "Fail to get web page %s (status code %d)",
            url, response.status_code)
        return None
    return response


def http_download_file(url, dir, overwrite=True):
    '''
    Download a file from HTTP request through getting an stream of
    chunks and write to specified directory location path. If a file
    with that name already exists in the directory, it can be overwriten
    or not by the "overwrite" argument.
    '''
    STREAM_CHUNK_SIZE = 8192
    # Get file name
    file_name = url.split('/')[-1]
    if '=' in file_name:
        file_name = file_name.split('=')[-1]
    write_path = f"{dir}/{file_name}"
    # Check if file already exists
    if overwrite is False:
        if os_path.exists(write_path):
            logger.info("File download skip (already exists) - %s", write_path)
            return write_path
    try:
        # Create path driectories
        if mkdirs(dir) is False:
            logger.error("Fail to download file at directories creation")
            return None
        # HTTP Get
        with requests_get(url, allow_redirects=True, stream=True) as r:
            r.raise_for_status()
            # File write
            with open(write_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=STREAM_CHUNK_SIZE):
                    f.write(chunk)
    except Exception:
        logger.error(format_exc())
        logger.error("Fail to download file - %s", url)
        return None
    return write_path


def parse_xml(text):
    parsed = bs.BeautifulSoup(text, "lxml")
    if parsed is None:
        return None
    return parsed

###############################################################################
### Auxiliary Application Functions

def auto_int(x):
    '''Integer conversion using automatic base detection.'''
    return int(x, 0)


def parse_options():
    '''Get and parse program input arguments.'''
    arg_parser = ArgumentParser()
    arg_parser.version = VERSION
    arg_parser.add_argument("-d", "--date", help=TEXT.ARG_DATE,
                            action='store', type=str, required=True)
    arg_parser.add_argument("-t", "--type", help=TEXT.ARG_TYPE,
                            action='store', type=str, required=True)
    arg_parser.add_argument("-o", "--outdir", help=TEXT.ARG_TYPE,
                            action='store', type=str, required=True)
    arg_parser.add_argument("-v", "--version", action="version")
    args = arg_parser.parse_args()
    return vars(args)

###############################################################################
### Main Application Function

app_exit = False

def main(argc, argv):
    # Get arguments
    arg_options = parse_options()
    date = arg_options["date"]
    request_type = arg_options["type"].upper()
    data_dir = arg_options["outdir"]
    # Check date valid format
    if len(date) != 8:
        logger.error("Invalid date format")
        return 1
    if not is_int(date):
        logger.error("Invalid date format")
        return 1
    # Get year, month and day
    date_y = date[:4]
    date_m = date[4:6]
    date_d = date[6:8]
    # Set config depending on BOE or BORME request
    if request_type == "BOE":
        summary_url = BOE_SUMMARY_URL
        emiter = BOE_SUMMARY_EMITER
        doc_type = BOE_DOC_TYPE
        data_dir = f"{data_dir}/{BOE_DATA_DIR}"
        logger.info("Requesting BOE documents of %s/%s/%s",
                    date_y, date_m, date_d)
    elif request_type == "BORME":
        summary_url = BORME_SUMMARY_URL
        emiter = BORME_SUMMARY_EMITER
        doc_type = BORME_DOC_TYPE
        data_dir = f"{data_dir}/{BORME_DATA_DIR}"
        logger.info("Requesting BORME documents of %s/%s/%s",
                    date_y, date_m, date_d)
    else:
        logger.error("Invalid type (expected BOE or BORME)")
        return 1
    # Get BOE Summary Document
    summary_url = f"{summary_url}{date}"
    summary_dir = f"{data_dir}/{date_y}/{date_m}/{date_d}"
    http_download_file(summary_url, summary_dir, False)
    boe_summary_http_res = http_get(summary_url)
    if boe_summary_http_res is None:
        return 1
    boe_summary = parse_xml(boe_summary_http_res.text)
    if boe_summary is None:
        return 1
    # Get all the department documents
    num_downloaded_files = 0
    boe_departments = boe_summary.find_all(emiter)
    for department in boe_departments:
        dept_id = department["etq"]
        # Create department directory
        dept_dir = f"{summary_dir}/{dept_id}"
        if mkdirs(dept_dir) is False:
            logger.error("BOE documents skipped!")
            logger.error("%s", department)
            continue
        # Get all documents from this department
        boe_items = department.find_all("item")
        for item in boe_items:
            if doc_type == BOE_DOC_TYPE:
                doc = f"{BOE_URL}{item.urlxml.get_text()}"
            else:
                doc = f"{BOE_URL}{item.urlpdf.get_text()}"
            logger.info("Downloading file - %s - %s/", doc, dept_dir)
            if http_download_file(doc, dept_dir, False):
                num_downloaded_files = num_downloaded_files + 1
    logger.info("Num files downloaded: %d", num_downloaded_files)
    logger.info("Operation completed")
    return 0

###############################################################################
### System Termination Signals Management

def system_termination_signal_handler(signal,  frame):
    '''Termination signals detection handler. It stop application execution.'''
    global app_exit
    app_exit = True


def system_termination_signal_setup():
    '''
    Attachment of System termination signals (SIGINT, SIGTERM, SIGUSR1) to
    function handler.
    '''
    # SIGTERM (kill pid) to signal_handler
    signal(SIGTERM, system_termination_signal_handler)
    # SIGINT (Ctrl+C) to signal_handler
    signal(SIGINT, system_termination_signal_handler)
    # SIGUSR1 (self-send) to signal_handler
    if os_system() != "Windows":
        signal(SIGUSR1, system_termination_signal_handler)

###############################################################################
### Runnable Main Script Detection

if __name__ == '__main__':
    logger.info("{} v{} {}\n".format(os_path.basename(NAME), VERSION, DATE))
    system_termination_signal_setup()
    return_code = main(len(sys_argv) - 1, sys_argv[1:])
    sys_exit(return_code)
