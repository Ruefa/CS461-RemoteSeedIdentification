import os
import string

from passHash import hashPassword, checkPassword
from randomPass import makePassword
from pony.orm import *

db = Database()
tokenLen = 16

class Account(db.Entity):
    username = PrimaryKey(bytes)
    password = Required(bytes)
    sessionToken = Optional(bytes)
    reports = Set('Report')

class Report(db.Entity):
    results = Optional(str)
    owner = Required(Account)

db.bind(provider='sqlite', filename='/home/nvidia/RemoteSeed/DB/database.sqlite', create_db=True)
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
def login(username, password):
    account = Account.get(username=username)
    if account and checkPassword(password, account.password): # Username and Password are correct
        token = os.urandom(tokenLen)
        account.sessionToken = token
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
    if account
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
def newReport(username):
    r = Report(owner=Account[username])
    commit()
    return r.id

@db_session
def addReportResults(username, reportId, results):
    r = Report[reportId]
    r.results = results

@db_session
def getReportList(username):
    return select(x.id for x in Report if x.owner == Account[username])[:]

#TODO remove username as parameter
@db_session
def getReport(username, report):
    #TODO Use get or something here, this is bad
    return select(x.results for x in Report if x.owner == Account[username] and x.id == report)[:]

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
    acct = Account.get(id=reportID)
    if acct:
        acct.delete()
        return True
    return False


