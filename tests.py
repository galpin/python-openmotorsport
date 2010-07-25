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
import numpy as np

from openmotorsport.openmotorsport import Session, Channel, Metadata
from openmotorsport.utils import *

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
    
  def testWriteWithData(self):
    path = 'test_data.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()    
    original_doc.channels.append(Channel(id=0, name='Channel 1',
      interval='1', data=self._getSampleData()))      
    original_doc.channels.append(Channel(id=1, name='Channel 2',
      interval='1', data=self._getSampleData()))            
    original_doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)
    for channel in imported_doc.channels: channel.data # lazy
    self.assertEquals(original_doc, imported_doc)
    os.remove(path)
    

  def testWriteWithVariableFrequencyChannel(self):
    path = 'test_variable.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()    
    original_doc.channels.append(Channel(id=0, name='Channel 1',
     data=self._getSampleData(), times=self._getSampleData()))
    original_doc.channels.append(Channel(id=1, name='Channel 2',
      interval='10', data=self._getSampleData()))            
    original_doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)
    self.assertEquals(original_doc, imported_doc)
    #os.remove(path)
    

  def testWriteWithMarkers(self):
    path = 'test_markers.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()    
    original_doc.channels.append(Channel(id=0, name='Channel 1',
      interval='1', data=self._getSampleData()))
    original_doc.channels.append(Channel(id=1, name='Channel 2',
      interval='1', data=self._getSampleData()))         
    original_doc.add_markers([1.0, 2.0, 3.0])
    original_doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)
    self.assertEquals(original_doc, imported_doc)
    os.remove(path)  


  def testWriteWithSectors(self):
    path = 'test_markers.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()    
    original_doc.channels.append(Channel(id=0, name='Channel 1',
      interval='1', data=self._getSampleData()))
    original_doc.channels.append(Channel(id=1, name='Channel 2',
      interval='1', data=self._getSampleData()))         
    original_doc.add_markers([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
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
      os.remove(path)  
    else:
      self.fail('Expected exception.')
  
      
  def testDataAppend(self):
    path = 'test_data.om'
    
    doc = Session()
    doc.metadata = self._getSampleMeta()    
    doc.channels.append(Channel(id=0, name='Channel 1',
      interval='1'))
    doc.channels.append(Channel(id=1, name='Channel 2',
        interval='1'))      
        
    self.assertEquals(len(doc.channels[0].data), 0)
    
    for x in range(0, 2):
      for y in range(0, 1000):
        doc.channels[x].append(float(y))
    
    self.assertEquals(len(doc.channels[0].data), 1000)
    self.assertEquals(len(doc.channels[1].data), 1000)
    
    doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)
    self.assertEquals(doc, imported_doc)
    #os.remove(path)
    
  def testChannelGroup(self):
    path = 'test_data.om'
    original_doc = Session()
    original_doc.metadata = self._getSampleMeta()    
    
    # no group
    original_doc.channels.append(Channel(id=0, name='Channel 1',
      interval='1', data=self._getSampleData()))      
    original_doc.channels.extend([
      Channel(
        id=1, 
        name='Channel 2', 
        interval='1', # TODO as ints
        data=self._getSampleData(),
        group='Group 2'
      ),
      Channel(
        id=2, 
        name='Channel 3', 
        interval='1', 
        data=self._getSampleData(),
        group='Group 1'
      )]
    )
    original_doc.write(path)
    self.assertTrue(os.path.exists(path))        
    imported_doc = Session(path)
    self.assertEquals(original_doc, imported_doc)
    os.remove(path)
    
  def testLapTimesSectors(self):
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0]
    self.assertEquals(len(doc.laps), 2)
    self.assertEquals(doc.laps[0].time, 30.0)
    self.assertEquals(doc.laps[0].sectors, [10.0, 20.0])
    self.assertEquals(doc.laps[1].time, 40.0)
    self.assertEquals(doc.laps[1].sectors, [20.0, 30.0])
    
    doc = Session()
    doc.num_sectors = 0
    doc.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0]
    self.assertEquals(len(doc.laps), 6)
    for lap in doc.laps:
      self.assertEquals(lap.sectors, [])
      
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0, 30.0, 40.0]
    self.assertEquals(len(doc.laps), 2)
    self.assertEquals(doc.laps[0].sectors, [10.0, 20.0])
    self.assertEquals(doc.laps[0].time, 30.0)
    self.assertEquals(doc.laps[1].sectors, [10.0, None])
    self.assertEquals(doc.laps[1].time, None)
    
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0]
    self.assertEquals(len(doc.laps), 1)
    self.assertEquals(doc.laps[0].sectors, [10.0, 20.0])
    self.assertEquals(doc.laps[0].time, None)
    
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0, 30.0]
    self.assertEquals(len(doc.laps), 1)
    self.assertEquals(doc.laps[0].sectors, [10.0, 20.0])
    self.assertEquals(doc.laps[0].time, 30.0)
    
    doc = Session()
    self.assertEquals(len(doc.laps), 0)  
    
    doc = Session()
    doc.markers = [10.0, 20.0, 30.0]
    self.assertEquals(len(doc.laps), 3)
    
  def testGetChannelOrGroup(self):
    c1 = Channel(name='Channel 1')
    c2 = Channel(name='Channel 2')
    c3 = Channel(name='Channel 3', group='Group 1')
    c4 = Channel(name='Channel 4', group='Group 2')
    c5 = Channel(name='Channel 5', group='Group 1')
    c6 = Channel(name='Channel 5')

    doc = Session()
    doc.channels = [c1,c2,c3,c4,c5,c6]

    self.assertEquals(doc.get_channel('Channel 1'), [c1])
    self.assertEquals(doc.get_channel('Channel 2'), [c2])
    self.assertEquals(doc.get_channel('Channel 3'), [c3])
    self.assertEquals(doc.get_channel('Channel 4'), [c4])
    self.assertEquals(doc.get_channel('Channel 5'), [c5, c6])    
    self.assertEquals(doc.get_group('Group 1'), [c3, c5])    
    self.assertEquals(doc.get_channel('Channel 5', group='Group 1'), [c5])    
        
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
      
