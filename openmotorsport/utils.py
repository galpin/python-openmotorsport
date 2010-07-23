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
  return None if not index else lap.time - session.laps[index - 1].time
  
def is_fastest_lap(session, lap):
  '''Returns True if the given lap is the fastest in the given session.'''
  return lap == fastest_lap(session)
  
def fastest_lap_time(session):
  '''Gets the fastest lap time in a given session.'''
  if not _has_at_least_one_lap(session): return None
  return min([lap.time for lap in session.laps if lap.time is not None])
  
def fastest_lap(session):
  '''Gets the fastest lap in a given session.'''
  if not _has_at_least_one_lap(session): return None
  f = lambda x, lap: lap.time == fastest_lap_time(session) and lap or x
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
  
def _has_at_least_one_lap(session):
  '''Private method. 
  Gets whether a session has no laps or if it has a lap, that the lap is 
  complete (and that they didn't crash on their outlap - it happens!)
  '''
  return not(not session.laps or session.laps[0].time is None)