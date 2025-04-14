# -*-coding:utf-8 -*-
'''
@Time    :   2024/06/26 18:30:20
@Author  :   Daniel Persaud
@Version :   1.0
@Contact :   da.persaud@mail.utoronto.ca
@Desc    :   this is a run script for running automated corrosion tests
'''

#%%
# IMPORT DEPENDENCIES------------------------------------------------------------------------------
import json
import os
import logging
from datetime import datetime
from re import I
import sys
import time

from opentrons import opentronsClient

from OT_Arduino_Client_matt import *

from biologic import connect, BANDWIDTH, I_RANGE, E_RANGE
from biologic.techniques.ocv import OCVTechnique, OCVParams, OCVData
from biologic.techniques.peis import PEISTechnique, PEISParams, SweepMode, PEISData
from biologic.techniques.ca import CATechnique, CAParams, CAStep, CAData
from biologic.techniques.cpp import CPPTechnique, CPPParams, CPPData
from biologic.techniques.pzir import PZIRTechnique, PZIRParams, PZIRData
from biologic.techniques.cv import CVTechnique, CVParams, CVStep, CVData
from biologic.techniques.lp import LPTechnique, LPParams, LPStep, LPData
from biologic.techniques.cp import CPTechnique, CPParams, CPStep, CPData

import pandas as pd

# HELPER FUNCTIONS---------------------------------------------------------------------------------

# define helper functions to manage solution
def fillWell(
    opentronsClient,
    strLabwareName_from,
    strWellName_from,
    strOffsetStart_from,
    strPipetteName,
    strLabwareName_to,
    strWellName_to,
    strOffsetStart_to,
    intVolume: int,
    fltOffsetX_from: float = 0,
    fltOffsetY_from: float = 0,
    fltOffsetZ_from: float = 0,
    fltOffsetX_to: float = 0,
    fltOffsetY_to: float = 0,
    fltOffsetZ_to: float = 0,
    intMoveSpeed : int = 100
) -> None:
    '''
    function to manage solution in a well because the maximum volume the opentrons can move is 1000 uL
    
    Parameters
    ----------
    opentronsClient : opentronsClient
        instance of the opentronsClient class

    strLabwareName_from : str
        name of the labware to aspirate from

    strWellName_from : str
        name of the well to aspirate from

    strOffset_from : str
        offset to aspirate from
        options: 'bottom', 'center', 'top'

    strPipetteName : str
        name of the pipette to use

    strLabwareName_to : str
        name of the labware to dispense to

    strWellName_to : str
        name of the well to dispense to

    strOffset_to : str
        offset to dispense to
        options: 'bottom', 'center', 'top'  

    intVolume : int
        volume to transfer in uL    

    intMoveSpeed : int
        speed to move in mm/s
        default: 100
    '''
    
    # while the volume is greater than 1000 uL
    while intVolume > 1000:
        # move to the well to aspirate from
        opentronsClient.moveToWell(strLabwareName = strLabwareName_from,
                                   strWellName = strWellName_from,
                                   strPipetteName = strPipetteName,
                                   strOffsetStart = 'top',
                                   fltOffsetX = fltOffsetX_from,
                                   fltOffsetY = fltOffsetY_from,
                                   intSpeed = intMoveSpeed)
        
        # aspirate 1000 uL
        opentronsClient.aspirate(strLabwareName = strLabwareName_from,
                                 strWellName = strWellName_from,
                                 strPipetteName = strPipetteName,
                                 intVolume = 1000,
                                 strOffsetStart = strOffsetStart_from,
                                 fltOffsetX = fltOffsetX_from,
                                 fltOffsetY = fltOffsetY_from,
                                 fltOffsetZ = fltOffsetZ_from)
        
        # move to the well to dispense to
        opentronsClient.moveToWell(strLabwareName = strLabwareName_to,
                                   strWellName = strWellName_to,
                                   strPipetteName = strPipetteName,
                                   strOffsetStart = 'top',
                                   fltOffsetX = fltOffsetX_to,
                                   fltOffsetY = fltOffsetY_to,
                                   intSpeed = intMoveSpeed)
        
        # dispense 1000 uL
        opentronsClient.dispense(strLabwareName = strLabwareName_to,
                                 strWellName = strWellName_to,
                                 strPipetteName = strPipetteName,
                                 intVolume = 1000,
                                 strOffsetStart = strOffsetStart_to,
                                 fltOffsetX = fltOffsetX_to,
                                 fltOffsetY = fltOffsetY_to,
                                 fltOffsetZ = fltOffsetZ_to)
        opentronsClient.blowout(strLabwareName = strLabwareName_to,
                                strWellName = strWellName_to,
                                strPipetteName = strPipetteName,
                                strOffsetStart = strOffsetStart_to,
                                fltOffsetX = fltOffsetX_to,
                                fltOffsetY = fltOffsetY_to,
                                fltOffsetZ = fltOffsetZ_to)
        
        # subtract 1000 uL from the volume
        intVolume -= 1000


    # move to the well to aspirate from
    opentronsClient.moveToWell(strLabwareName = strLabwareName_from,
                               strWellName = strWellName_from,
                               strPipetteName = strPipetteName,
                               strOffsetStart = 'top',
                               fltOffsetX = fltOffsetX_from,
                               fltOffsetY = fltOffsetY_from,
                               intSpeed = intMoveSpeed)
    
    # aspirate the remaining volume
    opentronsClient.aspirate(strLabwareName = strLabwareName_from,
                             strWellName = strWellName_from,
                             strPipetteName = strPipetteName,
                             intVolume = intVolume,
                             strOffsetStart = strOffsetStart_from,
                             fltOffsetX = fltOffsetX_from,
                             fltOffsetY = fltOffsetY_from,
                             fltOffsetZ = fltOffsetZ_from)
    
    # move to the well to dispense to
    opentronsClient.moveToWell(strLabwareName = strLabwareName_to,
                               strWellName = strWellName_to,
                               strPipetteName = strPipetteName,
                               strOffsetStart = 'top',
                               fltOffsetX = fltOffsetX_to,
                               fltOffsetY = fltOffsetY_to,
                               intSpeed = intMoveSpeed)
    
    # dispense the remaining volume
    opentronsClient.dispense(strLabwareName = strLabwareName_to,
                             strWellName = strWellName_to,
                             strPipetteName = strPipetteName,
                             intVolume = intVolume,
                             strOffsetStart = strOffsetStart_to,
                             fltOffsetX = fltOffsetX_to,
                             fltOffsetY = fltOffsetY_to,
                             fltOffsetZ = fltOffsetZ_to)
    
    # blowout
    opentronsClient.blowout(strLabwareName = strLabwareName_to,
                            strWellName = strWellName_to,
                            strPipetteName = strPipetteName,
                            strOffsetStart = strOffsetStart_to,
                            fltOffsetX = fltOffsetX_to,
                            fltOffsetY = fltOffsetY_to,
                            fltOffsetZ = fltOffsetZ_to)
    
    return

nozzle = {
    'water':1,
    'acid':0,
    'out':2,
    }

rinse = {
    'water':3,
    'acid':5,
    'out':4,
    }

