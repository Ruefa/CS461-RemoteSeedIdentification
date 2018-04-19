import os
import pathlib
import string

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
    owner = Required(Account)

db.bind(provider='sqlite', filename=str(dbDirectory/'RemoteSeedDB.sqlite'), create_db=True)
db.generate_mapping(create_tables=True)

set_sql_debug(True)


@db_session
def newAccount(username, password):
    # Check if username is available
    if Account.exists(username=username):
        return False

    # If it is, make account
    Account(username=username, password=hashPassword(password))
    return True

@db_session
def login(username, password, newToken = True):
    account = Account.get(username=username)
    if account and checkPassword(password, account.password): # Username and Password are correct
        if newToken:
            token = os.urandom(tokenLen)
            account.sessionToken = token
        else:
            token = account.sessionToken
        return username + token
    return None

@db_session
def checkToken(username, token):
    #TODO Exception handling
    account = Account.get(username=username)
    if account and token == account.sessionToken:
        return True
    return False

@db_session
def logout(username):
    #TODO Exception handling
    account = Account.get(username=username)
    if account:
        account.sessionToken = None

@db_session
def changePassword(username, newPass):
    account = Account.get(username=username)
    if account:
        account.password = hashPassword(newPass)

@db_session
def newPassword(username):
    account = Account.get(username=username)
    if account:
        newPass = makePassword
        account.password = hashPassword(newPass)
        return newPass
    return None

@db_session
def newReport(username, sourceImg='', resultsImg='', results=''):
    r = Report(owner=Account[username], sourceImg=sourceImg, resultsImg=resultsImg, results=results)
    commit()
    return r.id

@db_session
def updateReport(reportId, sourceImg='', resultsImg='', results=''):
    r = Report[reportId]
    r.sourceImg = sourceImg
    r.resultsImg = resultsImg
    r.results = results

@db_session
def getReportList(username):
    return select(x.id for x in Report if x.owner == Account[username])[:]

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
    delete(r for r in Report if r.owner == username)

@db_session
def deleteAccount(username):
    acct = Account.get(username=username)
    if acct:
        acct.delete()
        return True
    return False


