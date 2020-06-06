"""
The "Hourly Income" Plugin
fork from original by Blacky_BPG
"""

import l10n
import functools
import myNotebook as nb

_ = functools.partial(l10n.Translations.translate, context=__file__)

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
import sys
import time
from l10n import Locale

this = sys.modules[__name__]  # For holding module globals

try:
    from config import config
except ImportError:
    config = dict()

APP_VERSION = "20.06.06_b2135"

CFG_EARNINGS = "EarningSpeed_earnings"
CFG_DOCKINGS = "EarningSpeed_dockings"
CFG_TIME = "EarningSpeed_time"
CFG_DESIGN = "theme"
COLOR_RED = ("#AD1616", "#FF4040", "#FF4040")
COLOR_NORM = ("#000000", "#80FFFF", "#80FFFF")


class Transaction(object):
    """
    Represents a transaction
    """
    earnings = 0.0
    time = 0
    is_docking_event = 0.0


class HourlyIncome(object):
    """
    The main class for the hourlyincome plugin
    """
    speed_widget = None
    rate_widget = None
    earned_widget = None
    single_widget = None
    att_loockup = 0
    saved_earnings = 0
    saved_docking = 0
    saved_time = 0
    start_time = 0
    appdesign = 0
    transactions = []

    def reset(self):
        """
        Reset button pressed
        """
        self.transactions = []
        self.att_loockup = 0
        self.saved_earnings = 0
        self.saved_docking = 0
        self.saved_time = 0
        self.start_time = 0
        self.update_window()

    def load(self):
        """
        Load saved earnings, saved dockings and saved gametime from config
        """
        if config.getint(CFG_DESIGN):
            self.appdesign = config.getint(CFG_DESIGN)
        else:
           self.appdesign = 0

        saved = config.get(CFG_EARNINGS)
        if not saved:
            self.saved_earnings = 0.0
        else:
            self.saved_earnings = float(saved)

        savedD = config.get(CFG_DOCKINGS)
        if not savedD:
            self.saved_docking = 0.0
        else:
            self.saved_docking = float(savedD)

        savedT = config.get(CFG_TIME)
        if not savedT:
            self.saved_time = 0.0
        else:
            self.saved_time = float(savedT)

    def save(self):
        """
        Save the saved earnings to config
        """
        config.set(CFG_EARNINGS, str(self.saved_earnings + self.trip_earnings()))
        config.set(CFG_DOCKINGS, str(self.saved_docking + self.dockings()))
        config.set(CFG_TIME, str(self.saved_time + self.sincetime()))

    def start_data(self, totaltime):
        """
        """
        self.saved_time = totaltime / 3600
        self.update_window()
        self.save()

    def transaction(self, earnings):
        """
        Record a transaction
        """
        if self.start_time == 0:
            self.start_time = time.time()

        data = Transaction()
        data.earnings = earnings
        data.is_docking_event = 0.0
        data.time = time.time()
        self.transactions.append(data)
        self.update_window()
        self.save()

    def register_docking(self):
        """
        Register on docked state
        """
        if self.start_time == 0:
            self.start_time = time.time()

        if self.att_loockup > 0:
            self.update_window()
            self.save()
        else:
            data = Transaction()
            data.earnings = 0.0
            data.is_docking_event = 1.0
            data.time = time.time()
            self.transactions.append(data)
            self.update_window()
            self.save()

    def starttime(self):
        """
        start timer for daily statistics
        """
        self.start_time = time.time()
        self.update_window()

    def loockup(self,onoff):
        """
        dont log first docking on game load with this function
        """
        self.att_loockup = onoff
        
    def sincetime(self):
        """
        """
        if self.start_time > 0:
            return (time.time() - self.start_time) / 3600
        else:
            return 1

    def trip_earnings(self):
        """
        Measure how much we've earned
        :return sum of earnings for trip:
        """
        return sum([x.earnings for x in self.transactions])

    def dockings(self):
        """
        Get the station visits rate
        :return dockings for this trip:
        """
        if len(self.transactions) > 1:
            return sum([x.is_docking_event for x in self.transactions])
        else:
            return 0

    def rate(self):
        """
        Get the station visits/hr rate
        :return dockings overall per hour:
        """
        if len(self.transactions) > 1 and self.sincetime() > 0:
            return (self.saved_docking + self.dockings()) / (self.saved_time + self.sincetime())
        elif self.saved_docking > 0:
            return self.saved_docking / self.saved_time
        else:
            return 0

    def ratenow(self):
        """
        Get the station visits/hr rate
        :return dockings for this trip per hour:
        """
        if len(self.transactions) > 1 and self.sincetime() > 0:
            return self.dockings() / self.sincetime()
        else:
            return 0.0

    def speed(self):
        """
        Get the earning speed in Cr/hr
        :return earnings overall per hour:
        """
        if len(self.transactions) > 1 and self.sincetime() > 0:
            return (self.saved_earnings + self.trip_earnings()) / (self.saved_time + self.sincetime())
        elif self.saved_earnings > 1:
            return self.saved_earnings / self.saved_time
        else:
            return 0

    def speednow(self):
        """
        Get the earning speed in Cr/hr
        :return earnings for trip per hour:
        """
        if len(self.transactions) > 1 and self.sincetime() > 0:
            return self.trip_earnings() / self.sincetime()
        else:
            return 0.0

    def update_window(self):
        """
        Update the EDMC window
        """
        self.update_single()
        self.update_earned()
        self.update_transaction_rate()
        self.update_hourlyincome()

    def update_transaction_rate(self):
        """
        Set the transaction rate rate in the EDMC window
        """
        msg = " {}".format(Locale.stringFromNumber(self.rate(), 2))
        self.rate_widget["foreground"] = COLOR_NORM[self.appdesign]
        self.rate_widget.after(0, self.rate_widget.config, {"text": msg})

        msgnow = "  {}  |".format(Locale.stringFromNumber(self.ratenow(), 2))
        self.ratenow_widget["foreground"] = COLOR_NORM[self.appdesign]
        self.ratenow_widget.after(0, self.ratenow_widget.config, {"text": msgnow})

    def update_hourlyincome(self):
        """
        Set the transaction speed rate in the EDMC window
        """
        msg = " {}".format(Locale.stringFromNumber(self.speed(), 2))
        if self.speed() > 0:
            self.speed_widget["foreground"] = COLOR_NORM[self.appdesign]
        else:
            self.speed_widget["foreground"] = COLOR_RED[self.appdesign]

        self.speed_widget.grid(row=1, column=2, sticky=tk.E)
        self.speed_widget.after(0, self.speed_widget.config, {"text": msg})

        msgnow = "  {}  |".format(Locale.stringFromNumber(self.speednow(), 2))
        if self.speednow() > 0:
            self.speednow_widget["foreground"] = COLOR_NORM[self.appdesign]
        else:
            self.speednow_widget["foreground"] = COLOR_RED[self.appdesign]

        self.speednow_widget.grid(row=1, column=1, sticky=tk.E)
        self.speednow_widget.after(0, self.speednow_widget.config, {"text": msgnow})

    def update_earned(self):
        """
        Set the transaction sum in the EDMC window
        """
        msg = "  {}".format(Locale.stringFromNumber(self.trip_earnings() + self.saved_earnings, 0))
        self.earned_widget["foreground"] = COLOR_NORM[self.appdesign]
        self.earned_widget.after(0, self.earned_widget.config, {"text": msg})

    def update_single(self):
        """
        Set the transaction speed rate for trip in the EDMC window
        """
        msg = "{}".format(Locale.stringFromNumber(self.trip_earnings(), 0))
        if self.trip_earnings() > 0:
            self.single_widget["foreground"] = COLOR_NORM[self.appdesign]
        else:
            self.single_widget["foreground"] = COLOR_RED[self.appdesign]

        self.single_widget.grid(row=2, column=1, sticky=tk.E, columnspan=2)
        self.single_widget.after(0, self.single_widget.config, {"text": msg})


