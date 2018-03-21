import sys
import threading
import queue
import db

import server
from connectionHandler import jobQueue

sys.path.append('/home/nvidia/RemoteSeed/CS461-RemoteSeedIdentification/Classifier')
from sample_analysis import run_analysis


serverThread = threading.Thread(target = server.start, daemon=True)
serverThread.start()

while True:
    img, path, user, reportID = jobQueue.get()

    results = run_analysis(img, path)
    db.addReportResults(user, reportID, results)
