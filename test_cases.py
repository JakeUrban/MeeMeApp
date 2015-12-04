import main
import nose
import arrow
import datetime    

def test_case_1():
    """Generic test, not trying to break anything.
       Just seeing if it gives the same output as
       my own calendars would"""
    print("In test_case_1")
    tuple1 = (arrow.get('2015-12-04T10:00:00-08:00'), arrow.get('2015-12-04T11:00:00-08:00'))
    tuple2 = (arrow.get('2015-12-04T12:00:00-08:00'), arrow.get('2015-12-04T13:00:00-08:00'))
    tuple3 = (arrow.get('2015-12-04T15:00:00-08:00'), arrow.get('2015-12-04T16:00:00-08:00'))
    tuple4 = (arrow.get('2015-12-04T17:30:00-08:00'), arrow.get('2015-12-04T18:30:00-08:00'))
        
    data = [tuple1,tuple2,tuple3,tuple4]
    print(data)
    start = arrow.get('2015-12-04T00:00:00-08:00')
    end = arrow.get('2015-12-10T00:00:00-08:00')
    print(start)
    print(end)
    freeTimes = str(main.get_free_times(data,start,end))
    expected = "[(<Arrow [2015-12-04T09:00:00-08:00]>, <Arrow [2015-12-04T10:00:00-08:00]>), (<Arrow [2015-12-04T11:15:00-08:00]>, <Arrow [2015-12-04T12:00:00-08:00]>), (<Arrow [2015-12-04T13:15:00-08:00]>, <Arrow [2015-12-04T15:00:00-08:00]>), (<Arrow [2015-12-04T16:15:00-08:00]>, <Arrow [2015-12-04T17:00:00-08:00]>), (<Arrow [2015-12-05T09:00:00-08:00]>, <Arrow [2015-12-05T17:00:00-08:00]>), (<Arrow [2015-12-06T09:00:00-08:00]>, <Arrow [2015-12-06T17:00:00-08:00]>), (<Arrow [2015-12-07T09:00:00-08:00]>, <Arrow [2015-12-07T17:00:00-08:00]>), (<Arrow [2015-12-08T09:00:00-08:00]>, <Arrow [2015-12-08T17:00:00-08:00]>), (<Arrow [2015-12-09T09:00:00-08:00]>, <Arrow [2015-12-09T17:00:00-08:00]>), (<Arrow [2015-12-10T09:00:00-08:00]>, <Arrow [2015-12-10T17:00:00-08:00]>)]"
    assert freeTimes == expected
