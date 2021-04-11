""" Simple implementation of a pincer strategy """
import argparse
from os import environ

# spread to pass an order to be a maker
TICK = environ.get('BTCBOT_TICK', 500)


def main():
    """ Entry point to the script """
    parser = argparse.ArgumentParser(description='Start the execution of the trading with the Bot')
