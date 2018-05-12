import os
import pathlib
import string
import datetime

from passHash import hashPassword, checkPassword
from randomPass import makePassword
from pony.orm import *

db = Database()
dbDirectory = pathlib.Path('/home/nvidia/RemoteSeed/DB/')
tokenLen = 16

class Account(db.Entity):
    username = PrimaryKey(bytes)
    password = Required(bytes)
    sessionToken = Optional(bytes)
    reports = Set('Report')

class Report(db.Entity):
    results = Optional(str)
    sourceImg = Optional(str)
    resultsImg = Optional(str)
    datetime = Required(datetime.datetime)
    isAnalysisDone = Required(bool)
    owner = Required(Account)

#set_sql_debug(True)

def dbInit(dbDirectory = dbDirectory):
    global db
    db.bind(provider='sqlite', filename=str(dbDirectory / 'RemoteSeedDB.sqlite'), create_db=True)
    db.generate_mapping(create_tables=True)

@db_session
def newAccount(username, password):
    username = username.lower()
    # Check if username is available
    if Account.exists(username=username):
        return False

    # If it is, make account
    Account(username=username, password=hashPassword(password))
    return True

@db_session
def login(username, password, newToken = True):
    username = username.lower()
    account = Account.get(username=username)
    if account and checkPassword(password, account.password): # Username and Password are correct
        if not account.sessionToken or newToken:
            token = os.urandom(tokenLen)
            account.sessionToken = token
        else:
            token = account.sessionToken
        return username + token
    return None

@db_session
def checkToken(username, token):
    username = username.lower()
    account = Account.get(username=username)
    if account and token and token == account.sessionToken:
        return True
    return False

@db_session
def logout(username):
    username = username.lower()
    account = Account.get(username=username)
    if account:
        account.sessionToken = None

@db_session
def changePassword(username, newPass):
    username = username.lower()
    account = Account.get(username=username)
    if account:
        account.password = hashPassword(newPass)
        return True
    return False

@db_session
def newPassword(username):
    username = username.lower()
    account = Account.get(username=username)
    if account:
        newPass = makePassword()
        account.password = hashPassword(newPass)
        return newPass
    return None

@db_session
def newReport(username, sourceImg='', resultsImg='', results='', isAnalysisDone = False):
    username = username.lower()
    r = Report(owner=Account[username], sourceImg=sourceImg, resultsImg=resultsImg, 
               isAnalysisDone=isAnalysisDone, results=results, datetime=datetime.datetime.today())
    commit()
    return r.id

@db_session
def updateReport(reportId, isAnalysisDone=None, sourceImg=None, resultsImg=None, results=None):
    r = Report.get(id=reportId)
    if r:
        if isAnalysisDone is not None:
            r.isAnalysisDone = isAnalysisDone
        if sourceImg:
            r.sourceImg = sourceImg
        if resultsImg:
            r.resultsImg = resultsImg
        if results:
            r.results = results
        return True
    return False

@db_session
def getReportList(username):
    username = username.lower()
    u = Account.get(username=username)
    return select(x for x in Report if x.owner == u)[:]

@db_session
def getReport(report):
    return Report.get(id=report)

@db_session
def deleteReport(reportID):
    r = Report.get(id=reportID)
    if r:
        r.delete()
        return True
    return False

@db_session
def deleteAllReports(username):
    username = username.lower()
    u = Account.get(username=username)
    delete(r for r in Report if r.owner == u)

@db_session
def deleteAccount(username):
    username = username.lower()
    acct = Account.get(username=username)
    if acct:
        acct.delete()
        return True
    return False


