import os

from passHash import hashPassword, checkPassword
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

db.bind(provider='sqlite', filename=':memory:')
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
    return select(x.results for x in Report if x.owner == Account[username])[:]

@db_session
def getReport(username, report):
    #TODO Use get or something here, this is bad
    return select(x.results for x in Report if x.owner == Account[username] and x.id == report)[:]

