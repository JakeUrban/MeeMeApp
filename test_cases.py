import main
import nose
import arrow
import datetime

def generateData(numOfDays):
    start = arrow.now().to('local').replace(hour=0, minute=0, second=0, microsecond=0)
    end = arrow.now().to('local').replace(days=+numOfDays, hour=0, minute=0, second=0, microsecond=0)
    index = 0
    dataHour = 9
    dataTuples = []
    for index in range(numOfDays):
        dataTuple = (arrow.now().to('local').replace(days=+index, hour=dataHour, minute=0, second=0, microsecond=0),
                     arrow.now().to('local').replace(days=+index, hour=dataHour+1, minute=0, second=0, microsecond=0))
        dataTuples.append(dataTuple)
        index = index + 1
        if dataHour < 20:
            dataHour = dataHour + 3
        else:
            dataHour = 0
    return start,end,dataTuples 

def test_case_1():
    """Generic test, not trying to break anything.
       Just seeing if it gives the same output as
       my own calendars would"""
    tuple1 = (arrow.get('2015-12-04T10:00:00-08:00'), arrow.get('2015-12-04T11:00:00-08:00'))
    tuple2 = (arrow.get('2015-12-04T12:00:00-08:00'), arrow.get('2015-12-04T13:00:00-08:00'))
    tuple3 = (arrow.get('2015-12-04T15:00:00-08:00'), arrow.get('2015-12-04T16:00:00-08:00'))
    tuple4 = (arrow.get('2015-12-04T17:30:00-08:00'), arrow.get('2015-12-04T18:30:00-08:00'))
        
    data = [tuple1,tuple2,tuple3,tuple4]
    start = arrow.get('2015-12-04T00:00:00-08:00')
    end = arrow.get('2015-12-10T00:00:00-08:00')
    freeTimes = str(main.get_free_times(data,start,end))
    expected = "[(<Arrow [2015-12-04T09:00:00-08:00]>, <Arrow [2015-12-04T10:00:00-08:00]>), (<Arrow [2015-12-04T11:15:00-08:00]>, <Arrow [2015-12-04T12:00:00-08:00]>), (<Arrow [2015-12-04T13:15:00-08:00]>, <Arrow [2015-12-04T15:00:00-08:00]>), (<Arrow [2015-12-04T16:15:00-08:00]>, <Arrow [2015-12-04T17:00:00-08:00]>), (<Arrow [2015-12-05T09:00:00-08:00]>, <Arrow [2015-12-05T17:00:00-08:00]>), (<Arrow [2015-12-06T09:00:00-08:00]>, <Arrow [2015-12-06T17:00:00-08:00]>), (<Arrow [2015-12-07T09:00:00-08:00]>, <Arrow [2015-12-07T17:00:00-08:00]>), (<Arrow [2015-12-08T09:00:00-08:00]>, <Arrow [2015-12-08T17:00:00-08:00]>), (<Arrow [2015-12-09T09:00:00-08:00]>, <Arrow [2015-12-09T17:00:00-08:00]>), (<Arrow [2015-12-10T09:00:00-08:00]>, <Arrow [2015-12-10T17:00:00-08:00]>)]"
    assert freeTimes == expected

def test_case_2():
    """Same-day meeting (This was a bug previously)"""
    start,end,data = generateData(1)
    newData = [(data[0][0].replace(days=+1), data[0][1].replace(days=+1))]
    start = start.replace(days=+1)
    tuple1 = (arrow.now().to('local').replace(days=+1, hour=10, minute=0, second=0, microsecond=0),
                arrow.now().to('local').replace(days=+1, hour=17, minute=0, second=0, microsecond=0))
    expected = "[" + str(tuple1) + "]"
    freeTimes = str(main.get_free_times(newData,start,end))
    assert freeTimes == expected

def test_case_3():
    """End time same as start time of next busy time"""
    start,end,data = generateData(3)
    #(<Arrow [2015-12-03T09:00:00-08:00]>, <Arrow [2015-12-03T10:00:00-08:00]>), (<Arrow [2015-12-04T12:00:00-08:00]>, <Arrow [2015-12-04T13:00:00-08:00]>), (<Arrow [2015-12-05T15:00:00-08:00]>, <Arrow [2015-12-05T16:00:00-08:00]>)]
    newData = [ (data[0][0], data[0][1]), (data[1][0].replace(days=-1, hour=10), data[1][1].replace(days=-1)), (data[2][0],data[2][1]) ]
    tuple1 = (arrow.now().to('local').replace(hour=13, minute=15, second=0, microsecond=0),
              arrow.now().to('local').replace(hour=17, minute=0, second=0, microsecond=0))
    tuple2 = (arrow.now().to('local').replace(days=+1, hour=9, minute=0, second=0, microsecond=0),
              arrow.now().to('local').replace(days=+1, hour=17, minute=0, second=0, microsecond=0))
    tuple3 = (arrow.now().to('local').replace(days=+2, hour=9, minute=0, second=0, microsecond=0), 
              arrow.now().to('local').replace(days=+2, hour=15, minute=0, second=0, microsecond=0))
    tuple4 = (arrow.now().to('local').replace(days=+2, hour=16, minute=15, second=0, microsecond=0),
              arrow.now().to('local').replace(days=+2, hour=17, minute=0, second=0, microsecond=0))
    tuple5 = (arrow.now().to('local').replace(days=+3, hour=9, minute=0, second=0, microsecond=0),
              arrow.now().to('local').replace(days=+3, hour=17, minute=0, second=0, microsecond=0))
    expected = str([tuple1,tuple2,tuple3,tuple4,tuple5])
    print(expected)
    freeTimes = str(main.get_free_times(newData,start,end))
    print(freeTimes)
    assert freeTimes == expected
