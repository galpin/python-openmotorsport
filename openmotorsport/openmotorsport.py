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
import  os, sys, tempfile, zipfile
import itertools
import xml.etree.ElementTree as ET
import numpy as np

from utils import *
from time import *

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
    self._channels = {}
    self._groups = {}
    self._group_descriptions = {}
    self._channels_ids = {}
    self.markers = np.array([], dtype=np.uint32)
    self.num_sectors = None
    self._laps = []

    if filepath:
      self._load(filepath)

    self.__dict__.update(**kwargs)

  @property
  def channels(self):
    '''Gets a list of Channel instances for this session.'''
    return self._channels.values()

  @property
  def groups(self):
    '''Gets a list of groups in this session.'''
    return self._groups.keys()

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

  def add_marker(self, marker):
    '''Adds a markers to the current session.'''
    self.markers = np.append(self.markers, marker)

  def add_channel(self, channel):
    '''Adds a given instance of Channel to this session.'''
    channel.__parent__ = self # a reference to this session
    self._channels['%s/%s' % (channel.name, channel.group)] = channel
    self._channels_ids[str(channel.id)] = channel
    # only add if there is a channel group
    if channel.group:
      if not channel.group in self._groups:
        self._groups[channel.group] = []
      self._groups[channel.group].append(channel)

  def get_channel(self, name, group=None):
    '''Gets a channels that matches a given name and group.'''
    try:
      return self._channels['%s/%s' % (name, group)]
    except KeyError:
      return None

  def find_channel(self, name):
    return [channel for channel in self._channels.values() if channel.name == name]

  def get_channel_by_id(self, id):
    '''Gets a channels that matches a given id.'''
    try:
      return self._channels_ids[str(id)]
    except KeyError:
      return None

  def get_group(self, group):
    '''Gets a list of channels in a given group.'''
    try:
      return self._groups[group]
    except KeyError:
      return None

  def get_group_description(self, group):
    '''Gets the description of a given group if it exists.'''
    if group in self._group_descriptions:
      return self._group_descriptions[group]
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
        write_binary(c.timeseries.data, self._zipfile, 'data/%s.bin' % c.id)
        if not hasattr(c.timeseries, "frequency"):
          write_binary(c.timeseries.times, self._zipfile, 'data/%s.tms' % c.id)

      self._zipfile.close()
      return filepath
    except:
      # delete a partial file on error
      os.remove(filepath)
      raise

  def _read_channel_data(self, channel_id):
    p = 'data/%s.bin' % channel_id
    return np.fromfile(self._zipfile.extract(p, self._tempdir), dtype=np.float32)

  def _read_channel_times(self, channel_id):
    p = 'data/%s.tms' % channel_id
    return np.fromfile(self._zipfile.extract(p, self._tempdir), dtype=np.uint32)

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

    # duration
    if self.metadata.duration:
      ET.SubElement(meta, 'duration').text = str(self.metadata.duration)

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

      if hasattr(channel.timeseries, "frequency"):
        node.attrib["interval"] = str(channel.timeseries.frequency.interval)
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
    if self.num_sectors is not None:
      markers.attrib["sectors"] = str(self.num_sectors)

    for marker in self.markers:
      node = ET.SubElement(markers, 'marker')
      node.attrib["time"] = '%d' % int(marker)

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
    except Exception, e:
      raise Exception('Failed to import' + filepath, e), None, sys.exc_info()[2]

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

    # read duration
    duration = node.findtext(ns('duration'))
    if duration:
      self.metadata.duration = int(duration)

  def _parse_channels(self, root, group=None):
    '''Parses meta.xml/channels (and groups) from a given ElementTree root.'''
    def parse_channel(node, group=None):
      id = int(node.get('id'))
      interval = node.get('interval')
      if interval is None:
        timeseries = LazyVariableTimeSeries(parent=self, channel_id=id)
      else:
        timeseries = LazyUniformTimeSeries(
          parent=self, channel_id=id,
          frequency=Frequency.from_interval(interval)
        )

      channel = Channel(
        id = node.get('id'),
        name = node.findtext(ns('name')),
        timeseries = timeseries,
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
          group = node.findtext(ns('name'))
          description = node.findtext(ns('description'))
          parse_channels(node, group)
          if description:
            self._group_descriptions[group] = description

    parse_channels(root.find(ns('channels')))

  def _parse_markers(self, root):
    '''Parses meta.xml/markers from a given ElementTree root.'''
    node = root.find(ns('markers'))
    if not node:
      return
    self.num_sectors = int(node.get('sectors')) if node.get('sectors') else None
    markers = node.findall(ns('marker'))
    [self.add_marker(float(x.get('time'))) for x in markers]


  def refresh_laps(self):
    '''
    Calculates laps based on the sessions markers and number of sectors.

    When Session.num_sectors is None then it is considered that there is no laps
    in the session (for example, on a rally).

    If a Session.metadata.duration is given, then incomplete laps will be added
    as an additional lap at the end of a session. If no duration is given then
    incomplete laps (in laps, laps that were not complete [maybe crashed?]) will
    be ignored.

    Returns:
      A list of Lap instances.
    '''

    # TODO refactor this method
    def make_relative(time, laps):
      return time if not laps else time - sum([lap.length for lap in laps])

    def make_start_time(laps):
      return 0 if not laps else (laps[-1].offset + laps[-1].length)

    def make_relative_sector(time, sectors):
      return time if not sectors else time - sum(sectors)

    def grouper(iterable, n, fillvalue=None):
      return itertools.izip_longest(*[iter(iterable)]*n, fillvalue=fillvalue)

    # when num_sectors is None we take that to mean there are no laps.
    if self.num_sectors is None:
      return

    self._laps[:] = []
    for g in grouper(self.markers, self.num_sectors + 1):
      sectors = []
      for s in g[:-1]:
        sectors.append(make_relative_sector(make_relative(s, self._laps), sectors) if s else None)

      if g[-1]:
        lap = Lap(
          sectors = sectors,
          length = make_relative(g[-1], self._laps),
          offset = make_start_time(self._laps)
        )
        lap.__parent__ = self
        self._laps.append(lap)
      else:
        # if no duration is specified, we skip partially complete laps.
        if self.metadata.duration:
          lap = Lap(
            sectors = sectors,
            offset = make_start_time(self._laps),
            length = self.metadata.duration - make_start_time(self._laps),
            incomplete = True
          )
          lap.__parent__ = self
          self._laps.append(lap)

    if self.metadata.duration and self.metadata.duration > 0:
      if self._laps and self._laps[-1].end_time < self.metadata.duration:
        # we have a partially complete lap with no markers to indicate it
        # so we will create a new lap with no markers and a duration of the
        # remainder
        lap = Lap(
          offset = self._laps[-1].end_time,
          length = self.metadata.duration - self._laps[-1].end_time,
          sectors = [None for i in xrange(0, self.num_sectors)],
          incomplete = True
        )
        lap.__parent__ = self
        self._laps.append(lap)
      elif not self._laps:
        # there are no prior laps so this is an incomplete lap with no markers
        lap = Lap(
          offset = 0,
          length = self.metadata.duration,
          sectors = [None for i in xrange(0, self.num_sectors)],
          incomplete = True
        )
        lap.__parent__ = self
        self._laps.append(lap)


  def __repr__(self):
    return '%s' % self.metadata

  def __eq__(self, other):
    try:
      return other and \
            self.metadata == other.metadata and \
            self.num_sectors == other.num_sectors and \
            self.channels == other.channels and \
            np.equal(self.markers, other.markers).all()
    except:
      return False

  def __ne__(self, other):
    return not self.__eq__(other)

class Lap(Epoch):
  '''
  This class represents a single lap. It is a subclass of time.Epoch,
  adding a list of sector times and additional lap-specific methods.
  '''
  def __init__(self, length, offset=0, sectors=[], incomplete=False):
    super(Epoch, self).__init__()
    self._length = length
    self._offset = offset
    self._sectors = sectors

    self._incomplete = incomplete
    self._difference = None
    self.__parent__ = None

  @property
  def index(self):
    '''Gets the index of this lap relative to its parent session.'''
    return self.session.laps.index(self)

  @property
  def session(self):
    '''Get the instance of Session that this lap belongs to'''
    return self.__parent__

  @property
  def end_time(self):
    '''Gets the time (in seconds that this lap ends).
    If this lap is incomplete then end_time will be equal to the time
    of the last data sample.'''
    if self.length is not None:
      return self.offset + self.length
    else:
      if not self.sectors:
        return self.offset
      return self.offset + self.sectors[-1]

  @property
  def incomplete(self):
    '''Indicates that this lap is incomplete.'''
    return self._incomplete

  @property
  def sectors(self):
    '''Gets a list of sector times (in seconds).'''
    return self._sectors

  @property
  def difference(self):
    '''Gets the difference in time between this lap and its previous lap.'''
    if not self._difference and self.__parent__ is not None:
      self._difference = lap_difference(self.__parent__, self)
    return self._difference

  def __repr__(self):
    return '%s (%s)' % (self._length, self._sectors)

  def __eq__(self, other):
    return other and \
      self.length == other.length and \
      self.sectors == other.sectors and \
      self.offset == other.offset

  def __ne__(self, other):
    return not self.__eq__(other)

class Channel(object):
  '''This class represents a single channel within an OpenMotorsport file.'''
  def __init__(self,
              id,
              name=None,
              group=None,
              units=None,
              description=None,
              timeseries=VariableTimeSeries()):
    '''
    Contructs a new instance of Channel.

    Arguments:
      id
        The unique identifier for this channel.
      name
        The channel name. [optional]
      group
        The channel group name. [optional]
      units
        The abbreviated units of measurement for this channel. [optional]
      description
        A textual description of this channel. [optional]
      timeseries
        An initial timeseries for this channel. If none is specified, it
        will default to an empty instance of VariableTimeSeries. [optional].
    '''
    self._id = int(id)
    self._name = name
    self._group = group
    self._units = units
    self._description = description
    self._timeseries = timeseries
    self.__parent__ = None

  @property
  def session(self):
    '''Get the instance of Session that this lap belongs to'''
    return self.__parent__

  @property
  def name(self):
    '''Gets the channel name [read-only].'''
    return self._name

  @property
  def id(self):
    '''Gets the channel id [read-only].'''
    return self._id

  @property
  def identifier(self):
    '''An alias to get the channel id [read-only].'''
    return self._id

  @property
  def group(self):
    '''Gets the channel group [read-only].'''
    return self._group

  @property
  def units(self):
    '''Gets the channel units [read-only].'''
    return self._units

  @property
  def description(self):
    '''Gets the channel description [read-only].'''
    return self._description

  @property
  def timeseries(self):
    '''Gets the channel timeseries [read-only].'''
    return self._timeseries

  @property
  def min(self):
    '''Gets the minimum value of this channel [read-only].'''
    return np.min(self.timeseries.data)

  @property
  def max(self):
    '''Gets the avemaximumrage value of this channel [read-only].'''
    return np.max(self.timeseries.data)

  @property
  def average(self):
    '''Gets the average value of this channel [read-only].'''
    return np.average(self.timeseries.data)

  def __repr__(self):
    return 'Channel %s (%s)' % (self.name, self.group)

  def __eq__(self, other):
    return other and \
          self.id == other.id and \
          self.name == other.name and \
          self.group == other.group and \
          self.timeseries == other.timeseries

  def __ne__(self, other):
    return not self.__eq__(other)

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

    self.duration = None
    '''The total duration (in milliseconds) of this session [optional].'''

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

  def __ne__(self, other):
    return not self.__eq__(other)

# /----------------------------------------------------------------------/

class LazyVariableTimeSeries(VariableTimeSeries):
  '''
  A subclass of time.VariableTimeSeries that provides lazy initialisation of
  data and times.
  '''
  def __init__(self, parent, channel_id):
    '''
    Construct a new instance of LazyVariableTimeSeries.

    Arguments:
      parent
        The parent instance of openmotorsport.Session.
      channel_id
        The identifier of the channel this timeseries represents.
    '''
    self._parent = parent
    self._channel_id = channel_id
    self._loaded_data = False
    self._loaded_times = False
    VariableTimeSeries.__init__(self)

  @property
  def data(self):
    if not self._loaded_data:
      self._data = self._parent._read_channel_data(self._channel_id)
      self._loaded_data = True
    return self._data

  @property
  def times(self):
    if not self._loaded_times:
      self._times = self._parent._read_channel_times(self._channel_id)
      self._loaded_times = True
    return self._times

class LazyUniformTimeSeries(UniformTimeSeries):
  '''
  A subclass of time.UniformTimeSeries that provides lazy initialisation of data.
  '''
  def __init__(self, frequency, parent, channel_id):
    '''
    Construct a new instance of LazyUniformTimeSeries.

    Arguments:
      frequency
        The sample frequency of this channel, an instance of time.Frequency.
      parent
        The parent instance of openmotorsport.Session.
      channel_id
        The identifier of the channel this timeseries represents.
    '''
    self._parent = parent
    self._channel_id = channel_id
    self._loaded_data = False
    UniformTimeSeries.__init__(self, frequency=frequency)

  @property
  def data(self):
    if not self._loaded_data:
      self._data = self._parent._read_channel_data(self._channel_id)
      self._loaded_data = True
    return self._data

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