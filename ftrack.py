import ftrack_api
import os
import csv
import xlsxwriter
import glob
import traceback


# setup environment
try:
    import config
    session = ftrack_api.Session(
        server_url=config.server_url,
        api_key=config.api_key,
        api_user=config.api_user
    )
except:
    print traceback.format_exc

def getProjects():
    projects = session.query('Project').all()
    projectNames = [project['name'] for project in projects]
    return projectNames


def getSequences(projectName):
    sequences = session.query('Sequence where project.name is %s' % projectName).all()
    sequenceNames = [sequence['name'] for sequence in sequences]
    return sequenceNames


def getShots(projectName, sequenceName):
    shots = session.query('Shot where project.name is %s and parent.name is %s' % (projectName, sequenceName)).all()
    shotNames = [shot['name'] for shot in shots]
    return shotNames


def getProjectChildren(projectName):
    project = session.query('Project where name is %s' % projectName).one()
    d = {}
    for child in project['children']:
        d = createJson(child, d)
    return d


def getSequenceChart(projectName):
    d = getProjectChildren(projectName)
    seqList = getSequenceList([], d)
    seqDataList = []
    seqDataList.append(["Sequences", "Actual", "Bid", {'role':'style'}])
    seqUserList = [["User", "Days"]]
    userDict = {}
    for seq in seqList:
        shotTimes, userTimes = getShotTimeDict(seq, d)
        seqTime, bidTime = getSeqTiming(shotTimes)
        seqDataList.append([str(seq), formatTime(seqTime), formatTime(bidTime), "#dc3912"])
        for key in userTimes.keys():
            if userDict.has_key(key):
                userDict[key] += userTimes[key]
            else:
                userDict[key] = userTimes[key]
    for user in userDict.keys():
        seqUserList.append([user, formatTime(userDict[user])])
    return seqDataList, seqUserList


def getShotChart(projectName, sequenceName):
    d = getProjectChildren(projectName)
    shotTimes, userTimes = getShotTimeDict(sequenceName, d)
    shotDataList = []
    shotDataList.append(["Shots", "Actual", "Bid", {'role':'style'}])
    for shot in shotTimes.keys():
        time, bid = shotTimes[shot]
        shotDataList.append([str(shot), formatTime(time), formatTime(bid), "#dc3912"])
    userDataList = [["User", "Days"]]
    for user in userTimes.keys():
        userDataList.append([user, formatTime(userTimes[user])])
    return shotDataList, userDataList


def getTaskChart(projectName, sequenceName, shotName):
    d = getProjectChildren(projectName)
    taskDict = getTaskTimeDict(sequenceName, shotName, d)
    taskDataList = []
    taskUserList = []
    taskDataList.append(["Tasks", "Actual", "Bid", {'role':'style'}])
    taskUserList.append(["User", "Days"])
    userDict = {}
    for task in taskDict.keys():
        time = taskDict[task]['duration']
        bid = taskDict[task]['bid']
        taskDataList.append([str(taskDict[task]['task']), formatTime(time), formatTime(bid), "#dc3912"])
        user = taskDict[task]['user']
        if userDict.has_key(user):
            userDict[user] += time
        else:
            userDict[user] = time
    for key in userDict.keys():
        taskUserList.append([key, formatTime(userDict[key])])
    return taskDataList, taskUserList


def getShotTimeDict(seq, d):
    shotTimes = {}
    userTimes = {}
    seqName = '%s/Sequence' % seq
    if d.has_key(seqName):
        shotTimes, userTimes = getShotTiming(d[seqName])
    else:
        for key in d.keys():
            if 'Episode' in key:
                shotDict = getDict(seqName, d[key])
                shotTimes, userTimes = getShotTiming(shotDict)
    return shotTimes, userTimes


def getTaskTimeDict(seq, shot, d):
    taskDict = {}
    seqName = '%s/Sequence' % seq
    shotName = '%s/Shot' % shot
    if d.has_key(seqName):
        shotDict = d[seqName]
        taskDict = shotDict[shotName]
    else:
        for key in d.keys():
            if 'Episode' in key:
                shotDict = getDict(seqName, d[key])
                taskDict = shotDict[shotName]
    return taskDict


def createJson(node, d):
    key = '%s/%s' % (node['name'], node['object_type']['name'])
    d[key] = {}
    taskDictMain = {}
    for n in node['children']:
        if n['object_type']['name'] == 'Task':
            taskDict = {}
            taskDict['task'] = n['name']
            taskDict['duration'], taskDict['user'] = taskTime(n)
            taskDict['bid'] = n['bid']
            taskDictMain[n['name']] = taskDict
            d[key] = taskDictMain
        else:
            createJson(n, d[key])
    return d


def taskTime(task):
    tt = 0
    userid = ''
    user = {}
    for timelog in task['timelogs']:
        tt += timelog['duration']
        userid = timelog['user_id']
    try:
        user = session.query('User where id is %s' % userid).one()
    except:
        user['username'] = ''

    return tt, user['username']


def getDict(ref, d):
    if isinstance(d, dict):
        for key in d.keys():
            if ref == key:
                return d[key]


