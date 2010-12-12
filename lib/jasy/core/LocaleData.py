#
# Jasy - JavaScript Tooling Refined
# Copyright 2010 Sebastian Werner
#

import logging, os, json, xml.etree.ElementTree
from jasy.core.File import *
from jasy.core.Profiler import *
import jasy.core.Info



def store(locale):
    Parser(locale).export()
    
    
    
class Parser():
    def __init__(self, locale):
        pstart()
        logging.info("Preparing locale %s" % locale)
        splits = locale.split("_")
        
        # Store for internal usage
        self.__locale = locale
        self.__language = splits[0]
        self.__territory = splits[1] if len(splits) > 1 else None

        # This will hold all data extracted data
        self.__data = {}

        # Add info section
        self.__data["info"] = {
            "locale" : self.__locale,
            "language" : self.__language,
            "territory" : self.__territory
        }
        
        # Add keys
        path = "%s.xml" % os.path.join(jasy.core.Info.cldrData("keys"), self.__language)
        tree = xml.etree.ElementTree.parse(path)
        self.__data["key"] = {
            "short" : { key.get("type"): key.text for key in tree.findall("/keys/short/key") },
            "full" : { key.get("type"): key.text for key in tree.findall("/keys/full/key") }
        }
        
        
        # Add main CLDR data: Fallback chain for locales
        main = jasy.core.Info.cldrData("main")
        while True:
            path = "%s.xml" % os.path.join(main, locale)
            tree = xml.etree.ElementTree.parse(path)

            self.__addDisplayNames(tree)
            self.__addDelimiters(tree)
            self.__addCalendars(tree)
            self.__addNumbers(tree)            
            
            if "_" in locale:
                locale = locale[:locale.rindex("_")]
            else:
                break
                
        # Add supplemental CLDR data
        self.__addSupplementals()

        pstop()


    def export(self):
        project = jasy.core.Info.localeProject(self.__locale)
        logging.info("Writing result...")
        pstart()
        
        writefile(os.path.join(project, "manifest.cfg"), "[main]\nname = cldr\nkind = basic\n")
        self.__exportRecurser(self.__data, "locale", project)
        pstop()


    def __exportRecurser(self, data, prefix, project):
        for key in data:
            value = data[key]
            
            firstIsDict = False
            for childKey in value:
                if type(value[childKey]) == dict:
                    firstIsDict = True
                    break
            
            if firstIsDict:
                name = "%s.%s" % (prefix, key)
                self.__exportRecurser(value, name, project)
            else:
                name = "%s.%s%s" % (prefix, key[0].upper(), key[1:])
                result = "// Automatically generated by Jasy\ndeclare(\"%s\", %s);" % (name, json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False))
                filename = "%s.js" % name.replace(".", os.path.sep)
                
                writefile(os.path.join(project, "src", filename), result)


    def __getStore(self, parent, name):
        """ Manages data fields """
        
        if not name in parent:
            store = {}
            parent[name] = store
        else:
            store = parent[name]

        return store
        
        
        
    def __addSupplementals(self):
        """ Converts data from supplemental folder """
        
        supplemental = jasy.core.Info.cldrData("supplemental")

        # Plurals
        path = os.path.join(supplemental, "plurals.xml")
        tree = xml.etree.ElementTree.parse(path)
        self.__data["plural"] = {}
        for item in tree.findall("plurals/pluralRules"):
            attr = item.get("locales")
            if attr != None:
                if self.__language in attr.split(" "):
                    for rule in item.findall("pluralRule"):
                        self.__data["plural"][rule.get("count")] = rule.text
        
        # Telephone Codes
        path = os.path.join(supplemental, "telephoneCodeData.xml")
        tree = xml.etree.ElementTree.parse(path)
        self.__data["phonecode"] = {}
        for item in tree.findall("telephoneCodeData/codesByTerritory"):
            territory = item.get("territory")
            for rule in item.findall("telephoneCountryCode"):
                self.__data["phonecode"][territory] = int(rule.get("code"))
                # Respect first only
                break
        
        # Postal Codes
        path = os.path.join(supplemental, "postalCodeData.xml")
        tree = xml.etree.ElementTree.parse(path)
        self.__data["postalcode"] = {}
        for item in tree.findall("postalCodeData/postCodeRegex"):
            territoryId = item.get("territoryId")
            self.__data["postalcode"][territoryId] = item.text
        
        
        # Supplemental Data
        path = os.path.join(supplemental, "supplementalData.xml")
        tree = xml.etree.ElementTree.parse(path)
        
        # :: Calendar Preference
        ordering = None
        for item in tree.findall("calendarPreferenceData/calendarPreference"):
            if item.get("territories") == "001" and ordering == None:
                ordering = item.get("ordering")
            elif self.__territory in item.get("territories").split(" "):
                ordering = item.get("ordering")
                break
        
        self.__data["calendarpref"] = { "ordering" : ordering.split(" ") }
        
        # :: Week Data
        self.__data["weekdata"] = {}
        weekData = tree.find("weekData")
        for key in ["firstDay", "weekendStart", "weekendEnd"]:
            day = None
            for item in weekData.findall(key):
                if item.get("territories") == "001" and day == None:
                    day = item.get("day")
                elif self.__territory in item.get("territories").split(" "):
                    day = item.get("day")
                    break
            
            self.__data["weekdata"][key] = day

        # :: Measurement System
        self.__data["measurement"] = {}
        measurementData = tree.find("measurementData")
        for key in ["measurementSystem", "paperSize"]:
            mtype = None
            for item in measurementData.findall(key):
                if item.get("territories") == "001" and mtype == None:
                    mtype = item.get("type")
                elif self.__territory in item.get("territories").split(" "):
                    mtype = item.get("type")
                    break

            self.__data["measurement"][key] = mtype

        
        
    def __addDisplayNames(self, tree):
        """ Adds CLDR display names section """
        
        display = self.__getStore(self.__data, "display")
        
        for key in ["languages", "scripts", "territories", "variants", "keys", "types", "measurementSystemNames"]:
            # make it a little bit shorter, there is not really any conflict potential
            if key == "measurementSystemNames":
                store = self.__getStore(display, "measurement")
            elif key == "territories":
                store = self.__getStore(display, "territory")
            else:
                # remove last character "s" to force singular
                store = self.__getStore(display, key[:-1])
                
            for element in tree.findall("/localeDisplayNames/%s/*" % key):
                if not element.get("draft"):
                    field = element.get("type")
                    if not field in store:
                        store[field] = element.text
                    
                    
    def __addDelimiters(self, tree):
        """ Adds CLDR delimiters """
        
        delimiters = self.__getStore(self.__data, "delimiter")
        
        for element in tree.findall("/delimiters/*"):
            if not element.get("draft"):
                field = element.tag
                if not field in delimiters:
                    delimiters[field] = element.text
        
        
    def __addCalendars(self, tree, key="dates/calendars"):
        """ Loops through all CLDR calendars and adds them """
        
        calendars = self.__getStore(self.__data, "calendar")
            
        for element in tree.findall("/%s/*" % key):
            if not element.get("draft"):
                self.__addCalendar(calendars, element)


    def __addCalendar(self, store, element):
        """ Adds data from a CLDR calendar section """
        
        calendar = self.__getStore(store, element.get("type"))

        # Months Widths
        if element.find("months/monthContext/monthWidth"):
            months = self.__getStore(calendar, "month")
            for child in element.findall("months/monthContext/monthWidth"):
                if not child.get("draft"):
                    format = child.get("type")
                    if not format in months:
                        months[format] = {}
                
                    for month in child.findall("month"):
                        if not month.get("draft"):
                            name = month.get("type")
                            if not name in months[format]:
                                months[format][name] = month.text


        # Day Widths
        if element.find("days/dayContext/dayWidth"):
            days = self.__getStore(calendar, "day")
            for child in element.findall("days/dayContext/dayWidth"):
                if not child.get("draft"):
                    format = child.get("type")
                    if not format in days:
                        days[format] = {}

                    for day in child.findall("day"):
                        if not day.get("draft"):
                            name = day.get("type")
                            if not name in days[format]:
                                days[format][name] = day.text


        # Quarter Widths
        if element.find("quarters/quarterContext/quarterWidth"):
            quarters = self.__getStore(calendar, "quarter")
            for child in element.findall("quarters/quarterContext/quarterWidth"):
                if not child.get("draft"):
                    format = child.get("type")
                    if not format in quarters:
                        quarters[format] = {}

                    for quarter in child.findall("quarter"):
                        if not quarter.get("draft"):
                            name = quarter.get("type")
                            if not name in quarters[format]:
                                quarters[format][name] = quarter.text
        
        
        # Date Formats
        if element.find("dateFormats/dateFormatLength"):
            dateFormats = self.__getStore(calendar, "date")
            for child in element.findall("dateFormats/dateFormatLength"):
                if not child.get("draft"):
                    format = child.get("type")
                    text = child.find("dateFormat/pattern").text
                    if not format in dateFormats:
                        dateFormats[format] = text


        # Time Formats
        if element.find("timeFormats/timeFormatLength"):
            timeFormats = self.__getStore(calendar, "time")
            for child in element.findall("timeFormats/timeFormatLength"):
                if not child.get("draft"):
                    format = child.get("type")
                    text = child.find("timeFormat/pattern").text
                    if not format in timeFormats:
                        timeFormats[format] = text
                        
                        
        # DateTime Formats
        if element.find("dateTimeFormats/availableFormats"):
            datetime = self.__getStore(calendar, "datetime")
            for child in element.findall("dateTimeFormats/availableFormats/dateFormatItem"):
                if not child.get("draft"):
                    format = child.get("id")
                    text = child.text
                    if not format in datetime:
                        datetime[format] = text
        
        
        # Fields
        if element.find("fields/field"):
            fields = self.__getStore(calendar, "field")
            for child in element.findall("fields/field"):
                if not child.get("draft"):
                    format = child.get("type")
                    for nameChild in child.findall("displayName"):
                        if not nameChild.get("draft"):
                            text = nameChild.text
                            if not format in fields:
                                fields[format] = text
                            break
                        
                        
        # Relative
        if element.find("fields/field"):
            relatives = self.__getStore(calendar, "relative")
            for child in element.findall("fields/field"):
                if not child.get("draft"):
                    format = child.get("type")
                    if child.find("relative"):
                        relativeField = self.__getStore(relatives, format)
                        for relChild in child.findall("relative"):
                            if not relChild.get("draft"):
                                pos = relChild.get("type")
                                text = relChild.text
                                if not pos in relativeField:
                                    relativeField[pos] = text
                        
                        
    def __addNumbers(self, tree):
        store = self.__getStore(self.__data, "number")
                        
        # Symbols
        symbols = self.__getStore(store, "symbol")
        for element in tree.findall("numbers/symbol/*"):
            if not element.get("draft"):
                field = element.tag
                if not field in store:
                    symbols[field] = element.text

        # Formats
        if not "format" in store:
            store["format"] = {}
                    
        for format in ["decimal", "scientific", "percent", "currency"]:
            if not format in store["format"]:
                for element in tree.findall("numbers//%sFormat/pattern" % format):
                    store["format"][format] = element.text
            
        # Currencies
        currencies = self.__getStore(store, "currency")
        for child in tree.findall("numbers/currencies/currency"):
            if not child.get("draft"):
                short = child.get("type")
                for nameChild in child.findall("displayName"):
                    if not nameChild.get("draft"):
                        text = nameChild.text
                        if not format in currencies:
                            currencies[short] = text
                        break
                