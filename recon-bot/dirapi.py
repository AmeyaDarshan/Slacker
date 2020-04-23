import schedule
import time
import os
import pymongo
import json
from slacker import Slacker
import requests

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["dirscan"]
col = db["domains"]

def scanDirs(domain):
    if "http://" in domain:
        filename = str(time.time())
        os.system("touch /tmp/" + filename)
        os.system("python3 /Users/prey4/Pentesting/dirsearch/dirsearch.py -u " + domain + " --json-report=/tmp/" + filename + " -e * --threads 200 -b")
        with open("/tmp/" + filename, 'r') as f:
            results = json.load(f)
            paths = []
            for result in results[domain + ":80/"]:
                if result["status"] not in [400]:
                    paths.append(result["path"])
            col.insert({"domain": domain, "paths": paths}, check_keys = False)
        os.remove("/tmp/" + filename)
    elif "https://" in domain:
        filename = str(time.time())
        os.system("touch /tmp/" + filename)
        os.system("python3 /Users/prey4/Pentesting/dirsearch/dirsearch.py -u " + domain + " --json-report=/tmp/" + filename + " -e * --threads 200 -b")
        with open("/tmp/" + filename, 'r') as f:
            results = json.load(f)
            paths = []
            for result in results[domain + ":443/"]:
                if result["status"] not in [400]:
                    paths.append(result["path"])
            col.insert({"domain": domain, "paths": paths}, check_keys = False)
        os.remove("/tmp/" + filename)

class DirAlert:
    def __init__(self, domain):
        self.domain = domain
        scanDirs(self.domain)
        self.createAlerts()
        while True:
            schedule.run_pending()

    def compareResults(self):
        if "http://" in self.domain:
            oldPaths = dict()
            for x in col.find({"domain": self.domain}, {"_id": 0, "paths": 1}):
                oldPaths = x['paths']
            filename = str(time.time())
            os.system("touch /tmp/" + filename)
            os.system("python3 /Users/prey4/Pentesting/dirsearch/dirsearch.py -u " + self.domain + " --json-report=/tmp/" + filename + " -e * --threads 200 -b")
            with open("/tmp/" + filename, 'r') as f:
                results = json.load(f)
                newPaths = []
                for result in results[self.domain + ":80/"]:
                    if result["status"] not in [400]:
                        newPaths.append(result["path"])
            os.remove("/tmp/" + filename)
        elif "https://" in self.domain:
            oldPaths = dict()
            for x in col.find({"domain": self.domain}, {"_id": 0, "paths": 1}):
                oldPaths = x['paths']
            filename = str(time.time())
            os.system("touch /tmp/" + filename)
            os.system("python3 /Users/prey4/Pentesting/dirsearch/dirsearch.py -u " + self.domain + " --json-report=/tmp/" + filename + " -e * --threads 200 -b")
            with open("/tmp/" + filename, 'r') as f:
                results = json.load(f)
                newPaths = []
                for result in results[self.domain + ":443/"]:
                    if result["status"] not in [400]:
                        newPaths.append(result["path"])
            os.remove("/tmp/" + filename)
        if newPaths is not oldPaths:
            col.update_one({"domain": self.domain}, {"$set": {"paths": newPaths}})
            for path in list(set(newPaths) - set(oldPaths)):
                requests.post("https://hooks.slack.com/services/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", json = {"text": path})
        
    def createAlerts(self):
        #schedule.every().day.at("10:30").do(self.compareResults(domain))
        schedule.every(1).minutes.do(self.compareResults)