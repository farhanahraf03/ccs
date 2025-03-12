"""
Farhan Ansari
"""

import socket 
import time

# handles the termination of connection endpts and sessions
def connectionRequestClose():
    global sent, retrans, packets_successfully_sent


# Define a function named try_connect without any parameters
def connectionRequestStart():
    global isConnected

    isConnected = False 

    # Infinite loop that waits for connection
    try:
        while (isConnected is False):
            # Reconnect
            connect()
            # If unable to connect then pause for a sec
            time.sleep(1)
            continue

    # Handle exception by calling the closeUp() and reconnect
    except:
        connectionRequestClose()
        connectionRequestStart()


if __name__ == '__main__':
   connectionRequestStart()