# define helper function to wash electrode
def washElectrode(opentronsClient,
                  strLabwareName,
                  arduinoClient):
    '''
    function to wash electrode

    Parameters
    ----------
    opentronsClient : opentronsClient
        instance of the opentronsClient class

    strLabwareName : str
        name of the labware to wash electrode in

    intCycle : int
        number of cycles to wash electrode

    '''

    # fill wash station with Di water
    arduinoClient.dispense_ml(pumpNumber=rinse['water'], volume=15)

    # move to wash station
    opentronsClient.moveToWell(strLabwareName = strLabwareName,
                               strWellName = 'A2',
                               strPipetteName = 'p1000_single_gen2',
                               strOffsetStart = 'top',
                               intSpeed = 50)

    # move to wash station
    opentronsClient.moveToWell(strLabwareName = strLabwareName,
                               strWellName = 'A2',
                               strPipetteName = 'p1000_single_gen2',
                               strOffsetStart = 'bottom',
                               fltOffsetY = -15,
                               fltOffsetZ = -10,
                               intSpeed = 50)
    
    # arduinoClient.setUltrasonicOnTimer(0, 30000);

    # drain wash station
    arduinoClient.dispense_ml(pumpNumber=rinse['out'], volume=16)

    # fill wash station with acid
    arduinoClient.dispense_ml(pumpNumber=rinse['acid'], volume=10)

    # move to wash station
    arduinoClient.setUltrasonicOnTimer(0, 30000);

    # drain wash station
    arduinoClient.dispense_ml(pumpNumber=rinse['out'], volume=11)

    # fill wash station with Di water
    arduinoClient.dispense_ml(pumpNumber=rinse['water'], volume=15)


    arduinoClient.setUltrasonicOnTimer(0, 30000);

    # drain wash station
    arduinoClient.dispense_ml(pumpNumber=rinse['out'], volume=16)

    return

def rinseElectrode(
    opentronsClient,
    strLabwareName,
    arduinoClient
):
    '''
    function to wash electrode

    Parameters
    ----------
    opentronsClient : opentronsClient
        instance of the opentronsClient class

    strLabwareName : str
        name of the labware to wash electrode in

    intCycle : int
        number of cycles to wash electrode

    '''

    # fill wash station with Di water
    arduinoClient.dispense_ml(pumpNumber=rinse['water'], volume=30)

    # move to wash station
    opentronsClient.moveToWell(strLabwareName = strLabwareName,
                               strWellName = 'A2',
                               strPipetteName = 'p1000_single_gen2',
                               strOffsetStart = 'top',
                               intSpeed = 50)

    # move to wash station
    opentronsClient.moveToWell(strLabwareName = strLabwareName,
                               strWellName = 'A2',
                               strPipetteName = 'p1000_single_gen2',
                               strOffsetStart = 'bottom',
                               fltOffsetY = -15,
                               fltOffsetZ = -10,
                               intSpeed = 50)
    
    arduinoClient.setUltrasonicOnTimer(0, 30000);

    # drain wash station
    arduinoClient.dispense_ml(pumpNumber=rinse['out'], volume=31)


    return

# make a dictionary to warp numbers to pipette names
dicNumToPipetteTipLoc = {
    1: 'A1', 2: 'A2', 3: 'A3', 4: 'A4', 5: 'A5', 6: 'A6', 7: 'A7', 8: 'A8', 9: 'A9', 10: 'A10', 11: 'A11', 12: 'A12',
    13: 'B1', 14: 'B2', 15: 'B3', 16: 'B4', 17: 'B5', 18: 'B6', 19: 'B7', 20: 'B8', 21: 'B9', 22: 'B10', 23: 'B11', 24: 'B12',
    25: 'C1', 26: 'C2', 27: 'C3', 28: 'C4', 29: 'C5', 30: 'C6', 31: 'C7', 32: 'C8', 33: 'C9', 34: 'C10', 35: 'C11', 36: 'C12',
    37: 'D1', 38: 'D2', 39: 'D3', 40: 'D4', 41: 'D5', 42: 'D6', 43: 'D7', 44: 'D8', 45: 'D9', 46: 'D10', 47: 'D11', 48: 'D12',
    49: 'E1', 50: 'E2', 51: 'E3', 52: 'E4', 53: 'E5', 54: 'E6', 55: 'E7', 56: 'E8', 57: 'E9', 58: 'E10', 59: 'E11', 60: 'E12',
    61: 'F1', 62: 'F2', 63: 'F3', 64: 'F4', 65: 'F5', 66: 'F6', 67: 'F7', 68: 'F8', 69: 'F9', 70: 'F10', 71: 'F11', 72: 'F12',
    73: 'G1', 74: 'G2', 75: 'G3', 76: 'G4', 77: 'G5', 78: 'G6', 79: 'G7', 80: 'G8', 81: 'G9', 82: 'G10', 83: 'G11', 84: 'G12',
    85: 'H1', 86: 'H2', 87: 'H3', 88: 'H4', 89: 'H5', 90: 'H6', 91: 'H7', 92: 'H8', 93: 'H9', 94: 'H10', 95: 'H11', 96: 'H12'
}

#%%
# SETUP LOGGING------------------------------------------------------------------------------------

# get the path to the current directory
strWD = os.getcwd()
# get the name of this file
strLogFileName = os.path.basename(__file__)
# split the file name and the extension
strLogFileName = os.path.splitext(strLogFileName)[0]
# add .log to the file name
strLogFileName = strLogFileName + ".log"
# join the log file name to the current directory
print(strLogFileName)
strLogFilePath = os.path.join(strWD, strLogFileName)