def prefs_changed(cmdr, is_beta):
    hourlyincome = this.hourlyincome
    hourlyincome.appdesign = config.getint(CFG_DESIGN)
    hourlyincome.update_window()

def plugin_start3(plugin_dir):
    hourlyincome = HourlyIncome()
    hourlyincome.load()
    this.hourlyincome = hourlyincome

def plugin_start():
    hourlyincome = HourlyIncome()
    hourlyincome.load()
    this.hourlyincome = hourlyincome

def plugin_app(parent):
    """
    Create a pair of TK widgets for the EDMC main window
    """
    hourlyincome = this.hourlyincome

    frame = tk.Frame(parent)

    hourlyincome.rate_widget = tk.Label(frame, text="", justify=tk.RIGHT)
    hourlyincome.rate_widget.grid(row=0, column=2, sticky=tk.E)
    rate_label = tk.Label(frame, text=_("Dock rate:").encode('utf-8'), justify=tk.LEFT)
    rate_label.grid(row=0, column=0, sticky=tk.W)
    rateT_label = tk.Label(frame, text=_("p.Hr").encode('utf-8'), justify=tk.LEFT)
    rateT_label.grid(row=0, column=4, sticky=tk.W)

    hourlyincome.ratenow_widget = tk.Label(frame, text="", justify=tk.RIGHT)
    hourlyincome.ratenow_widget.grid(row=0, column=1, sticky=tk.E)

    hourlyincome.speed_widget = tk.Label(frame, text="", justify=tk.RIGHT)
    hourlyincome.speed_widget.grid(row=1, column=2, sticky=tk.E)
    speed_label = tk.Label(frame, text=_("Average:").encode('utf-8'), justify=tk.LEFT)
    speed_label.grid(row=1, column=0, sticky=tk.W)
    speedT_label = tk.Label(frame, text=_("Cr/hr").encode('utf-8'), justify=tk.LEFT)
    speedT_label.grid(row=1, column=4, sticky=tk.W)

    hourlyincome.speednow_widget = tk.Label(frame, text="", justify=tk.RIGHT)
    hourlyincome.speednow_widget.grid(row=1, column=1, sticky=tk.E)

    hourlyincome.single_widget = tk.Label(frame, text="", justify=tk.RIGHT)
    hourlyincome.single_widget.grid(row=2, column=1, sticky=tk.E, columnspan=2)
    single_label = tk.Label(frame, text=_("Earnings:").encode('utf-8'), justify=tk.LEFT)
    single_label.grid(row=2, column=0, sticky=tk.W)
    singleT_label = tk.Label(frame, text="Cr", justify=tk.LEFT)
    singleT_label.grid(row=2, column=4, sticky=tk.W)

    hourlyincome.earned_widget = tk.Label(frame, text="", justify=tk.RIGHT)
    hourlyincome.earned_widget.grid(row=3, column=1, sticky=tk.E, columnspan=2)
    earned_label = tk.Label(frame, text=_("Cash holding:").encode('utf-8'), justify=tk.LEFT)
    earned_label.grid(row=3, column=0, sticky=tk.W)
    earnedT_label = tk.Label(frame, text="Cr", justify=tk.LEFT)
    earnedT_label.grid(row=3, column=4, sticky=tk.W)

    """
    reset_btn = tk.Button(frame, text="Reset", command=hourlyincome.reset)
    reset_btn.grid(row=3, column=1, sticky=tk.W)
    """

    frame.columnconfigure(0, weight=0)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, weight=1)
    frame.columnconfigure(3, weight=0)
    frame.grid_columnconfigure(1, minsize=95)
    frame.grid_columnconfigure(2, minsize=95)

    this.spacer = tk.Frame(frame)
    hourlyincome.update_window()
    return frame


