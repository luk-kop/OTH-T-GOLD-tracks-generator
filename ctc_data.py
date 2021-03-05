import random
from enum import Enum


class CtcType(Enum):
    FFS = 'FRIGATE, SMALL, CORVETTE'
    MS = 'MINESWEEPER, SMALL, GENERAL'
    FF = 'FRIGATE'
    MH = 'MINEHUNTER, GENERAL'
    CA = 'HEAVY CRUISER, GUN'
    CL = 'CRUISER, LIGHT'
    CLH = 'CRUISER, LIGHT, AVIATION'
    PBS = 'PATROL BOAT, FIRE SUPPORT'
    PB = 'PATROL BOAT'
    PF = 'PATROL FRIGATE'
    DD = 'DESTROYER, GENERAL'
    DER = 'DESTROYER ESCORT, RADAR PICKET'
    DDM = 'DESTROYER, MINELAYING'
    FFG = 'FRIGATE, GUIDED MISSILE'
    MON = 'RIVER MONITOR, ASSAULT'
    BMR = 'MONITOR, RIVER'
    PR = 'PATROL CRAFT, RESCUE'
    PTA = 'TORPEDO BOAT, AIR CUSHION'
    WPG = 'PATROL COMBATANT, COAST GUARD'
    MIS = 'MISCELLANEOUS'
    MHS = 'MINEHUNTER/SWEEPER, GENERAL'

    @classmethod
    def get_random_name(cls):
        return random.choice(list(cls)).name


class CtcCategory(Enum):
    NAV = 'Surface Naval Vessel'
    MER = 'Merchant Vessel'
    FSH = 'Fishing Vessel'
    AIR = 'Aircraft'
    SUB = 'Submarine Naval Vessel'
    UNK = 'Unknown'
    LND = 'Land-based Installation/Facility'

    @classmethod
    def get_random_name(cls):
        return random.choice(list(cls)).name


class CtcFlag(Enum):
    AF = 'Afghanistan'
    AA = 'Aruba'
    AJ = 'Azerbaijan'
    BA = 'Bahrain'
    BR = 'Brazil'
    CA = 'Canada'
    CM = 'Cameroon'
    DA = 'Denmark'
    RS = 'Russia'
    HR = 'Croatia'
    CU = 'Cuba'
    DJ = 'Djibouti'
    EC = 'Ecuador'
    EG = 'Egypt'
    UV = 'Burkina'
    HA = 'Haiti'
    FR = 'France'
    FI = 'Finland'
    FG = 'French Guiana'
    JA = 'Japan'
    JO = 'Jordan'
    GR = 'Greece'
    KU = 'Kuwait'
    LG = 'Latvia'
    LH = 'Lithuania'
    LI = 'Liberia'
    PK = 'Pakistan'
    PL = 'Poland'
    OX = 'Red Cross'
    NL = 'Netherlands'
    NO = 'Norway'
    UK = 'United Kingdom'
    UP = 'Ukraine'
    US = 'United States'

    @classmethod
    def get_random_name(cls):
        return random.choice(list(cls)).name