# Initialize logging
logging.basicConfig(
    level = logging.DEBUG,                                                      # Can be changed to logging.INFO to see less
    format = "%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(strLogFilePath, mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)

#%%
# INITIALIZE EXPERIMENT----------------------------------------------------------------------------
# make a variable to store the well in the reactor to be used
strWell2Test = 'C5'                                           # YANG reactor

# provide a run number
strRunNumber = "014"                                           # YANG str

# make a variable to store the next pipette tip location
intPipetteTipLoc = 1                                          # pipette solution id

# get the current time
strTime_start = datetime.now().strftime("%H:%M:%S")

# get the current date
strDate = datetime.now().strftime("%Y%m%d")


# make a strin with the experimentID
strExperimentID = f"{strDate}_{strRunNumber}"

# make a new directory in the data folder to store the results
strExperimentPath = os.path.join(strWD, 'data', strExperimentID)
os.makedirs(strExperimentPath, exist_ok=True)
os.makedirs(os.path.join(strExperimentPath, 'deposition'), exist_ok=True)
os.makedirs(os.path.join(strExperimentPath, 'characterization'), exist_ok=True)

# make a metadata file in the new directory
strMetadataPath = os.path.join(strExperimentPath, f"metadata.json")
dicMetadata = {"date": strDate,
               "time": strTime_start,
               "runNumber": strRunNumber,
               "experimentID": strExperimentID,
               "cell":strWell2Test,
               "status": "running",
               "notes": "Ni(NO3)2 9H2O electrodeposition on C paper (Top) and basic OER"}

with open(strMetadataPath, 'w') as f:
    json.dump(dicMetadata, f)

# log the start of the experiment
logging.info(f"experiment {strExperimentID} started!")

#%%
# SETUP OPENTRONS PLATFORM-------------------------------------------------------------------------

robotIP = "100.67.89.154"
# initialize an the opentrons client
oc = opentronsClient(
    strRobotIP = robotIP
)


# -----LOAD OPENTRONS STANDARD LABWARE-----

    # -----LOAD OPENTRONS TIP RACK-----
# load opentrons tip rack in slot 1
strID_pipetteTipRack = oc.loadLabware(
    intSlot = 1,
    strLabwareName = 'opentrons_96_tiprack_1000ul'
)

# -----LOAD CUSTOM LABWARE-----

# get path to current directory
strCustomLabwarePath = os.getcwd()
# join "labware" folder to current directory
strCustomLabwarePath = os.path.join(strCustomLabwarePath, 'labware')

    # -----LOAD 25ml VIAL RACK-----
# join "nis_8_reservoir_25000ul.json" to labware directory
strCustomLabwarePath_temp = os.path.join(strCustomLabwarePath, 'nis_8_reservoir_25000ul.json')
# read json file
with open(strCustomLabwarePath_temp, 'r', encoding='utf-8') as f:
    dicCustomLabware_temp = json.load(f)
# load custom labware in slot 2
strID_vialRack_2 = oc.loadCustomLabware(
    dicLabware = dicCustomLabware_temp,
    intSlot = 2
)

# load custom labware in slot 7
strID_vialRack_7 = oc.loadCustomLabware(
    dicLabware = dicCustomLabware_temp,
    intSlot = 7
)

# load custom labware in slot 11
strID_vialRack_11 = oc.loadCustomLabware(
    dicLabware = dicCustomLabware_temp,
    intSlot = 11
)

    # -----LOAD WASH STATION-----
# join "nis_2_wellplate_30000ul.json" to labware directory
strCustomLabwarePath_temp = os.path.join(strCustomLabwarePath, 'nis_2_wellplate_30000ul.json')
# read json file
with open(strCustomLabwarePath_temp, 'r', encoding='utf-8') as f:
    dicCustomLabware_temp = json.load(f)
# load custom labware in slot 3
strID_washStation = oc.loadCustomLabware(
    dicLabware = dicCustomLabware_temp,
    intSlot = 3
)

#     # -----LOAD AUTODIAL CELL-----
# # join "autodial_25_reservoir_4620ul.json" to labware directory
# strCustomLabwarePath_temp = os.path.join(strCustomLabwarePath, 'autodial_25_reservoir_4620ul.json')
# # read json file
# with open(strCustomLabwarePath_temp) as f:
#     dicCustomLabware_temp = json.load(f)
# # load custom labware in slot 4
# strID_autodialCell = oc.loadCustomLabware(
#     dicLabware = dicCustomLabware_temp,
#     intSlot = 4
# )


    # -----LOAD ZOU'S CELL-----
# # join "zou_21_wellplate_4500ul.json" to labware directory
# strCustomLabwarePath_temp = os.path.join(strCustomLabwarePath, 'zou_21_wellplate_4500ul.json')
# # read json file
# with open(strCustomLabwarePath_temp) as f:
#     dicCustomLabware_temp = json.load(f)
# # load custom labware in slot 6
# strID_zouWellplate = oc.loadCustomLabware(dicLabware = dicCustomLabware_temp,
#                                             intSlot = 4)

#     # -----LOAD 50ml BEAKERS-----
# # join "tlg_1_reservoir_50000ul.json" to labware directory
# strCustomLabwarePath_temp = os.path.join(strCustomLabwarePath, 'tlg_1_reservoir_50000ul.json')

# # read json file
# with open(strCustomLabwarePath_temp) as f:
#     dicCustomLabware_temp = json.load(f)

# strID_dIBeaker = oc.loadCustomLabware(dicLabware = dicCustomLabware_temp,
#                                       intSlot = 5)


    # -----LOAD NIS'S REACTOR-----
# join "nis_15_wellplate_3895ul.json" to labware directory
strCustomLabwarePath_temp = os.path.join(strCustomLabwarePath, 'nis_15_wellplate_3895ul.json')

# read json file
with open(strCustomLabwarePath_temp, 'r', encoding='utf-8') as f:
    dicCustomLabware_temp = json.load(f)

strID_NISreactor = oc.loadCustomLabware(
    dicLabware = dicCustomLabware_temp,
    intSlot = 9
)

    # -----LOAD ELECTRODE TIP RACK-----
# join "nis_4_tiprack_1ul.json" to labware directory
strCustomLabwarePath_temp = os.path.join(strCustomLabwarePath, 'nistall_4_tiprack_1ul.json')

# read json file
with open(strCustomLabwarePath_temp, 'r', encoding='utf-8') as f:
    dicCustomLabware_temp = json.load(f)

# load custom labware in slot 10
strID_electrodeTipRack = oc.loadCustomLabware(
    dicLabware = dicCustomLabware_temp,
    intSlot = 10
)

# LOAD OPENTRONS STANDARD INSTRUMENTS--------------------------------------------------------------
# add pipette
oc.loadPipette(
    strPipetteName = 'p1000_single_gen2',
    strMount = 'right'
)

#%%
# MOVE OPENTRONS INSTRUMENTS-----------------------------------------------------------------------

# turn the lights on 
oc.lights(True)

# home robot
oc.homeRobot()

# #%%
# # PREPARE WELL WITH ACID---------------------------------------------------------------------------

# oc.moveToWell(
#     strLabwareName=strID_electrodeTipRack,
#     strWellName='B1',
#     strPipetteName="p1000_single_gen2",
#     strOffsetStart='top',
#     fltOffsetX=0.5,
#     fltOffsetY=0.5,
#     fltOffsetZ=2,
#     intSpeed=100
# )

# oc.pickUpTip(
#     strLabwareName=strID_electrodeTipRack,
#     strWellName='B1',
#     strPipetteName="p1000_single_gen2",
#     strOffsetStart='top',
#     fltOffsetX=0.5,
#     fltOffsetY=0.5
# )

# oc.moveToWell(
#     strLabwareName=strID_NISreactor,
#     strWellName=strWell2Test,
#     strPipetteName='p1000_single_gen2',
#     strOffsetStart='top',
#     fltOffsetX=0.3,
#     fltOffsetY=0.5,
#     fltOffsetZ=-10,
#     intSpeed=100
# )

# oc.moveToWell(
#     strLabwareName=strID_NISreactor,
#     strWellName=strWell2Test,
#     strPipetteName='p1000_single_gen2',
#     strOffsetStart='top',
#     fltOffsetX=0.3,
#     fltOffsetY=0.5,
#     fltOffsetZ=-52,
#     intSpeed=100
# )

# ac = Arduino()

# ac.dispense_ml(
#     pumpNumber=2,
#     volume=1
# )
# time.sleep(300)
# ac.dispense_ml(
#     pumpNumber=nozzle['out'],
#     volume=3
# )

# ac.dispense_ml(
#     pumpNumber=nozzle['water'],
#     volume=1
# )
# ac.dispense_ml(
#     pumpNumber=nozzle['out'],
#     volume=3
# )

# ac.dispense_ml(
#     pumpNumber=nozzle['water'],
#     volume=1
# )
# ac.dispense_ml(
#     pumpNumber=nozzle['out'],
#     volume=3
# )

# ac.dispense_ml(
#     pumpNumber=nozzle['water'],
#     volume=1
# )
# ac.dispense_ml(
#     pumpNumber=nozzle['out'],
#     volume=3
# )

# oc.moveToWell(
#     strLabwareName=strID_electrodeTipRack,
#     strWellName='B1',
#     strPipetteName="p1000_single_gen2",
#     strOffsetStart='top',
#     fltOffsetX=0.5,
#     fltOffsetY=0.5,
#     fltOffsetZ=10,
#     intSpeed=100
# )

# oc.moveToWell(
#     strLabwareName=strID_electrodeTipRack,
#     strWellName='B1',
#     strPipetteName="p1000_single_gen2",
#     strOffsetStart='top',
#     fltOffsetX=0.5,
#     fltOffsetY=0.5,
#     fltOffsetZ=-80,
#     intSpeed=100
# )

# oc.dropTip(
#     strLabwareName=strID_electrodeTipRack,
#     strWellName='B1',
#     strPipetteName="p1000_single_gen2",
#     strOffsetStart='top',
#     fltOffsetX=0.5,
#     fltOffsetY=0.5,
#     fltOffsetZ=-88
# )

# ac.connection.close()



# -----USE OPENTRONS TO MOVE M+ SOLUTIONS TO DEPOSIT-----
# move to pipette tip rack
oc.moveToWell(
    strLabwareName = strID_pipetteTipRack,
    strWellName = dicNumToPipetteTipLoc[intPipetteTipLoc],
    strPipetteName = 'p1000_single_gen2',
    strOffsetStart = 'top',
    fltOffsetY = 1,
    intSpeed = 100
)

# pick up pipette tip
oc.pickUpTip(
    strLabwareName = strID_pipetteTipRack,
    strPipetteName = 'p1000_single_gen2',
    strWellName = dicNumToPipetteTipLoc[intPipetteTipLoc],
    fltOffsetY = 1
)

fillWell(
    opentronsClient = oc,
    strLabwareName_from = strID_vialRack_2,
    strWellName_from = 'B1',                       # fe(NO3)3 YANG - CHANGE IF YOU RUN OUT
    strOffsetStart_from = 'bottom',
    strPipetteName = 'p1000_single_gen2',
    strLabwareName_to = strID_NISreactor,
    strWellName_to = strWell2Test,
    strOffsetStart_to = 'top',
    intVolume = 3000,
    fltOffsetX_from = 0,
    fltOffsetY_from = 0,
    fltOffsetZ_from = 8,
    fltOffsetX_to = -1,
    fltOffsetY_to = 0.5,
    fltOffsetZ_to = 0,
    intMoveSpeed = 100
)


# move back to pipette tip rack
oc.moveToWell(
    strLabwareName = strID_pipetteTipRack,
    strWellName = dicNumToPipetteTipLoc[intPipetteTipLoc],
    strPipetteName = 'p1000_single_gen2',
    strOffsetStart = 'top',
    fltOffsetY = 1,
    intSpeed = 100
)

# drop pipette tip
oc.dropTip(
    strLabwareName = strID_pipetteTipRack,
    strPipetteName = 'p1000_single_gen2',
    strWellName = dicNumToPipetteTipLoc[intPipetteTipLoc],
    strOffsetStart = 'bottom',
    fltOffsetY = 1,
    fltOffsetZ = 7
)

# increment the pipette tip location
intPipetteTipLoc += 1


# -----USE OPENTRONS TO MOVE ELECTRODES-----


# [FIX ME]*** CHECK TO SEE IF PIPETTE IS EMPTY ***

# move to electrode tip rack
oc.moveToWell(
    strLabwareName = strID_electrodeTipRack,
    strWellName = 'A2',
    strPipetteName = 'p1000_single_gen2',
    strOffsetStart = 'top',
    fltOffsetX = 0.6,
    fltOffsetY = 0.5,
    fltOffsetZ = 3,
    intSpeed = 100
)
# pick up electrode tip
oc.pickUpTip(
    strLabwareName = strID_electrodeTipRack,
    strPipetteName = 'p1000_single_gen2',
    strWellName = 'A2',
    fltOffsetX = 0.6,
    fltOffsetY = 0.5
)

ac = Arduino()

# rinse electrode
rinseElectrode(opentronsClient = oc,
               strLabwareName = strID_washStation,
               arduinoClient = ac)

ac.connection.close()

# move to top only!!
oc.moveToWell(strLabwareName = strID_NISreactor,
              strWellName = strWell2Test,
              strPipetteName = 'p1000_single_gen2',
              strOffsetStart = 'top',
              fltOffsetX = 0.5,
              fltOffsetY = 0.5,
              fltOffsetZ = 5,
              intSpeed = 50)

# move to autodial cell
oc.moveToWell(strLabwareName = strID_NISreactor,
              strWellName = strWell2Test,
              strPipetteName = 'p1000_single_gen2',
              strOffsetStart = 'top',
              fltOffsetX = 0.5,
              fltOffsetY = 0.5,
              fltOffsetZ = -22,
              intSpeed = 50)

#%%
# RUN ELECTRODEPOSITION EXPERIMENT---------------------------------------------
# -----CP-----
# make deposition step
cpStep_deposition = CPStep(
    current=-0.002,
    duration=60,
    vs_initial=False
)

cpParams_deposition = CPParams(
    record_every_dT=0.1,
    record_every_dE=0.05,
    n_cycles=0,
    steps=[cpStep_deposition],
    I_range=I_RANGE.I_RANGE_10mA
)

cpTech_deposition = CPTechnique(cpParams_deposition)

# -----OCV-----
# create OCV parameters
ocvParams_1mins = OCVParams(
    rest_time_T = 60,
    record_every_dT = 0.5,
    record_every_dE = 10,
    E_range = E_RANGE.E_RANGE_2_5V,
    bandwidth = BANDWIDTH.BW_5,
    )

# create OCV technique
ocvTech_1mins = OCVTechnique(ocvParams_1mins)

boolTryToConnect = True
intAttempts_temp = 0
intMaxAttempts = 3

# initialize an empty dataframe to store the results
dfData = pd.DataFrame()
# initialize a counter to keep track of the technique index
intID_tech = 0
# initialize a counter to keep track of the number to add to technique index 
# (to account for multiple processes)
intID_tech_add = 0
# initialize a string to keep track of the current technique
strCurrentTechnique = ''

boolNewTechnique = False
boolAdd1ToTechIndex = False
boolFirstTechnique = True

fltTime_prev = 0
fltTime_curr = 0



while boolTryToConnect and intAttempts_temp < intMaxAttempts:
    logging.info(f"Attempting to connect to the Biologic: {intAttempts_temp+1} / {intMaxAttempts}")

    try:
        # run all techniques
        with connect('USB0') as bl:
            channel = bl.get_channel(1)

            # run all techniques
            runner = channel.run_techniques([
                ocvTech_1mins,
                cpTech_deposition,
                ocvTech_1mins
            ])
    
            for data_temp in runner:

                if boolFirstTechnique:
                    # down select the string to only that which is inside the single quotes 
                    strCurrentTechnique = str(type(data_temp.data))
                    # down select the string to only that which is inside the single quotes
                    strCurrentTechnique = strCurrentTechnique.split("'")[1]
                    # down select the string to only that which is after the second to last period
                    strCurrentTechnique = strCurrentTechnique.split(".")[-2]
                    boolFirstTechnique = False

                # check if the technique index is not the same as the previous technique index
                if data_temp.tech_index != intID_tech:
                    boolNewTechnique = True
                
                if 'process_index' in data_temp.data.to_json(): 
                    dfData_temp = pd.DataFrame(data_temp.data.process_data.to_json(), index=[0])
                else:
                    dfData_temp = pd.DataFrame(data_temp.data.to_json(), index=[0])
                    # if the time is available in the data
                    if 'time' in data_temp.data.to_json():
                        fltTime_prev = fltTime_curr
                        fltTime_curr = float(data_temp.data.to_json()['time'])
                    # if the previous time is greater than the current time but the technique id is the sam , then a new technique is being run
                    if (fltTime_prev-2 > fltTime_curr) and (data_temp.tech_index == intID_tech):
                        boolAdd1ToTechIndex = True
                        boolNewTechnique = True

                if boolNewTechnique:
                    # the data coming in is from a new technique - save the previous data to a csv
                    dfData.to_csv(os.path.join(strExperimentPath, 'deposition', f'{strExperimentID}_{intID_tech+intID_tech_add}_{strCurrentTechnique}.csv'))
                    # reinitialize the dataframe
                    dfData = pd.DataFrame()
                    # reset the boolean
                    boolNewTechnique = False

                    if boolAdd1ToTechIndex:
                        intID_tech_add += 1
                        boolAdd1ToTechIndex = False

                    # set the technique index to the current technique index
                    intID_tech = data_temp.tech_index
                    # update the current technique
                    strCurrentTechnique = str(type(data_temp.data))
                    # down select the string to only that which is inside the single quotes
                    strCurrentTechnique = strCurrentTechnique.split("'")[1]
                    # down select the string to only that which is after the second to last period
                    strCurrentTechnique = strCurrentTechnique.split(".")[-2] 

                # log the data
                logging.info(data_temp)
                # add the data to the dataframe
                dfData = pd.concat([dfData, dfData_temp], ignore_index=True)
            else:
                time.sleep(1)

            # break the loop - successful connection
            boolTryToConnect = False
            # save the final data to a csv
            dfData.to_csv(os.path.join(strExperimentPath, 'deposition', f'{strExperimentID}_{intID_tech+intID_tech_add}_{strCurrentTechnique}.csv'))

    except Exception as e:
        logging.error(f"Failed to connect to the Biologic: {e}")
        logging.info(f"Attempting again in 50 seconds")
        time.sleep(50)
        intAttempts_temp += 1

# log the end of the experiment
logging.info("End of electrodeposition experiment!")

# # update the metadata file
# dicMetadata['status'] = "completed"
# dicMetadata['time'] = datetime.now().strftime("%H:%M:%S")
# with open(strMetadataPath, 'w') as f:
#     json.dump(dicMetadata, f)

#%%
# USE OPENTRONS INSTRUMENTS AND ARDUINO TO CLEAN ELECTRODE-----------------------------------------

# initialize an the arduino client
ac = Arduino() #arduino_search_string = "USB Serial")

# wash electrode
washElectrode(opentronsClient = oc,
              strLabwareName = strID_washStation,
              arduinoClient = ac)

# move to electrode tip rack
oc.moveToWell(strLabwareName = strID_electrodeTipRack,
              strWellName = 'A2',
              strPipetteName = 'p1000_single_gen2',
              strOffsetStart = 'top',
              fltOffsetX = 0.6,
              fltOffsetY = 0.5,
              intSpeed = 50)

# drop electrode tip
oc.dropTip(strLabwareName = strID_electrodeTipRack,
               strPipetteName = 'p1000_single_gen2',
               strWellName = 'A2',
               fltOffsetX = 0.6,
               fltOffsetY = 0.5,
               fltOffsetZ = 6,
               strOffsetStart = "bottom")

# close arduino
ac.connection.close()


#%%
# RINSE WELL----------------------------------------------------------------------------------

oc.moveToWell(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5,
    fltOffsetZ=2,
    intSpeed=100
)

oc.pickUpTip(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5
)

oc.moveToWell(
    strLabwareName=strID_NISreactor,
    strWellName=strWell2Test,
    strPipetteName='p1000_single_gen2',
    strOffsetStart='top',
    fltOffsetX=0.3,
    fltOffsetY=0.5,
    fltOffsetZ=-10,
    intSpeed=100
)

oc.moveToWell(
    strLabwareName=strID_NISreactor,
    strWellName=strWell2Test,
    strPipetteName='p1000_single_gen2',
    strOffsetStart='top',
    fltOffsetX=0.3,
    fltOffsetY=0.5,
    fltOffsetZ=-35,
    intSpeed=100
)

ac = Arduino()

ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=1
)