def dashboard_entry(cmdr, is_beta, entry):
    this.hourlyincome.update_window()


def journal_entry(cmdr, is_beta, system, station, entry, state):
    """
    Process a journal event
    :param cmdr:
    :param system:
    :param station:
    :param entry:
    :param state:
    :return:
    """
    if "event" in entry:
        # ! trading
        if "Shutdown" in entry["event"]:
            this.hourlyincome.save()
            this.hourlyincome.reset()
            this.hourlyincome.load()
        elif "LoadGame" in entry["event"]:
            this.hourlyincome.saved_earnings = entry["Credits"]
            this.hourlyincome.starttime()
            this.hourlyincome.loockup(1)
        elif "Loadout" in entry["event"]:
            this.hourlyincome.loockup(0)
        elif "Statistics" in entry["event"]:
            this.hourlyincome.start_data(entry["Exploration"]["Time_Played"])
        elif "MarketSell" in entry["event"]:
            this.hourlyincome.transaction(entry["TotalSale"])
        elif "MarketBuy" in entry["event"]:
            this.hourlyincome.transaction(-entry["TotalCost"])
        elif "BuyTradeData" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        # ! refuel/repair/restock
        elif "BuyAmmo" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        elif "BuyDrones" in entry["event"]:
            this.hourlyincome.transaction(-entry["TotalCost"])
        elif "SellDrones" in entry["event"]:
            this.hourlyincome.transaction(entry["TotalSale"])
        elif "RefuelAll" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        elif "RefuelPartial" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        elif "Repair" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        elif "RepairAll" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        elif "RestockVehicle" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        # ! shipyard/outfitting/engineering
        elif "ModuleBuy" in entry["event"]:
            this.hourlyincome.transaction(-entry["BuyPrice"])
            if "SellItem" in entry:
                this.hourlyincome.transaction(entry["SellPrice"])
        elif "ModuleSell" in entry["event"]:
            this.hourlyincome.transaction(entry["SellPrice"])
        elif "ModuleSellRemote" in entry["event"]:
            this.hourlyincome.transaction(entry["SellPrice"])
        elif "FetchRemoteModule" in entry["event"]:
            this.hourlyincome.transaction(-entry["TransferCost"])
        elif "ShipyardBuy" in entry["event"]:
            this.hourlyincome.transaction(-entry["ShipPrice"])
            if "SellOldShip" in entry:
                this.hourlyincome.transaction(entry["SellPrice"])
        elif "ShipyardSell" in entry["event"]:
            this.hourlyincome.transaction(entry["ShipPrice"])
        elif "ShipyardTransfer" in entry["event"]:
            this.hourlyincome.transaction(-entry["TransferPrice"])
        elif "EngineerContribution" in entry["event"] and "Credits" in entry["Type"]:
            this.hourlyincome.transaction(-entry["Quantity"])
        # ! fees
        elif "PayBounties" in entry["event"]:
            this.hourlyincome.transaction(-entry["Amount"])
        elif "PayFines" in entry["event"]:
            this.hourlyincome.transaction(-entry["Amount"])
        elif "PayLegacyFines" in entry["event"]:
            this.hourlyincome.transaction(-entry["Amount"])
        # ! combat
        elif "RedeemVoucher" in entry["event"]:
            this.hourlyincome.transaction(entry["Amount"])
        # ! exploration
        elif "BuyExplorationData" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        elif "SellExplorationData" in entry["event"]:
            this.hourlyincome.transaction(entry["TotalEarnings"])
        # ! missions/community goals/search and rescue
        elif "CommunityGoalReward" in entry["event"]:
            this.hourlyincome.transaction(entry["Reward"])
        elif "SearchAndRescue" in entry["event"]:
            this.hourlyincome.transaction(entry["Reward"])
        elif "MissionCompleted" in entry["event"]:
            if "Dontation" in entry:
                this.hourlyincome.transaction(-entry["Dontation"])
            else:
                this.hourlyincome.transaction(entry["Reward"])
        # ! npc crew
        elif "CrewHire" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        elif "NpcCrewPaidWage" in entry["event"]:
            this.hourlyincome.transaction(-entry["Amount"])
        # ! rebuy
        elif "SellShipOnRebuy" in entry["event"]:
            this.hourlyincome.transaction(entry["ShipPrice"])
        elif "Resurrect" in entry["event"]:
            this.hourlyincome.transaction(-entry["Cost"])
        # ! powerplay
        elif "PowerplayFastTrack" in entry["event"]:
            this.hourlyincome.transaction(-entry["cost"])
        elif "PowerplaySalary" in entry["event"]:
            this.hourlyincome.transaction(entry["Amount"])
        # ! is_docking_event
        elif "Docked" in entry["event"]:
            this.hourlyincome.register_docking()

        this.hourlyincome.update_window()