class UtilsTests(unittest.TestCase):

  def testLapDifference(self):
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertEquals(lap_difference(doc, doc.laps[0]), None)
    self.assertEquals(lap_difference(doc, doc.laps[1]), 10.0)
    self.assertEquals(lap_difference(doc, doc.laps[2]), -20.0)
    
  def testFastestLapTime(self):
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertEquals(fastest_lap_time(doc), 20.0)
    
    # no markers at all
    doc = Session()
    doc.num_sectors = 2
    doc.markers = []
    self.assertEquals(fastest_lap_time(doc), None)
    
    # no complete laps
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0]
    self.assertEquals(fastest_lap_time(doc), None)
    
  def testFastestLap(self):
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertEquals(fastest_lap(doc), doc.laps[2])
    
    # no markers at all
    doc = Session()
    doc.num_sectors = 2
    doc.markers = []
    self.assertEquals(fastest_lap(doc), None)
    
    # no complete laps
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0]
    self.assertEquals(fastest_lap(doc), None)
    
  def testFastestSector(self):
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertEquals(fastest_sector(doc, 1), 5.0)
    self.assertEquals(fastest_sector(doc, 2), 10.0)
    
    # no markers at all
    doc = Session()
    doc.num_sectors = 2
    doc.markers = []
    self.assertEquals(fastest_sector(doc, 1), None)
    
    # no complete laps
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0]
    self.assertEquals(fastest_sector(doc, 2), 20.0)
    
  def testIsFastestSector(self):
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertTrue(is_fastest_sector(doc, 1, 5.0))
    self.assertTrue(is_fastest_sector(doc, 2, 10.0))   
    
    # no markers at all
    doc = Session()
    doc.num_sectors = 2
    doc.markers = []
    self.assertEquals(fastest_sector(doc, 1), None)
    
    # no complete laps
    doc = Session()
    doc.num_sectors = 2
    doc.markers = [10.0, 20.0]
    self.assertEquals(fastest_sector(doc, 2), 20.0)   
    
if __name__ == '__main__':
  unittest.main()