oc.moveToWell(
    strLabwareName=strID_NISreactor,
    strWellName=strWell2Test,
    strPipetteName='p1000_single_gen2',
    strOffsetStart='top',
    fltOffsetX=0.3,
    fltOffsetY=0.5,
    fltOffsetZ=-40,
    intSpeed=100
)

ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=1
)

oc.moveToWell(
    strLabwareName=strID_NISreactor,
    strWellName=strWell2Test,
    strPipetteName='p1000_single_gen2',
    strOffsetStart='top',
    fltOffsetX=0.3,
    fltOffsetY=0.5,
    fltOffsetZ=-50,
    intSpeed=100
)

ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=1
)

ac.dispense_ml(
    pumpNumber=nozzle['water'],
    volume=1
)
ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=3
)

ac.dispense_ml(
    pumpNumber=nozzle['water'],
    volume=1
)
ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=3
)

ac.dispense_ml(
    pumpNumber=nozzle['water'],
    volume=1
)
ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=3
)


oc.moveToWell(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5,
    fltOffsetZ=10,
    intSpeed=100
)

oc.moveToWell(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5,
    fltOffsetZ=-80,
    intSpeed=100
)

oc.dropTip(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5,
    fltOffsetZ=-88
)

ac.connection.close()

#%%
# -----USE OPENTRONS TO MOVE KOH FOR CHARACTEIZATION-----

