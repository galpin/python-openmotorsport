#!/usr/bin/python2.5
#
# Utility functions for an OpenMotorsport sessions.
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

__author__  = 'Martin Galpin'
__contact__ = 'm@66laps.com'
__version__ = '1.0'
__license__ = 'Apache License, Version 2.0'

def lap_difference(session, lap):
  '''Gets the time difference between this lap and the previous lap.'''
  index = session.laps.index(lap)
  return None if not index else lap.length - session.laps[index - 1].length
  
def is_fastest_lap(session, lap):
  '''Returns True if the given lap is the fastest in the given session.'''
  return lap == fastest_lap(session)
  
def fastest_lap_time(session):
  '''Gets the fastest lap time in a given session.'''
  if not _has_at_least_one_lap(session): return None
  return min([lap.length for lap in session.laps if lap.length is not None])
  
def fastest_lap(session):
  '''Gets the fastest lap in a given session.'''
  if not _has_at_least_one_lap(session): return None
  f = lambda x, lap: lap.length == fastest_lap_time(session) and lap or x
  return reduce(f, session.laps)

def fastest_sector(session, sector):
  '''Returns True if time is the fastest sector in a given session.'''
  sector -= 1
  # make sure we at least have this number of sectors
  if len(session.markers) <= sector: return None
  fastest = session.laps[0].sectors[sector]
  for lap in session.laps[1:]:
    if lap.sectors[sector] < fastest: fastest = lap.sectors[sector]
  return fastest
  
def is_fastest_sector(session, sector, time):
  '''Returns True if a given time is the fastest for a given in a session.'''
  return time == fastest_sector(session, sector)

def fastest_or_next_fastest_lap(lap):
  '''
  Gets the fastest lap for a given lap. If this already is the fastest lap,
  get the next fastest lap instead. Finally, if there is no other lap, None
  will be returned.
  '''
  the_fastest_lap = fastest_lap(lap.session)
  if lap != the_fastest_lap: return the_fastest_lap
  laps = [x for x in lap.session.laps if x.length >= lap.length and x != lap]
  return laps[0] if laps else None

def slowest_lap_time(session):
  '''Gets the slowest lap time in a given session.'''
  if not _has_at_least_one_lap(session): return None
  return max([lap.length for lap in session.laps if lap.length is not None])

def slowest_lap(session):
  '''Gets the slowest Lap in a given session. Currently include outliners.'''
  if not _has_at_least_one_lap(session): return None
  f = lambda x, lap: lap.length == slowest_lap_time(session) and lap or x
  return reduce(f, session.laps)

def slowest_or_next_slowest_lap(lap):
  '''
  Gets the slowest Lap for a given session. If this is already the slowest Lap,
  get the next slowest Lap instead. Finally, if there is no other Lap, None will
  be returned.
  '''
  the_slowest_lap = slowest_lap(lap.session)
  if lap != the_slowest_lap: return the_slowest_lap
  laps = [x for x in lap.session.laps if x.length <= lap.length and x != lap]
  return laps[0] if laps else None

def next_lap(lap):
  '''Get the next Lap sequentially. Returns None if this is the last lap.'''
  return lap.session.laps[lap.index + 1] \
    if lap.index < (len(lap.session.laps) - 1) else None

def previous_lap(lap):
  ''' Gets the previous Lap. Returns None if this is the first lap.'''
  return lap.session.laps[lap.index - 1] if lap.index > 0 else None
  
def _has_at_least_one_lap(session):
  '''Private method. 
  Gets whether a session has no laps or if it has a lap, that the lap is 
  complete (and that they didn't crash on their outlap - it happens!)
  '''
  return not(not session.laps or session.laps[0].length is None)