def getSequenceList(seqList, d):
    for key in d.keys():
        keyParts = key.split('/')
        if keyParts[-1] == 'Sequence':
            seqList.append(keyParts[0])
        if isinstance(d[key], dict):
            getSequenceList(seqList, d[key])
    return seqList


def getShotTiming(d):
    shotTiming = {}
    userTiming = {}
    for key in d.keys():
        totalTime = 0
        bidTime = 0
        taskDict = d[key]
        for task in taskDict.keys():
            if len(task.split('/')) == 1: # Making sure we're dealing with a task.
                totalTime = totalTime + float(taskDict[task]['duration'])
                bidTime = bidTime + float(taskDict[task]['bid'])
                user = taskDict[task]['user']
                if userTiming.has_key(user):
                    userTiming[user] += taskDict[task]['duration']
                else:
                    userTiming[user] = taskDict[task]['duration']
        shot = key.split('/')[0]
        shotTiming[shot] = (totalTime, bidTime)
    return shotTiming, userTiming


def getSeqTiming(d):
    totalTime = 0
    bidTime = 0
    for shot in d.keys():
        time, bid = d[shot]
        totalTime = totalTime + time
        bidTime = bidTime + bid
    return totalTime, bidTime


def formatTime(seconds):
    h = seconds/3600
    d = h/8
    return round(d, 2)


def exportCVSData(project):
    d = getProjectChildren(project)
    sequences = getSequences(project)
    exportDir = '/data/work01/Documents/exportCSV'
    if not os.path.exists(exportDir):
        os.makedirs(exportDir)
    for sequence in sequences:
        dataList = formatData(sequence, d)
        writeToCVS(project, sequence, exportDir, dataList)
    exportFile = consolidateCVS(exportDir, project)
    return exportFile


def formatData(sequence, d):
    shotTimes, userTimes = getShotTimeDict(sequence, d)
    taskList = set()
    shotTaskTimeDict = {}
    mainShotDict = {}
    for key in shotTimes:
        shotTaskTimeDict[key] = getTaskTimeDict(sequence, key, d)
        for task in shotTaskTimeDict[key].keys():
            taskList.add(task)

    for key in shotTimes:
        tempDict = {}
        taskTimes = shotTaskTimeDict[key]
        tempDict['total'] = shotTimes[key]
        for task in taskList:
            if taskTimes.has_key(task):
                tempDict[task] = (taskTimes[task]['duration'], taskTimes[task]['bid'])
            else:
                tempDict[task] = (0.0, 0.0)
        mainShotDict[key] = tempDict

    tmpList = ['', 'total', 'total', 'total']
    for task in taskList:
        tmpList.extend([task, task, task])
    dataList = []
    dataList.append(tmpList)
    titles = ['Shots', 'Actual (days)', 'Bid (days)', 'Under/Over (%)']

    for task in taskList:
        titles.append('Actual (days)')
        titles.append('Bid (days)')
        titles.append('Under/Over (%)')
    dataList.append(titles)
    for key in mainShotDict.keys():
        shotList = []
        shotList.append(key)
        shotTime = mainShotDict[key]['total']
        act = formatTime(shotTime[0])
        bid = formatTime(shotTime[1])
        if bid != 0.0:
            margin = ((bid - act)/bid)*100
        else:
            margin = 0.0
        shotList.append(act)
        shotList.append(bid)
        shotList.append(round(margin, 2))
        for task in taskList:
            taskTime = mainShotDict[key][task]
            act = formatTime(taskTime[0])
            bid = formatTime(taskTime[1])
            if bid != 0.0:
                margin = ((bid - act)/bid)*100
            else:
                margin = 0.0
            shotList.append(act)
            shotList.append(bid)
            shotList.append(round(margin, 2))
        dataList.append(shotList)
    return dataList


def writeToCVS(project, sequence, exportDir, dataList):
    exportFile = os.path.join(exportDir, '%s_%s.csv' % (project, sequence))
    with open(exportFile, 'wb') as fp:
        a = csv.writer(fp)
        a.writerows(dataList)

def consolidateCVS(exportDir, project):
    workbook = xlsxwriter.Workbook('%s/%s_compiled.xlsx' % (exportDir, project))
    for filename in glob.glob('%s/*.csv' % exportDir):
        fpath, fname = os.path.split(filename)
        fsname, fext = os.path.splitext(fname)
        worksheet = workbook.add_worksheet(fsname)
        spamReader = csv.reader(open(filename, 'rb'))
        cell_format = workbook.add_format()
        cell_format.set_bold()
        cell_format.set_font_color('red')
        for rowx, row in enumerate(spamReader):
            for colx, value in enumerate(row):
                if value and value[0] == '-': # To avoid error when converting str with negative value to float.
                    worksheet.set_row(rowx, None, cell_format)
                if value == "Under/Over (%)":
                    red = workbook.add_format({'color': 'red'})
                    worksheet.write_rich_string(rowx, colx, 'Under/', red, 'Over', ' (%)')
                else:
                    worksheet.write(rowx, colx, value)

    workbook.close()
    # Clear the csv files
    for filename in glob.glob('%s/*.csv' % exportDir):
        os.remove(filename)
    return '%s/%s_compiled.xlsx' % (exportDir, project)
