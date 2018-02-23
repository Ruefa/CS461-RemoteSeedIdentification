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
    results = Required(bytes)
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
    if token == Account[username].sessionToken:
        return True
    return False

@db_session
def logout(username):
    #TODO Exception handling
    Account[username].sessionToken = None

@db_session
def addReport(username, results):
    Report(results=results, owner=Account[username])

@db_session
def getReportList(username):
    return select(x.results for x in Report if x.owner == Account[username])[:]

@db_session
def getReport(username, report):
    #TODO Use get or something here, this is bad
    return select(x.results for x in Report if x.owner == Account[username] and x.id == report)[:]