# move to pipette tip rack
oc.moveToWell(
    strLabwareName = strID_pipetteTipRack,
    strWellName = dicNumToPipetteTipLoc[intPipetteTipLoc],
    strPipetteName = 'p1000_single_gen2',
    strOffsetStart = 'top',
    fltOffsetY = 1,
    intSpeed = 100
)

# pick up pipette tip
oc.pickUpTip(
    strLabwareName = strID_pipetteTipRack,
    strPipetteName = 'p1000_single_gen2',
    strWellName = dicNumToPipetteTipLoc[intPipetteTipLoc],
    fltOffsetY = 1
)

fillWell(
    opentronsClient = oc,
    strLabwareName_from = strID_vialRack_2,
    strWellName_from = 'B2',                       # KOH YANG - CHANGE IF YOU RUN OUT
    strOffsetStart_from = 'bottom',
    strPipetteName = 'p1000_single_gen2',
    strLabwareName_to = strID_NISreactor,
    strWellName_to = strWell2Test,
    strOffsetStart_to = 'top',
    intVolume = 3000,
    fltOffsetX_from = 0,
    fltOffsetY_from = 0,
    fltOffsetZ_from = 8,
    fltOffsetX_to = -1,
    fltOffsetY_to = 0.5,
    fltOffsetZ_to = 0,
    intMoveSpeed = 100
)


