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

import numpy as np
from scipy import interpolate
from scipy import signal

# Base time is currently milliseconds (sufficient for up to 1KHz)
BASE_TIME = 1000
# Base units are currently milliseconds
BASE_UNITS = 'ms'
# Conversion multipliers between millisecond and other units
CONVERSION = {
  's': 10**-3,
  'ms': 1,
  'us': 10**3,
  'ns': 10**6,
  'ps': 10**9
}

class Frequency(object):
  '''
  This class represents a sampling rate (and interval).
  '''
  def __init__(self, frequency):
    '''
    Creates a new instance of Frequency. Takes a sampling frequency:

    >>> f = Frequency(5) # 5Hz
    >>> f.frequency
    5
    >>> f.interval
    200
    
    '''
    self._frequency = frequency
    self._interval = BASE_TIME / frequency

  @staticmethod
  def from_interval(interval):
    '''
    A convienience method to create a Frequency object from a sampling interval.
    Takes a sampling interval in milliseconds:

    >>> f = Frequency.from_interval(200)
    >>> f.interval
    200
    >>> f.frequency
    5
    '''
    f = Frequency(BASE_TIME / int(interval))
    return f

  @property
  def interval(self):
    return self._interval

  @property
  def frequency(self):
    return self._frequency

  def __repr__(self):
    return '%dHz' % self._frequency

  def __eq__(self, other):
    return other and self.frequency == other.frequency


class Epoch(object):
  '''
  This class represents a period of time of a given length and offset.
  '''
  def __init__(self, length, offset=0):
    self._length = length
    self._offset = offset

  @property
  def length(self):
    return self._length

  @property
  def offset(self):
    return self._offset


class VariableTimeSeries(object):
  '''This class represents a time series with a variable sampling rate.'''

  def __init__(self, data=[], times=[], offset=0):
    '''
    Create a new instance of VariableTimeSeries.

    Raises ValueError if data and times are not of equal length.
    '''
    self._data = np.array(data, dtype=np.float32)
    self._times = np.array(times, dtype=np.uint32)
    self._offset = offset
      
    if np.size(self.data) != np.size(self.times):
      raise ValueError('Data/times mismatch. Lengths must be equal.')

  @property
  def data(self):
    return self._data

  @property
  def times(self):
    '''Gets the array of sample times.'''
    return self._times

  @property
  def offset(self):
    return self._offset
    
  @property
  def duration(self):
    '''Gets the duration of this time series.'''
    return 0 if not len(self.times) else self.times[-1]

  @property
  def end_time(self):
    '''Gets the end time of this time series (start time plus duration).'''
    return self.offset + self.duration

  @property
  def min(self):
    '''Convienience property for getting the min data value.'''
    return np.min(self.data)

  @property
  def max(self):
    '''Convienience property for getting the mas data value.'''
    return np.max(self.data)      

  def at(self, time):
    '''Gets a data sample at a given time using linear interpolation.'''
    f = interpolate.interp1d(self.times, self.data)  # TODO cache
    return f(time)

  def get(self, index):
    '''Gets a data sample at a given index.'''
    return self.data[index]

  def index_at(self, time):
    indices = np.where(self.times >= time)[0]
    if not np.size(indices):
      raise ValueError('Time exceeds length of time series.')
    return indices[0]

  def slice(self, epoch):
    '''
    Gets a new instance of VariableTimeSeries that contains only the data/times
    for a given epoch. This method currently does not implement interpolation
    and will only return actual actual data samples.
    '''
    start = self.index_at(epoch.offset)
    end = self.index_at(epoch.offset + epoch.length) + 1# inclusive
    
    return VariableTimeSeries(
      data=self.data[start:end],
      times=self.times[start:end],
      offset=epoch.offset
    )

  def append(self, data, time):
    '''
    Appends a value and times to this time series.

    Raises ValueError if value and time are not equal in length.    
    '''
    if np.size(data) != np.size(time):
      raise ValueError('Data/times mismatch. Lengths must be equal.')

    self._data = np.append(self.data,
                           np.asanyarray(data, dtype=self._data.dtype))
    self._times = np.append(self.times,
                            np.asanyarray(time, dtype=self._data.dtype))

  def __len__(self):
    return np.size(self.data)

  def __eq__(self, other):
    if hasattr(other, 'data') and hasattr(other, 'times'):
      try:
        return np.equal(self.data, other.data).all() and \
          np.equal(self.times, other.times).all()
      except ValueError:
        return False
    return False

  def __ne__(self, other):
    return not self.__eq__(other)

class UniformTimeSeries(object):
  '''
  This class represents a time series with uniform data samples.
  '''
  def __init__(self, frequency, data=[], offset=0, **kwargs):
    self._frequency = frequency
    self._data = np.array(data, dtype=np.float32)
    self._offset = offset

  @property
  def frequency(self):
    return self._frequency

  @property
  def duration(self):
    return len(self) * self._frequency.interval

  @property
  def data(self):
    return self._data

  @property
  def offset(self):
    return self._offset

  @property
  def times(self):
    # TODO cache
    return np.arange(self.offset, self.end_time, self.frequency.interval)
    
  @property
  def end_time(self):
    '''Gets the end time of this time series (start time plus duration).'''
    return self.offset + self.duration

  @property
  def min(self):
    '''Convienience property for getting the min data value.'''
    return np.min(self.data)

  @property
  def max(self):
    '''Convienience property for getting the mas data value.'''
    return np.max(self.data)     

  def append(self, data):
    '''Appends a given data sample to this time series.'''
    self._data = np.append(self.data,
                           np.asanyarray(data, dtype=self._data.dtype))

  def at(self, time):
    '''Gets a data sample at a given time using linear interpolation.'''    
    f = interpolate.interp1d(self.times, self.data)
    return f(time)

  def get(self, index):
    '''Gets a data sample at a given index.'''
    return self.data[index]    

  def slice(self, epoch):
    times = np.arange(self.offset, self.end_time, self.frequency.interval)
    f = interpolate.interp1d(times, self.data)
    epoch_times = np.arange(epoch.offset, epoch.offset + epoch.length,
                            self.frequency.interval)
    
    return UniformTimeSeries(
      frequency=self.frequency,
      data=f(epoch_times),
      offset=epoch.offset
    )

  def resample(self, frequency):
    if frequency == self.frequency or not np.size(self.data):
      data = self.data
    elif frequency.frequency > self.frequency.frequency:
      factor = frequency.frequency / self.frequency.frequency
      data = self.upsample(factor)
    else:
      factor = self.frequency.frequency / frequency.frequency
      data = self.downsample(factor)

    return UniformTimeSeries(
      frequency=frequency,
      data=data,
      offset=self.offset
    )

  def downsample(self, factor):
    return signal.decimate(self.data, factor)

  def upsample(self, factor):
    # TODO find appropriate resampling method
    return signal.resample(self.data, factor * len(self))

  def __len__(self):
    return np.size(self.data)
    
  def __eq__(self, other):
    if hasattr(other, 'data') and hasattr(other, 'frequency'):
      try:
        return self.frequency == other.frequency and \
          np.equal(self.data, other.data).all()
      except ValueError:
        return False
    return False
    
  def __ne__(self, other):
    return not self.__eq__(other)

def time(value, to):
  '''
  Converts a time in BASE_UNITS (currently milliseconds) and converts
  to a given unit. To must be one of the following:

  's': seconds
  'ms': milliseconds
  'us': microseconds
  'ns': nanoseconds
  'ps': picoseconds

  For example:
  
  >>> time(12500, 's')
  12.5
  '''
  return value * CONVERSION[to]
