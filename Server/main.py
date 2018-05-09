import sys
import pathlib
import threading
import queue
import db

import server
from connectionHandler import jobQueue

sys.path.append('/home/nvidia/RemoteSeed/CS461-RemoteSeedIdentification/Classifier')
from sample_analysis import run_analysis


db.dbInit()
serverThread = threading.Thread(target = server.start, daemon=True)
serverThread.start()

while True:
    reportID, imgPath = jobQueue.get()

    resultImgPath = imgPath.parent / 'result.png'

    results = run_analysis(str(imgPath), str(resultImgPath))
    db.updateReport(reportID, isAnalysisDone=True, results=results, resultsImg=str(resultImgPath))