# move back to pipette tip rack
oc.moveToWell(
    strLabwareName = strID_pipetteTipRack,
    strWellName = dicNumToPipetteTipLoc[intPipetteTipLoc],
    strPipetteName = 'p1000_single_gen2',
    strOffsetStart = 'top',
    fltOffsetY = 1,
    intSpeed = 100
)

# drop pipette tip
oc.dropTip(
    strLabwareName = strID_pipetteTipRack,
    strPipetteName = 'p1000_single_gen2',
    strWellName = dicNumToPipetteTipLoc[intPipetteTipLoc],
    strOffsetStart = 'bottom',
    fltOffsetY = 1,
    fltOffsetZ = 7
)

#%%
# -----USE OPENTRONS TO MOVE ELECTRODES-----


# *** CHECK TO SEE IF PIPETTE IS EMPTY ***

# move to electrode tip rack
oc.moveToWell(
    strLabwareName = strID_electrodeTipRack,
    strWellName = 'A2',
    strPipetteName = 'p1000_single_gen2',
    strOffsetStart = 'top',
    fltOffsetX = 0.6,
    fltOffsetY = 0.5,
    fltOffsetZ = 3,
    intSpeed = 100
)
# pick up electrode tip
oc.pickUpTip(
    strLabwareName = strID_electrodeTipRack,
    strPipetteName = 'p1000_single_gen2',
    strWellName = 'A2',
    fltOffsetX = 0.6,
    fltOffsetY = 0.5
)

ac = Arduino()

# rinse electrode
rinseElectrode(opentronsClient = oc,
               strLabwareName = strID_washStation,
               arduinoClient = ac)

ac.connection.close()

# move to top only!!
oc.moveToWell(strLabwareName = strID_NISreactor,
              strWellName = strWell2Test,
              strPipetteName = 'p1000_single_gen2',
              strOffsetStart = 'top',
              fltOffsetX = 0.5,
              fltOffsetY = 0.5,
              fltOffsetZ = 5,
              intSpeed = 50)

# move to autodial cell
oc.moveToWell(strLabwareName = strID_NISreactor,
              strWellName = strWell2Test,
              strPipetteName = 'p1000_single_gen2',
              strOffsetStart = 'top',
              fltOffsetX = 0.5,
              fltOffsetY = 0.5,
              fltOffsetZ = -21,
              intSpeed = 50)

#%%
# RUN CHARACTERIZATION EXPERIMENT----------------------------------------------

# -----OCV-----
# create OCV parameters
ocvParams_10sec = OCVParams(
    rest_time_T = 10,
    record_every_dT = 0.5,
    record_every_dE = 10,
    E_range = E_RANGE.E_RANGE_10V,
    bandwidth = BANDWIDTH.BW_5,
    )

# create OCV technique
ocvTech_10sec = OCVTechnique(ocvParams_10sec)


# -----PEIS----- under OER & above OER
applied_ocv = 0.01
# applied_ocv_OER = 0.7

peisParams_noOER = PEISParams(
    vs_initial = False,
    initial_voltage_step = 0.0,
    duration_step = 60,
    record_every_dT = 0.5,
    record_every_dI = 0.01,
    final_frequency = 1,
    initial_frequency = 200000,
    sweep = SweepMode.Logarithmic,
    amplitude_voltage = applied_ocv,
    frequency_number = 60,
    average_n_times = 2,
    correction = False,
    wait_for_steady = 0.1,
    bandwidth = BANDWIDTH.BW_5,
    E_range = E_RANGE.E_RANGE_2_5V
    )

peisParams_OER = PEISParams(
    vs_initial = False,
    initial_voltage_step = 0.7,
    duration_step = 60,
    record_every_dT = 0.5,
    record_every_dI = 0.01,
    final_frequency = 1,
    initial_frequency = 200000,
    sweep = SweepMode.Logarithmic,
    amplitude_voltage = applied_ocv,
    frequency_number = 60,
    average_n_times = 2,
    correction = False,
    wait_for_steady = 0.1,
    bandwidth = BANDWIDTH.BW_5,
    E_range = E_RANGE.E_RANGE_2_5V
    )

# create PEIS technique
peisTech_noOER = PEISTechnique(peisParams_noOER)
peisTech_OER = PEISTechnique(peisParams_OER)

# -----CV-----
# create CV steps -- active materials
Ei_active = CVStep(
    voltage = 1.25,
    scan_rate = 0.005,
    vs_initial = False
)
E1_active = CVStep(
    voltage = 1.3,
    scan_rate = 0.005,
    vs_initial = False
)
E2_active = CVStep(
    voltage = 1.25,
    scan_rate = 0.005,
    vs_initial = False
)
Ef_active = CVStep(
    voltage = 1.25,
    scan_rate = 0.005,
    vs_initial = False
)

cvParams_active = CVParams(
    record_every_dE = 0.01,
    average_over_dE = False,
    n_cycles = 60,
    begin_measuring_i = 0.5,
    end_measuring_i = 1,
    Ei = Ei_active,
    E1 = E1_active,
    E2 = E2_active,
    Ef = Ef_active,
    bandwidth = BANDWIDTH.BW_5,
    I_range = I_RANGE.I_RANGE_100mA
)

cvTech_active = CVTechnique(cvParams_active)


# -----CV----- check the redox peaks 
Ei_active = CVStep(
    voltage = -0.8,
    scan_rate = 0.025,
    vs_initial = False
)
E1_active = CVStep(
    voltage = 1.0,
    scan_rate = 0.025,
    vs_initial = False
)
E2_active = CVStep(
    voltage = -0.8,
    scan_rate = 0.025,
    vs_initial = False
)
Ef_active = CVStep(
    voltage = 1.0,
    scan_rate = 0.025,
    vs_initial = False
)

cvParams_redox = CVParams(
    record_every_dE = 0.01,
    average_over_dE = False,
    n_cycles = 1,
    begin_measuring_i = 0.5,
    end_measuring_i = 1,
    Ei = Ei_active,
    E1 = E1_active,
    E2 = E2_active,
    Ef = Ef_active,
    bandwidth = BANDWIDTH.BW_5,
    I_range = I_RANGE.I_RANGE_100mA
)

cvTech_redox = CVTechnique(cvParams_redox)

# -----CVA----- - CV with different sweeping speed
# create CV steps
Ei_20 = CVStep(
    voltage = -0.05,
    scan_rate = 0.02,
    vs_initial = True # RUNZE CHANGES
)
E1_20 = CVStep(
    voltage = 0.05,
    scan_rate = 0.02,
    vs_initial = True
)
E2_20 = CVStep(
    voltage = -0.05,
    scan_rate = 0.02,
    vs_initial = True
)
Ef_20 = CVStep(
    voltage = -0.05,
    scan_rate = 0.02,
    vs_initial = True
)

