#!/usr/bin/python
#
# Author: Martin Galpin (m@66laps.com)
#
# Copyright 2007 66laps Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from datetime import datetime
import os

from openmotorsport.openmotorsport import Session, Channel, Metadata, Lap
from openmotorsport.time import *

class SessionTests(unittest.TestCase):
  
  def testWriteEmpty(self):
    path = 'empty.om'    
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()
    original_doc.write(path)        
    self.assertTrue(os.path.exists(path))            
    imported_doc = Session(path)
    self.assertEquals(imported_doc, original_doc)
    os.remove(path)
    
  def testMarkersNoSectors(self):
    path = 'nosectors.om'
    session = Session()
    session.metadata = self._getSampleMeta()
    self.assertEquals(session.laps, [])
    session.add_marker(10)
    session.add_marker(20)
    self.assertEquals(session.laps, [])
    session.write(path)
    imported = Session(path)
    self.assertEquals(imported, session)
    self.assertEquals(imported.laps, [])  
    os.remove(path)
     
  def testMarkersZeroSectors(self):
    session = Session()
    session.metadata = self._getSampleMeta()
    self.assertEquals(session.laps, [])
    session.num_sectors = 0
    session.add_marker(10)
    session.add_marker(20)
    self.assertEquals(len(session.laps), 2)
    
  def testWriteWithData(self):
    path = 'test_data.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()    
    original_doc.add_channel(
      Channel(
        id=0, name='Channel 1',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1),
          data=self._getSampleData()
        )
      )
    )
    original_doc.add_channel(
      Channel(
        id=1, name='Channel 2',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1),
          data=self._getSampleData()
        )
      )
    )
    original_doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)
    for channel in imported_doc.channels: channel.timeseries.data # lazy
    self.assertEquals(original_doc, imported_doc)
    os.remove(path)
    

  def testWriteWithVariableFrequencyChannel(self):
    path = 'test_variable.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()    
    original_doc.add_channel(Channel(id=0, name='Channel 1',
      timeseries=VariableTimeSeries(data=self._getSampleData(),
                                    times=self._getSampleData())
    ))          
    original_doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)
    self.assertEquals(original_doc, imported_doc)
    os.remove(path)
    

  def testWriteWithMarkers(self):
    path = 'test_markers.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()
    original_doc.add_channel(
      Channel(
        id=0, name='Channel 1',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1),
          data=self._getSampleData()
        )
      )
    )
    original_doc.add_channel(
      Channel(
        id=1, name='Channel 2',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1),
          data=self._getSampleData()
        )
      )
    )       
    [original_doc.add_marker(m) for m in [1.0, 2.0, 3.0]]
    original_doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)
    self.assertEquals(original_doc, imported_doc)
    os.remove(path)  


  def testWriteWithSectors(self):
    path = 'test_markers.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()
    original_doc.add_channel(
      Channel(
        id=0, name='Channel 1',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1),
          data=self._getSampleData()
        )
      )
    )
    original_doc.add_channel(
      Channel(
        id=1, name='Channel 2',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1),
          data=self._getSampleData()
        )
      )
    )        
    [original_doc.add_marker(m) for m in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]]
    original_doc.num_sectors = 2
    original_doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)  
    self.assertEquals(original_doc, imported_doc)
    os.remove(path)  
  
 
  def testFailMissingMadatoryMetaInformation(self):
    path = 'test_failure.om'
    original_doc = Session()
    try:
      original_doc.write(path)
    except Exception:
      pass
    else:
      self.fail('Expected exception.')
  
      
  def testDataAppend(self):
    path = 'test_data.om'

    # test a simple two channel session with sampling interval
    session = Session()
    session.metadata = self._getSampleMeta()
    session.add_channel(
      Channel(
        id=0, name='Channel 1',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1)
        )
      )
    )
    session.add_channel(
      Channel(
        id=1, name='Channel 2',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1)
        )
      )
    )
    self.assertEquals(len(session.channels[0].timeseries), 0)
    for x in range(0, 2):
      for y in range(0, 1000):
        session.channels[x].timeseries.append(float(y))
    self.assertEquals(len(session.channels[0].timeseries), 1000)
    self.assertEquals(len(session.channels[1].timeseries), 1000)
    session.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_session = Session(path)
    self.assertEquals(session, imported_session)


    os.remove(path)
    
  def testChannelGroup(self):
    path = 'test_data.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()    
    
    # no group
    original_doc.add_channel(
      Channel(
        id=0, name='Channel 1',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1),
          data=get_data(interval=1, duration=30.0)
        )
      )
    )
    original_doc.channels.extend([
      Channel(
        id=1, name='Channel 2', group='Group 1',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1)
        )
      ),
      Channel(
        id=2, name='Channel 3', group='Group 1',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1)
        )
      )
    ])
    original_doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)
    self.assertEquals(original_doc, imported_doc)
    os.remove(path)
    
  def testLapTimesSectors(self):
    # test two complete laps
    session = Session()
    session.num_sectors = 2
    [session.add_marker(m) for m in [10.0, 20.0, 30.0, 50.0, 60.0, 70.0]]
    self.assertEquals(len(session.laps), 2)
    self.assertEquals(session.laps[0].length, 30.0)
    self.assertEquals(session.laps[0].offset, 0.0)
    self.assertEquals(session.laps[0].sectors, [10.0, 10.0])
    self.assertEquals(session.laps[1].length, 40.0)
    self.assertEquals(session.laps[1].offset, 30.0)
    self.assertEquals(session.laps[1].sectors, [20.0, 10.0])

    # test six laps, no sectors
    session = Session()
    session.num_sectors = 0
    [session.add_marker(m) for m in [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]]
    self.assertEquals(len(session.laps), 6)
    start_time = 10.0
    for index, lap in enumerate(session.laps):
      self.assertEquals(lap.offset, start_time * index)
      self.assertEquals(lap.sectors, [])

    # test one lap, partially complete second lap
    session = Session()
    session.num_sectors = 2
    [session.add_marker(m) for m in [10.0, 20.0, 30.0, 40.0]]
    self.assertEquals(len(session.laps), 2)
    self.assertEquals(session.laps[0].sectors, [10.0, 10.0])
    self.assertEquals(session.laps[0].length, 30.0)
    self.assertEquals(session.laps[0].offset, 0.0)
    self.assertEquals(session.laps[1].sectors, [10.0, None])
    self.assertEquals(session.laps[1].length, None)
    self.assertEquals(session.laps[1].offset, 30.0)

    # test one partially completed lap
    session = Session()
    session.num_sectors = 2
    [session.add_marker(m) for m in [10.0, 20.0]]
    self.assertEquals(len(session.laps), 1)
    self.assertEquals(session.laps[0].sectors, [10.0, 10.0])
    self.assertEquals(session.laps[0].length, None)
    self.assertEquals(session.laps[0].offset, 0.0)

    # test just a single lap
    session = Session()
    session.num_sectors = 2
    [session.add_marker(m) for m in [10.0, 20.0, 30.0]]
    self.assertEquals(len(session.laps), 1)
    self.assertEquals(session.laps[0].sectors, [10.0, 10.0])
    self.assertEquals(session.laps[0].length, 30.0)
    self.assertEquals(session.laps[0].offset, 0.0)
    

    # test empty session
    session = Session()
    self.assertEquals(len(session.laps), 0)

    # test one lap, no markers
    session = Session()
    [session.add_marker(m) for m in [10.0, 20.0, 30.0]]
    session.num_sectors = 0
    self.assertEquals(len(session.laps), 3)
    start_time = 10.0
    for index, lap in enumerate(session.laps):
      self.assertEquals(lap.offset, start_time * index)
      self.assertEquals(lap.sectors, [])    
    
  def testGetChannelOrGroup(self):
    channels = [
      Channel(id=1, name='Channel 1'),
      Channel(id=2, name='Channel 2'),
      Channel(id=3, name='Channel 3', group='Group 1'),
      Channel(id=4, name='Channel 4', group='Group 2'),
      Channel(id=5, name='Channel 5', group='Group 1'),
      Channel(id=6, name='Channel 5')
    ]

    session = Session()
    [session.add_channel(c) for c in channels]

    self.assertEquals(session.get_channel('Channel 1'), channels[0])
    self.assertEquals(session.get_channel('Channel 2'), channels[1])
    self.assertEquals(session.get_channel('Channel 3'), None)
    self.assertEquals(session.get_channel('Channel 3', group='Group 1'), channels[2])
    self.assertEquals(session.get_channel('Channel 4', group='Group 2'), channels[3])
    self.assertEquals(session.get_channel('Channel 5', group='Group 1'), channels[4])
    self.assertEquals(session.get_channel('Channel 5'), channels[5])
    self.assertEquals(session.get_group('Group 1'), [channels[2], channels[4]])
    self.assertEquals(session.get_group('Foo'), None)    

  def test_get_channel_by_id(self):
    channels = [
      Channel(id=1, name='Channel 1'),
      Channel(id=2, name='Channel 2'),
      Channel(id=3, name='Channel 3', group='Group 1'),
      Channel(id=4, name='Channel 4', group='Group 2')
    ]

    session = Session()
    [session.add_channel(c) for c in channels]

    self.assertEquals(session.get_channel_by_id(1), channels[0])
    self.assertEquals(session.get_channel_by_id(2), channels[1])
    self.assertEquals(session.get_channel_by_id(3), channels[2])
    self.assertEquals(session.get_channel_by_id(4), channels[3])
    self.assertEquals(session.get_channel_by_id(5), None)

  # /----------------------------------------------------------------------/    
  
  def _getSampleMeta(self):
    return Metadata(
      user = 'Michael Schumacher',
      venue = { 
        'name': 'Silverstone', 
        'configuration': 'Arena GP'
      },
      vehicle = { 
        'name': 'Mercedes MGP W01',
        'year': '2010', 
        'category': 'Formula One',
        'comments': None
      },
      date = self._getSampleDate()
    )
  
  def _getSampleData(self):
    return np.array([x * 0.1 for x in range(0, 10)], dtype=np.float32)      
  
  def _getSampleDate(self):
    # contruct a datetime object with no microseconds as these are lost when
    # converted to iso8601
    date = datetime.now()
    return datetime(date.year, date.month, date.day, date.hour, 
      date.minute, date.second)

