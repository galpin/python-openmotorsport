#!/usr/bin/python2.6
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

__author__  = 'Martin Galpin'
__contact__ = 'm@66laps.com'
__version__ = '1.0b'
__license__ = 'Apache License, Version 2.0'

import datetime
import os
import tempfile
import zipfile
import itertools
import xml.etree.ElementTree as ET
import numpy as np

class Session(object):
  '''An instance of openmotorsport.Session represents a OpenMotorsport file.'''
  
  def __init__(self, filepath=None, **kwargs):
    '''
    Create a new instance of openmotorsport.Session. Either constructs a 
    brand new instance that is empty or loads an existing file.
    
    Args:
      filepath
        The path to an existing OpenMotorsport session to load. [optional]
    '''    
    self.metadata = Metadata()
    '''An instance of openmotorsport.Metadata for this session.'''
    
    self._channels = {}
    self._groups = {}
    
    '''A list of openmotorsport.Channel instance for this session.'''
    
    self.markers = np.array([], dtype=np.float32)
    '''A list of time offset markers for this session.'''
    
    self.num_sectors = 0
    '''The number of sectors (recorded as markers) per lap.'''
    
    self._laps = []
    
    if filepath:
      self._load(filepath)
      
    self.__dict__.update(**kwargs)
    
  @property
  def channels(self):
    '''Gets a list of Channel instances for this session.'''
    return self._channels.values()
    
  def __enter__(self):
    '''Context manager protocol. Returns self.'''
    return self
    
  def __exit__(self, type, value, traceback):
    '''Context manager protocol. Automatically closes resources.'''
    self.close()
    return False
    
  def close(self):
    '''Close any open resources.'''
    self._zipfile.close()
    
  def add_markers(self, markers):
    '''Adds a list of markers to the current session.'''
    self.markers = np.append(self.markers, markers)

  def add_marker(self, marker):
    '''Adds a markers to the current session.'''
    self.markers = np.append(self.markers, marker)
    
  def add_channel(self, channel):
    '''Adds a given instance of Channel to this session.'''
    self._channels['%s/%s' % (channel.name, channel.group)] = channel
    if not channel.group in self._groups:
      self._groups[channel.group] = []
    self._groups[channel.group].append(channel)
    
  def get_channel(self, name, group=None):
    '''Gets a list of channels that match a given name and group.'''
    try:
      return self._channels['%s/%s' % (name, group)]
    except KeyError:
      return None
      
  def get_group(self, group):
    '''Gets a list of channels in a given group.'''
    try:
      return self._groups[group]
    except KeyError:
      return None
          
  def _getlaps(self):
    '''Lazy initialized getter for laps (laps are calculated from markers).'''
    if not self._laps:
      self.refresh_laps()
    return self._laps

  laps = property(_getlaps)    
  '''A list of openmotorsport.Lap instances for this session. Laps are 
  calculated based on the number of the markers and sectors per lap.'''
        
  def write(self, filepath):
    '''Write this instance to an OpenMotorsport file and returns the filepath.'''
    def write_binary(array, zipfile, arcname):
      tup = tempfile.mkstemp()            
      array.tofile(os.fdopen(tup[0], "wb"))        
      zipfile.write(tup[1], arcname=arcname)
      os.remove(tup[1])
      
    try:    
      self._zipfile = zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED)
      self._zipfile.writestr('meta.xml', self._write_meta())            

      for c in self.channels:
        write_binary(c.data, self._zipfile, 'data/%s.bin' % c.id)
        if not c.interval and c.times is not None:
          write_binary(c.times, self._zipfile, 'data/%s.tms' % c.id)

      self._zipfile.close()
      return filepath
    except:
      # delete a partial file on error
      os.remove(filepath)
      raise
    
  def _read_channel(self, channel):                    
    '''Read the binary data (and times, if necessary) for a given a channel.'''
    try:
      p = 'data/%s.bin' % channel.id
      channel.data = np.fromfile(self._zipfile.extract(p, self._tempdir), dtype=np.float32)

      if not channel.interval:
        # variable frequency, we need to read the acompanying times
        p = 'data/%s.tms' % channel.id
        channel.times = np.fromfile(self._zipfile.extract(p, self._tempdir), dtype=np.float32)
    except KeyError:
      raise ImportError('Cannot find data file for %s (id = %s)' 
        % (channel.name, channel.id))    
    
  def _write_meta(self):
    '''Generate the meta.xml file and return the contents as a string.'''
    root = ET.Element('openmotorsport')
    root.attrib['xmlns'] = BASE_NS
    
    # metadata
    meta = ET.SubElement(root, 'metadata')
    
    # user
    ET.SubElement(meta, 'user').text = self.metadata.user
    
    # venue (only circuit is mandatory)
    venue = ET.SubElement(meta, 'venue')
    SubElementFromDict(venue, self.metadata.venue, 'name')
    SubElementFromDictConditional(venue, self.metadata.venue, 'configuration')
        
    # vehicle (manufactuer, model is mandatory)
    vehicle = ET.SubElement(meta, 'vehicle')
    SubElementFromDict(vehicle, self.metadata.vehicle, 'name')
    SubElementFromDictConditional(vehicle, self.metadata.vehicle, 'year')
    SubElementFromDictConditional(vehicle, self.metadata.vehicle, 'category')
    SubElementFromDictConditional(vehicle, self.metadata.vehicle, 'comments')
      
    # date in ISO-8601
    ET.SubElement(meta, 'date').text = to_iso8601_date(self.metadata.date)
    
    # comments
    if self.metadata.comments:
      ET.SubElement(meta, 'comments').text = self.metadata.comments

    # datasource
    if self.metadata.datasource:
      ET.SubElement(meta, 'datasource').text = self.metadata.datasource
    
    # channels and groups
    def write_channel(root, groups, channel):
      # channel parent node
      if channel.group:
        if channel.group in groups:
          root = groups[channel.group]
        else:
          root = ET.SubElement(root, 'group')
          ET.SubElement(root, 'name').text = channel.group
          groups[channel.group] = root

      node = ET.SubElement(root, 'channel')
        
      node.attrib['id'] = str(channel.id)
      
      if channel.interval:
        node.attrib["interval"] = str(channel.interval)
      if channel.units:
        node.attrib['units'] = channel.units
    
      ET.SubElement(node, 'name').text = channel.name
      if channel.description:
        ET.SubElement(node, 'description').text = channel.description
        
    channels = ET.SubElement(root, 'channels')
    groups = {}
    for obj in self.channels:
      write_channel(channels, groups, obj)
    
    # markers
    markers = ET.SubElement(root, 'markers')
    if self.num_sectors:
      markers.attrib["sectors"] = str(self.num_sectors)
      
    for marker in self.markers:
      node = ET.SubElement(markers, 'marker')
      node.attrib["time"] = '%.2f' % float(marker)
        
    return ET.tostring(root, encoding='UTF-8')

  def _load(self, filepath):
    '''Read an OpenMotorsport file from a given filepath.'''
    self._tempdir = tempfile.mkdtemp() 
    self._zipfile = zipfile.ZipFile(filepath, 'r', zipfile.ZIP_DEFLATED)
    
    try:
      metafilepath = self._zipfile.extract('meta.xml', self._tempdir)
      root = ET.parse(metafilepath).getroot()    
      self._parse_meta(root)
      self._parse_markers(root)      
      self._parse_channels(root)
    except KeyError:
      raise Exception('meta.xml was not found.')
      
    # the zipfile is left open (for lazy loading of data)             

  def _parse_meta(self, root):
    '''Parses meta.xml/metadata from a given ElementTree root node.'''
    
    def read(root, path, dict, key):
      dict[key] = root.findtext('%s/%s' % (ns(path), ns(key)))
        
    node = root.find(ns('metadata'))
                
    # read user
    self.metadata.user = node.findtext(ns('user'))
    
    # read vehicle
    read(node, 'vehicle', self.metadata.vehicle, 'name') 
    read(node, 'vehicle', self.metadata.vehicle, 'year') 
    read(node, 'vehicle', self.metadata.vehicle, 'category') 
    read(node, 'vehicle', self.metadata.vehicle, 'comments') 

    # read venue
    read(node, 'venue', self.metadata.venue, 'name')
    read(node, 'venue', self.metadata.venue, 'configuration')
    
    # read date
    date = datetime.datetime.now()    
    self.metadata.date = from_iso8601_date(node.find(ns('date')).text)
    
    # read comments
    self.metadata.comments = node.findtext(ns('comments'))
    
    # read datasource
    self.metadata.datasource = node.findtext(ns('datasource'))    
    
  def _parse_channels(self, root, group=None):
    '''Parses meta.xml/channels (and groups) from a given ElementTree root.'''
    def parse_channel(node, group=None):
      channel = Channel(
        id = node.get('id'),
        name = node.findtext(ns('name')),
        interval = node.get('interval'),
        units = node.get('units'),
        description = node.findtext(ns('description')),
        group = group
      )
      channel.__parent__ = self # a reference to this session for lazy loading
      return channel
      
    def parse_channels(root, group=None):
      for node in root.getchildren():
        if node.tag == ns('channel'):
          self.add_channel(parse_channel(node, group))
        elif node.tag == ns('group'):
          parse_channels(node, node.findtext(ns('name')))
      
    parse_channels(root.find(ns('channels')))
  
  def _parse_markers(self, root):
    '''Parses meta.xml/markers from a given ElementTree root.'''
    node = root.find(ns('markers'))
    if not node:
      return
    
    self.num_sectors = int(node.get('sectors')) if node.get('sectors') else 0
    
    markers = node.findall(ns('marker'))
    
    self.add_markers((float(x.get('time')) for x in markers))
    
        
  def refresh_laps(self): 
    '''Calculates laps based on the sessions markers and number of sectors.
    
    Returns:
      A list of Lap instances.
    '''
    def make_relative(time, laps): 
      return time if not laps else time - sum([lap.time for lap in laps])

    def grouper(iterable, n, fillvalue=None):
      return itertools.izip_longest(*[iter(iterable)]*n, fillvalue=fillvalue)

    self._laps[:] = []
    for g in grouper(self.markers, self.num_sectors + 1):
      self._laps.append(Lap(
        sectors = [make_relative(s, self._laps) if s else None for s in g[:-1]],
        time = make_relative(g[-1], self._laps) if g[-1] else None
      ))    
      
  def __repr__(self):
    return self.metadata      
        
  def __eq__(self, other):
    return other and \
            self.metadata == other.metadata and \
            self.channels == other.channels and \
            self.num_sectors == other.num_sectors and \
            np.equal(self.markers.all(), other.markers.all())