cvParams_20 = CVParams(
    record_every_dE = 0.001,
    average_over_dE = True,
    n_cycles = 3,
    begin_measuring_i = 0.5,
    end_measuring_i = 1,
    Ei = Ei_20,
    E1 = E1_20,
    E2 = E2_20,
    Ef = Ef_20,
    bandwidth = BANDWIDTH.BW_5,
    I_range = I_RANGE.I_RANGE_10mA
)

cvTech_20 = CVTechnique(cvParams_20)

# create CV steps
Ei_40 = CVStep(
    voltage = 0.0,
    scan_rate = 0.04,
    vs_initial = True 
)
E1_40 = CVStep(
    voltage = 0.10,
    scan_rate = 0.04,
    vs_initial = True
)
E2_40 = CVStep(
    voltage = -0.00,
    scan_rate = 0.04,
    vs_initial = True
)
Ef_40 = CVStep(
    voltage = -0.00,
    scan_rate = 0.04,
    vs_initial = True
)

cvParams_40 = CVParams(
    record_every_dE = 0.001,
    average_over_dE = True,
    n_cycles = 3,
    begin_measuring_i = 0.5,
    end_measuring_i = 1,
    Ei = Ei_40,
    E1 = E1_40,
    E2 = E2_40,
    Ef = Ef_40,
    bandwidth = BANDWIDTH.BW_5,
    I_range = I_RANGE.I_RANGE_10mA
)

cvTech_40 = CVTechnique(cvParams_40)

# create CV steps
Ei_60 = CVStep(
    voltage = -0.00,
    scan_rate = 0.06,
    vs_initial = True 
)
E1_60 = CVStep(
    voltage = 0.10,
    scan_rate = 0.06,
    vs_initial = True
)
E2_60 = CVStep(
    voltage = -0.00,
    scan_rate = 0.06,
    vs_initial = True
)
Ef_60 = CVStep(
    voltage = -0.00,
    scan_rate = 0.06,
    vs_initial = True
)

cvParams_60 = CVParams(
    record_every_dE = 0.001,
    average_over_dE = True,
    n_cycles = 3,
    begin_measuring_i = 0.5,
    end_measuring_i = 1,
    Ei = Ei_60,
    E1 = E1_60,
    E2 = E2_60,
    Ef = Ef_60,
    bandwidth = BANDWIDTH.BW_5,
    I_range = I_RANGE.I_RANGE_10mA
)

cvTech_60 = CVTechnique(cvParams_60)

# create CV steps
Ei_80 = CVStep(
    voltage = -0.00,
    scan_rate = 0.08,
    vs_initial = True 
)
E1_80 = CVStep(
    voltage = 0.10,
    scan_rate = 0.08,
    vs_initial = True
)
E2_80 = CVStep(
    voltage = -0.00,
    scan_rate = 0.08,
    vs_initial = True
)
Ef_80 = CVStep(
    voltage = -0.00,
    scan_rate = 0.08,
    vs_initial = True
)

cvParams_80 = CVParams(
    record_every_dE = 0.001,
    average_over_dE = True,
    n_cycles = 3,
    begin_measuring_i = 0.5,
    end_measuring_i = 1,
    Ei = Ei_80,
    E1 = E1_80,
    E2 = E2_80,
    Ef = Ef_80,
    bandwidth = BANDWIDTH.BW_5,
    I_range = I_RANGE.I_RANGE_10mA
)

cvTech_80 = CVTechnique(cvParams_80)

# create CV steps
Ei_100 = CVStep(
    voltage = -0.00,
    scan_rate = 0.1,
    vs_initial = True 
)
E1_100 = CVStep(
    voltage = 0.10,
    scan_rate = 0.1,
    vs_initial = True
)
E2_100 = CVStep(
    voltage = -0.00,
    scan_rate = 0.1,
    vs_initial = True
)
Ef_100 = CVStep(
    voltage = -0.00,
    scan_rate = 0.1,
    vs_initial = True
)

cvParams_100 = CVParams(
    record_every_dE = 0.001,
    average_over_dE = True,
    n_cycles = 3,
    begin_measuring_i = 0.5,
    end_measuring_i = 1,
    Ei = Ei_100,
    E1 = E1_100,
    E2 = E2_100,
    Ef = Ef_100,
    bandwidth = BANDWIDTH.BW_5,
    I_range = I_RANGE.I_RANGE_10mA
)

cvTech_100 = CVTechnique(cvParams_100)


# ----- CV ----- stability test
# create CV steps
Ei_stability = CVStep(
    voltage = 0.6,
    scan_rate = 0.025,
    vs_initial = False 
)
E1_stability = CVStep(
    voltage = 1.00,
    scan_rate = 0.025,
    vs_initial = False
)
E2_stability = CVStep(
    voltage = 0.6,
    scan_rate = 0.025,
    vs_initial = False
)
Ef_stability = CVStep(
    voltage = 1.00,
    scan_rate = 0.025,
    vs_initial = False
)

cvParams_stability = CVParams(
    record_every_dE = 0.01,
    average_over_dE = False,
    n_cycles = 50,
    begin_measuring_i = 0.5,
    end_measuring_i = 1,
    Ei = Ei_stability,
    E1 = E1_stability,
    E2 = E2_stability,
    Ef = Ef_stability,
    bandwidth = BANDWIDTH.BW_5,
    I_range = I_RANGE.I_RANGE_10mA
)

cvTech_stability = CVTechnique(cvParams_stability)



# -----LSV-----

# create LP steps for testing OER performance
Ei_lsv = LPStep(
    voltage_scan=0,
    scan_rate=0.005,
    vs_initial_scan=False
)
El_lsv = LPStep(
    voltage_scan=1,
    scan_rate=0.005,
    vs_initial_scan=False
)
# create LP parameters for LPR with OCP
lpParams_lsv_wOCP = LPParams(
    record_every_dEr = 0.01,
    rest_time_T = 5,
    record_every_dTr = 0.5,
    Ei = Ei_lsv,
    El = El_lsv,
    record_every_dE = 0.001,
    average_over_dE = False,
    begin_measuring_I = 0.5,
    end_measuring_I = 1,
    I_range = I_RANGE.I_RANGE_100mA,
    E_range = E_RANGE.E_RANGE_2_5V
)

# create a technique for LPR with OCP
lpTech_lsv_wOCP = LPTechnique(lpParams_lsv_wOCP)



