import logging

__author__ = 'gkralik'

import argparse


def configure_logging(logger=None, config=None):
    #if config is None:
        #return

    if logger is None:
        logger = logging.getLogger()

    # TODO configure
    logging.basicConfig(filename='dbgpproxy.log', level=logging.INFO)


def parse_arguments():
    parser = argparse.ArgumentParser()