class Lap(object):
  '''This class represents a single lap with a time and list of sectors.'''
  def __init__(self, time=None, sectors=[]):
    self._time = time
    self._sectors = sectors
    
  @property
  def time(self):
    '''Gets the lap time (in seconds) of this lap.'''
    return self._time
  
  @property
  def sectors(self):
    '''Gets a list of sector times (in seconds).'''
    return self._sectors
    
  def __repr__(self):
    return '%.3f (%s)' % (self._time, self._sectors)
  
  def __eq__(self, other):
    return other and \
      self.time == other.time and \
      self.sectors == other.sectors
      
class Channel(object):
  '''This class represents a single channel within an OpenMotorsport file.'''
  def __init__(self,
              id=None,
              name=None,              
              group=None,
              units=None,
              interval=None,
              description=None,
              data=np.array([], dtype=np.float32), 
              times=np.array([], dtype=np.float32)):
    '''Contructs a new instance of Channel.
    
    Arguments:
      data
        An initial numpy data array.
      times
        An initial numpy times array.
    '''
    
    self._id = id
    '''The unique identifier for this channel.'''
    
    self._name = name
    '''The channel name.'''
    
    self._group = group
    '''The channel group name.'''
    
    self._interval = interval
    '''The sample interval for this channel. If not specified (None) then the
    time of each sample will be provided in Channel.times.'''
    
    self._units = units
    '''The abbreviated units of measurement for this channel.'''
    
    self._description = description
    '''A textual description of this channel.'''
    
    self._data = data
    self._times = times
    self.__parent__ = None
        
  @property 
  def name(self):
    '''Gets the channel name [read-only].'''
    return self._name
  
  @property
  def id(self):
    '''Gets the channel id [read-only].'''
    return self._id
  
  @property
  def group(self):
    '''Gets the channel group [read-only].'''
    return self._group
  
  @property
  def interval(self):
    '''Gets the channel interval [read-only].'''
    return self._interval
  
  @property
  def units(self):
    '''Gets the channel units [read-only].'''
    return self._units
    
  @property
  def description(self):
    '''Gets the channel description [read-only].'''
    return self._description
    
  def append(self, value, time=None):
    '''A convienience method to append a data sample and optional time.'''
    self._data = np.append(self._data, np.asanyarray([value], dtype=self._data.dtype))
    if time:
      self._times = np.append(self._time, np.asanyarray([value], dtype=self._times.dtype))   

  def _lazy_load(self):
    if self.__parent__ and not len(self._data):
      self.__parent__._read_channel(self)
      
  def _getdata(self):
    self._lazy_load()
    return self._data
  
  def _setdata(self, data):
    self._data = data
  
  data = property(_getdata, _setdata)
  '''An array of data samples for this channel.'''
  
  def _gettimes(self):
    self._lazy_load()
    return self._times
  
  def _settimes(self, times):
    self._times = times
  
  times = property(_gettimes, _settimes)
  '''An array of times for each data sample.'''
  
  def __repr__(self):
    return '%s (%s) [%s]' % (self.name, self.group, self.interval)

  def __eq__(self, other):
    return other and \
          self.name == other.name and \
          self.group == other.group and \
          self.interval == other.interval and \
          len(self.data) == len(other.data)


