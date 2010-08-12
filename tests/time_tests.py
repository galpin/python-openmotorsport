#!/usr/bin/python
#
# A library that provides a python interface the OpenMotorsport format.
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
from openmotorsport.time import *
from numpy.testing.utils import assert_array_equal

class FrequencyTests(unittest.TestCase):
  def test_frequency(self):
    f = Frequency(5) # 5Hz
    self.assertEquals(f.frequency, 5)
    self.assertEquals(f.interval, 200)
    self.assertEquals(f.__repr__(), '5Hz')
    self.assertEquals(f, Frequency.from_interval(200))

class VariableTimeSeriesTests(unittest.TestCase):
  def test_VariableTimeSeries(self):
    ts = VariableTimeSeries()
    self.assertEquals(len(ts), 0)
    self.assertEquals(len(ts.times), 0)

    ts = VariableTimeSeries([1,2,3], [1,2,3])
    self.assertEquals(len(ts), 3)
    self.assertEquals(len(ts.times), 3)

    ts = VariableTimeSeries(np.array([1,2,3], dtype=np.float32),
                            np.array([1,2,3], dtype=np.float32))
    self.assertEquals(len(ts), 3)
    self.assertEquals(len(ts.times), 3)

    ts = VariableTimeSeries(np.array([1,2,3], dtype=np.float64),
                            np.array([1,2,3], dtype=np.float64))
    self.assertEquals(len(ts), 3)
    self.assertEquals(len(ts.times), 3)
    self.assertEquals(ts.data.dtype, np.float32)
    self.assertEquals(ts.times.dtype, np.int32)

    self.assertRaises(ValueError, VariableTimeSeries, [1,2,3], [])
    self.assertRaises(ValueError, VariableTimeSeries, [], [1,2,3])
    self.assertRaises(ValueError, VariableTimeSeries, [1,2,3])

  def test_index_at(self):
    ts = VariableTimeSeries([1,2,3], [1,2,3])
    self.assertEquals(ts.index_at(1), 0)
    self.assertEquals(ts.index_at(2), 1)
    self.assertEquals(ts.index_at(3), 2)
    self.assertEquals(ts.index_at(1.5), 1)
    self.assertRaises(ValueError, ts.index_at, 3.5)

  def test_append(self):
    ts = VariableTimeSeries([1,2,3], [1,2,3])
    self.assertEquals(len(ts), 3)
    self.assertEquals(len(ts.times), 3)

    ts.append([4,5,6], [4,5,6])
    self.assertEquals(len(ts), 6)
    self.assertEquals(len(ts.times), len(ts))

    ts.append(7,7)
    self.assertEquals(len(ts), 7)
    self.assertEquals(len(ts.times), len(ts))

    ts.append(np.array([8,9,10], dtype=np.float32),
              np.array([8,9,10], dtype=np.float32))
    self.assertEquals(len(ts), 10)
    self.assertEquals(len(ts.times), len(ts))

    self.assertRaises(ValueError, ts.append, [1,2,3], [])

  def test_get(self):
    ts = VariableTimeSeries(data=[1,2,3], times=[1,2,3])
    self.assertEqual(ts.get(0), 1)
    self.assertEqual(ts.get(1), 2)
    self.assertEqual(ts.get(2), 3)    
    self.assertRaises(IndexError, ts.get, 4)

  def test_at(self):
    ts = VariableTimeSeries()
    self.assertRaises(ValueError, ts.at, 1)

    ts = VariableTimeSeries([1,2,3], [1,2,3])
    self.assertRaises(ValueError, ts.at, 0)
    self.assertEquals(ts.at(2), 2)
    self.assertEquals(ts.at(3), 3)
    self.assertEquals(ts.at(2.5), 2.5)
    self.assertRaises(ValueError, ts.at, 4)    

  def test_duration(self):
    ts = VariableTimeSeries([1,2,3], [1,2,3])
    self.assertEquals(ts.duration, 3)

    ts = VariableTimeSeries()
    self.assertEquals(ts.duration, 0)
    self.assertEquals(ts.end_time, 0)

    ts = VariableTimeSeries([1,2,3], [1,2,3], offset=4)
    self.assertEquals(ts.end_time, 7)

  def test_slice(self):
    ts = VariableTimeSeries([1,2,3], [1,2,3])
    assert_array_equal(
      ts.slice(Epoch(offset=ts.offset, length=ts.duration)).data,
      [1,2,3]
    )
    assert_array_equal(ts.slice(Epoch(offset=1, length=2)).data, [1,2,3])
    self.assertRaises(ValueError, ts.slice, Epoch(offset=0, length=4))

  def test_equality(self):
    ts1 = VariableTimeSeries([1,2,3], [1,2,3])
    ts2 = VariableTimeSeries([1,2,3,4], [1,2,3,4])
    self.assertTrue(ts1 == ts1)
    self.assertFalse(ts1 == ts2)
    self.assertTrue(ts2 != ts1)
    self.assertFalse(ts2 == None)