# this is fucking stupid - fix it in the future -- not stupid, its ok!
def run_and_save_characterization(
    strExperimentID,
    strExperimentPath,
    techniques_list,
    intGlobalTechID=0,  # for multiple batch
    intMaxAttempts=3,
    usb_port='USB0',
    channel_id=1
):
    """
    Run Biologic techniques in batches and save each technique's data as a separate CSV,
    with increasing global numbering across batches.
    """
    boolTryToConnect = True
    intAttempts_temp = 0

    boolFirstTechnique = True
    boolNewTechnique = False
    boolAdd1ToTechIndex = False

    intID_tech = None
    fltTime_prev = 0.0
    fltTime_curr = 0.0
    dfData = pd.DataFrame()
    strCurrentTechnique = ''

    while boolTryToConnect and intAttempts_temp < intMaxAttempts:
        logging.info(f"Attempting to connect to Biologic: {intAttempts_temp + 1} / {intMaxAttempts}")

        try:
            with connect(usb_port) as bl:
                channel = bl.get_channel(channel_id)
                runner = channel.run_techniques(techniques_list)

                for data_temp in runner:
                    if boolFirstTechnique:
                        strCurrentTechnique = str(type(data_temp.data)).split("'")[1].split(".")[-2]
                        boolFirstTechnique = False

                    # detect whether a tech is new
                    if intID_tech is None or data_temp.tech_index != intID_tech:
                        boolNewTechnique = True

                    # load data
                    if 'process_index' in data_temp.data.to_json():
                        dfData_temp = pd.DataFrame(data_temp.data.process_data.to_json(), index=[0])
                    else:
                        dfData_temp = pd.DataFrame(data_temp.data.to_json(), index=[0])

                        if 'time' in data_temp.data.to_json():
                            fltTime_prev = fltTime_curr
                            fltTime_curr = float(data_temp.data.to_json()['time'])

                        if (fltTime_prev - 2 > fltTime_curr) and (data_temp.tech_index == intID_tech):
                            boolAdd1ToTechIndex = True
                            boolNewTechnique = True

                    if boolNewTechnique:
                        # save the last tech if current tech is not new
                        if not dfData.empty:
                            filename = f'{strExperimentID}_{intGlobalTechID}_{strCurrentTechnique}.csv'
                            filepath = os.path.join(strExperimentPath, 'characterization', filename)
                            dfData.to_csv(filepath, index=False)
                            logging.info(f"Saved: {filepath}")
                            intGlobalTechID += 1  

                        dfData = pd.DataFrame()
                        boolNewTechnique = False
                        boolAdd1ToTechIndex = False

                        intID_tech = data_temp.tech_index
                        strCurrentTechnique = str(type(data_temp.data)).split("'")[1].split(".")[-2]

                    logging.info(data_temp)
                    dfData = pd.concat([dfData, dfData_temp], ignore_index=True)

                # save the last 
                if not dfData.empty:
                    filename = f'{strExperimentID}_{intGlobalTechID}_{strCurrentTechnique}.csv'
                    filepath = os.path.join(strExperimentPath, 'characterization', filename)
                    dfData.to_csv(filepath, index=False)
                    logging.info(f"Saved final: {filepath}")
                    intGlobalTechID += 1

                boolTryToConnect = False

        except Exception as e:
            logging.error(f"Failed to connect to the Biologic: {e}")
            logging.info("Retrying in 50 seconds...")
            time.sleep(50)
            intAttempts_temp += 1

    logging.info("Finished one batch of characterization.")
    return intGlobalTechID  # return id

intGlobalTechID = 0

# First job request
intGlobalTechID = run_and_save_characterization(
    strExperimentID, strExperimentPath,
    [ocvTech_10sec, cvTech_20, cvTech_40, cvTech_60,
        cvTech_80, cvTech_100, peisTech_noOER, peisTech_OER,
        cvTech_redox, cvTech_active, ocvTech_10sec, cvTech_20,
        cvTech_40, cvTech_60, cvTech_80, cvTech_100],
    intGlobalTechID
)

intGlobalTechID = run_and_save_characterization(
    strExperimentID, strExperimentPath,
    [peisTech_noOER, peisTech_OER,
        cvTech_redox, lpTech_lsv_wOCP],
    intGlobalTechID
)

intGlobalTechID = run_and_save_characterization(
    strExperimentID, strExperimentPath,
    [ cvTech_stability, ocvTech_10sec, cvTech_20,
        cvTech_40, cvTech_60, cvTech_80, cvTech_100,
        peisTech_noOER, peisTech_OER, cvTech_redox, lpTech_lsv_wOCP],
    intGlobalTechID
)

# log the end of the experiment
logging.info("End of characterization experiment!")

#%%
# USE OPENTRONS INSTRUMENTS AND ARDUINO TO CLEAN ELECTRODE-----------------------------------------

# initialize an the arduino client
ac = Arduino() #arduino_search_string = "USB Serial")

# wash electrode
washElectrode(opentronsClient = oc,
              strLabwareName = strID_washStation,
              arduinoClient = ac)

# move to electrode tip rack
oc.moveToWell(strLabwareName = strID_electrodeTipRack,
              strWellName = 'A2',
              strPipetteName = 'p1000_single_gen2',
              strOffsetStart = 'top',
              fltOffsetX = 0.6,
              fltOffsetY = 0.5,
              intSpeed = 50)

# drop electrode tip
oc.dropTip(strLabwareName = strID_electrodeTipRack,
               strPipetteName = 'p1000_single_gen2',
               strWellName = 'A2',
               fltOffsetX = 0.6,
               fltOffsetY = 0.5,
               fltOffsetZ = 6,
               strOffsetStart = "bottom")

# close arduino
ac.connection.close()

#%%
# RINSE WELL----------------------------------------------------------------------------------

oc.moveToWell(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5,
    fltOffsetZ=2,
    intSpeed=100
)

oc.pickUpTip(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5
)

oc.moveToWell(
    strLabwareName=strID_NISreactor,
    strWellName=strWell2Test,
    strPipetteName='p1000_single_gen2',
    strOffsetStart='top',
    fltOffsetX=0.3,
    fltOffsetY=0.5,
    fltOffsetZ=-10,
    intSpeed=100
)

oc.moveToWell(
    strLabwareName=strID_NISreactor,
    strWellName=strWell2Test,
    strPipetteName='p1000_single_gen2',
    strOffsetStart='top',
    fltOffsetX=0.3,
    fltOffsetY=0.5,
    fltOffsetZ=-35,
    intSpeed=100
)

ac = Arduino()

ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=1
)

oc.moveToWell(
    strLabwareName=strID_NISreactor,
    strWellName=strWell2Test,
    strPipetteName='p1000_single_gen2',
    strOffsetStart='top',
    fltOffsetX=0.3,
    fltOffsetY=0.5,
    fltOffsetZ=-40,
    intSpeed=100
)

ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=1
)

oc.moveToWell(
    strLabwareName=strID_NISreactor,
    strWellName=strWell2Test,
    strPipetteName='p1000_single_gen2',
    strOffsetStart='top',
    fltOffsetX=0.3,
    fltOffsetY=0.5,
    fltOffsetZ=-50,
    intSpeed=100
)

ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=1
)

ac.dispense_ml(
    pumpNumber=nozzle['water'],
    volume=1
)
ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=3
)

ac.dispense_ml(
    pumpNumber=nozzle['water'],
    volume=1
)
ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=3
)

ac.dispense_ml(
    pumpNumber=nozzle['water'],
    volume=1
)
ac.dispense_ml(
    pumpNumber=nozzle['out'],
    volume=3
)


oc.moveToWell(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5,
    fltOffsetZ=10,
    intSpeed=100
)

oc.moveToWell(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5,
    fltOffsetZ=-80,
    intSpeed=100
)

oc.dropTip(
    strLabwareName=strID_electrodeTipRack,
    strWellName='B1',
    strPipetteName="p1000_single_gen2",
    strOffsetStart='top',
    fltOffsetX=0.5,
    fltOffsetY=0.5,
    fltOffsetZ=-88
)

ac.connection.close()

# home robot
oc.homeRobot()
# turn the lights off
oc.lights(False)
# %%