class Metadata(object):
  '''This class represents the metadata associated with an OpenMotorsport session.'''  
  def __init__(self, **kwargs):
    self.user = None
    '''The name of the user.'''
    
    self.venue = { 
      'name': None,
      'configuration': None 
    }
    '''A description for the venue. 
    
    Elements:
      name
        The title name of a venue (e.g. Silverstone).
      configuration
        The specific track layout (e.g. National or Grand Prix) [optional].
    '''
    
    self.vehicle = { 
      'name': None,
      'year': None, 
      'comments': None, 
      'category': None 
    }
    '''A description of the vehicle.
    
    Elements:
      name 
        A description of the vehicle (e.g. Van Diemen RF92). 
      year 
        e.g. 1992. [optional]
      category
        e.g. Formula Ford. [optional]
      comments
        A textual comment on the car. [optional]
    ''' 
    
    self.date = datetime.datetime.now()
    '''The date of the session.'''
    
    self.comments = None
    '''A textual comment on this session. [optional]'''
    
    self.datasource = None
    '''A description of the recording datasource (e.g. Pi System I). [optional]'''
    
    self.__dict__.update(**kwargs)
    
  def __repr__(self):
    return '%s at %s (%s)' % (self.user, self.venue['name'], self.date)
      
  def __eq__(self, other):
    return other and \
      self.user == other.user and \
      self.venue == other.venue and \
      self.vehicle == other.vehicle and \
      self.date == other.date and \
      self.comments == other.comments                  