class TimeSeriesTests(unittest.TestCase):
  def test_TimeSeries(self):
    ts = UniformTimeSeries(Frequency(5))
    self.assertEquals(ts.frequency, Frequency(5))
    self.assertEquals(len(ts), 0)

    ts = UniformTimeSeries(Frequency(5), [1,2,3])
    self.assertEquals(len(ts), 3)

    ts = UniformTimeSeries(Frequency(5), np.array([1,2,3], dtype=np.float32))
    self.assertEquals(len(ts), 3)
    self.assertEquals(ts.data.dtype, np.float32)

    ts = UniformTimeSeries(Frequency(5), [1,2,3,4,5])
    self.assertEquals(ts.offset, 0)
    self.assertEquals(ts.duration, 1000)

  def test_append(self):
    ts = UniformTimeSeries(Frequency(5), [1,2,3])
    self.assertEquals(len(ts), 3)
    ts.append(4)
    self.assertEquals(len(ts), 4)
    ts.append([5,6,7])
    self.assertEquals(len(ts), 7)
    ts.append(np.array([8,9,10], dtype=np.float32))
    self.assertEquals(len(ts), 10)
    self.assertEquals(ts.duration, 2000)
    self.assertEquals(ts.end_time, 2000)

    ts = UniformTimeSeries(Frequency(5), [1,2,3], offset=1000)
    ts.append([5,6,7])
    self.assertEquals(ts.duration, 1200)
    self.assertEquals(ts.end_time, 2200)

  def test_at(self):
    ts = UniformTimeSeries(Frequency(5), [10,20,30,40,50,60,70])
    self.assertEquals(ts.duration, 1400)
    self.assertEquals(ts.at(0), 10)
    self.assertEquals(ts.at(200), 20)
    self.assertEquals(ts.at(1200), 70)
    self.assertRaises(ValueError, ts.at, 1400)

  def test_slice(self):
    ts = UniformTimeSeries(Frequency(5), [10,20,30,40,50,60,70])
    assert_array_equal(ts.slice(Epoch(offset=0, length=600)).data, [10,20,30])
    assert_array_equal(ts.slice(Epoch(length=ts.end_time)).data, ts.data)
    assert_array_equal(ts.slice(Epoch(length=ts.end_time)).data, ts.data)
    self.assertRaises(ValueError, ts.slice, Epoch(offset=0, length=1600))

  def test_downsample(self):
    ts = UniformTimeSeries(Frequency(10), [10,20,30,40,50,60,70,80,90,100])
    self.assertEqual(len(ts.resample(Frequency(5))), 5)
    ts = UniformTimeSeries(Frequency(5), [10,20,30,40,50,60,70,80,90,100])
    self.assertEqual(len(ts.resample(Frequency(1))), 2)
    ts = UniformTimeSeries(Frequency(5), [])
    self.assertEqual(len(ts.resample(Frequency(1))), 0)    

  def test_upsample(self):
    ts = UniformTimeSeries(Frequency(5), [10,20,30,40,50,60,70,80,90,100])
    self.assertEqual(len(ts.resample(Frequency(10))), 20)
    ts = UniformTimeSeries(Frequency(5), [10,20,30,40,50,60,70,80,90,100])
    self.assertEqual(len(ts.resample(Frequency(20))), 40)
    ts = UniformTimeSeries(Frequency(5), [])
    self.assertEqual(len(ts.resample(Frequency(10))), 0)

  def test_equality(self):
    ts1 = UniformTimeSeries(Frequency(5), [10,20,30,40,50,60,70,80,90,100])
    ts2 = UniformTimeSeries(Frequency(10), [10,20,30,40,50,60,70,80,90,100])    
    ts3 = UniformTimeSeries(Frequency(5), [])
    self.assertTrue(ts1 == ts1)
    self.assertFalse(ts1 == ts2)
    self.assertFalse(ts1 == ts3)
    self.assertTrue(ts1 != ts2)
    self.assertTrue(ts1 != ts3)
    self.assertFalse(ts1 == None)

  def test_get(self):
    ts = UniformTimeSeries(Frequency(5), data=[1,2,3])
    self.assertEqual(ts.get(0), 1)
    self.assertEqual(ts.get(1), 2)
    self.assertEqual(ts.get(2), 3)
    self.assertRaises(IndexError, ts.get, 4)

class TestConversion(unittest.TestCase):
  def test_time(self):
    self.assertEquals(time(1000, 's'), 1)
    self.assertEquals(time(1000, 'ms'), 1000)
    self.assertEquals(time(1000, 'us'), 1000000)
    self.assertEquals(time(1000, 'ns'), 1000000000)
    self.assertEquals(time(1000, 'ps'), 1000000000000)

if __name__ == '__main__':
  unittest.main()