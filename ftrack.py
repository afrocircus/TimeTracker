import ftrack_api

session = ftrack_api.session.Session(
    server_url='http://192.168.0.209',
    api_user='Natasha',
    api_key='68ec1c94-8e8f-4355-a121-d054f4af91f5'
)


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
    seqDataList.append(["Sequences", "Duration", "Bid", {'role':'style'}])
    for seq in seqList:
        shotTimes = getShotTimeDict(seq, d)
        seqTime, bidTime = getSeqTiming(shotTimes)
        seqDataList.append([str(seq), formatTime(seqTime), formatTime(bidTime), "#dc3912"])
    return seqDataList


def getShotChart(projectName, sequenceName):
    d = getProjectChildren(projectName)
    shotTimes = getShotTimeDict(sequenceName, d)
    shotDataList = []
    shotDataList.append(["Shots", "Duration", "Bid", {'role':'style'}])
    for shot in shotTimes.keys():
        time, bid = shotTimes[shot]
        shotDataList.append([str(shot), formatTime(time), formatTime(bid), "#dc3912"])
    return shotDataList


def getTaskChart(projectName, sequenceName, shotName):
    d = getProjectChildren(projectName)
    taskDict = getTaskTimeDict(sequenceName, shotName, d)
    taskDataList = []
    taskDataList.append(["Tasks", "Duration", "Bid", {'role':'style'}])
    for task in taskDict.keys():
        time = taskDict[task]['duration']
        bid = taskDict[task]['bid']
        taskDataList.append([str(taskDict[task]['task']), formatTime(time), formatTime(bid), "#dc3912"])
    return taskDataList


def getShotTimeDict(seq, d):
    shotTimes = {}
    seqName = '%s/Sequence' % seq
    if d.has_key(seqName):
        shotTimes = getShotTiming(d[seqName])
    else:
        for key in d.keys():
            if 'Episode' in key:
                shotDict = getDict(seqName, d[key])
                shotTimes = getShotTiming(shotDict)
    return shotTimes


def getTaskTimeDict(seq, shot, d):
    taskTimes = {}
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
            taskDict['duration'] = taskTime(n)
            taskDict['user'] = 'Natasha'
            taskDict['bid'] = n['bid']
            taskDictMain[n['name']] = taskDict
            d[key] = taskDictMain
        else:
            createJson(n, d[key])
    return d


def taskTime(task):
    tt = 0
    for timelog in task['timelogs']:
        tt += timelog['duration']
    return tt


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
    for key in d.keys():
        totalTime = 0
        bidTime = 0
        taskDict = d[key]
        for task in taskDict.keys():
            if len(task.split('/')) == 1: # Making sure we're dealing with a task.
                totalTime = totalTime + float(taskDict[task]['duration'])
                bidTime = bidTime + float(taskDict[task]['bid'])
        shot = key.split('/')[0]
        shotTiming[shot] = (totalTime, bidTime)
    return shotTiming


def getSeqTiming(d):
    totalTime = 0
    bidTime = 0
    for shot in d.keys():
        time, bid = d[shot]
        totalTime = totalTime + time
        bidTime = bidTime + bid
    return totalTime, bidTime


def formatTime(seconds):
    h = m = s = 0
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return h
