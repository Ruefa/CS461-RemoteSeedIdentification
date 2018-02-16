from pony.orm import *

db = Database()

class Account(db.Entity):
    username = PrimaryKey(bytes)
    password = Required(bytes)
    reports = Set('Report')

class Report(db.Entity):
    results = Required(bytes)
    owner = Required(Account)

db.bind(provider='sqlite', filename=':memory:')
db.generate_mapping(create_tables=True)


@db_session
def makeLogin(username, password):
    # Check if username is available
    if Account.exists(username=username):
        return False

    #TODO Probably shouldn't store pword as plaintxt
   
   # If it is, make account
    Account(username=username, password=password)
    return True

@db_session
def checkLogin(username, password):
    return Account.exists(username=username, password=password)

@db_session
def addReport(username, results):
    Report(results=results, owner=Account[username])

@db_session
def getReportList(username):
    return select(x.id for x in Account[username].reports)[:]

@db_session
def getReport(username, report):
    return select(x for x in Account[username].reports if x.id == report)