# /----------------------------------------------------------------------/    

# NB: Upper Camel Case for consistency with ElementTree.                   
def SubElementFromDict(parent, dict, key):
  '''Creates an ElementTree text element from a given dict and key. If the 
  key does not exist in the dict, an Exception is raised.'''
  if dict[key] is None: raise Exception('Missing value for %s' % key)
  ET.SubElement(parent, key).text = dict[key]

def SubElementFromDictConditional(parent, dict, key):
  '''Creates an ElementTree text elelemnt from a given dict and key only if
  the key exist and its value is not None.'''
  if dict.has_key(key) and dict[key] is not None:
    ET.SubElement(parent, key).text = dict[key] 
  
def to_iso8601_date(date):
  '''Gets an ISO-8601 string for a given date.'''
  return date.strftime("%Y-%m-%dT%H:%M:%S")
  
def from_iso8601_date(string):
  '''Gets a date from an ISO-8601 string.'''
  return datetime.datetime.now().strptime(string, "%Y-%m-%dT%H:%M:%S")
  
def ns(string):
  '''Format an XPath with the default namespace.'''
  return '{%s}%s' % (BASE_NS, string)

BASE_NS = 'http://66laps.org/ns/openmotorsport-1.0'
'''The default namespace of an OpenMotorsport document.'''