class LapTests(unittest.TestCase):
  def test_end_time(self):
    # test basic
    session = Session()
    session.num_sectors = 0
    [session.add_marker(m) for m in [10.0, 20.0, 30.0]]
    session.add_channel(
      Channel(
        id=0, name='Channel 1',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1),
          data=get_data(interval=1, duration=30.0)
        )
      )
    )

    self.assertEquals(len(session.laps), 3)
    self.assertEquals(session.laps[0].end_time, 10.0)
    self.assertEquals(session.laps[1].end_time, 20.0)
    self.assertEquals(session.laps[2].end_time, 30.0)

    # test with incomplete lap
    session = Session()
    session.num_sectors = 0
    [session.add_marker(m) for m in [10.0, 20.0]]
    session.add_channel(
      Channel(
        id=0, name='Channel 1',
        timeseries=UniformTimeSeries(
          frequency=Frequency.from_interval(1),
          data=get_data(interval=1, duration=25.0)
        )
      )
    )    
    self.assertEquals(session.laps[0].end_time, 10.0)
    self.assertEquals(session.laps[1].end_time, 20.0)

    # test with no lap time but sector times
    lap = Lap(offset=0.0, length=None, sectors=[10.0, 20.0])
    self.assertEquals(lap.end_time, 20.0)

    # test with no lap time but also no sectors
    lap = Lap(offset=0.0, length=None, sectors=[])
    self.assertEquals(lap.end_time, 0.0)
      
# utility functions
  
def get_data(interval, duration):
  num_samples = int((duration * 1000) / interval)
  return np.array([x * 0.1 for x in range(0, num_samples)], dtype=np.float32)

def get_times(interval, duration):
  '''Gets sampling times at the specified interval (which technically
  isn't variable, but never mind)'''
  num_samples = int((duration * 1000) / interval)
  return np.array(range(0, num_samples, interval), dtype=np.float32)

if __name__ == '__main__':
  unittest.main()