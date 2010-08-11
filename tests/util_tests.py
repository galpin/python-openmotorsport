import unittest

from openmotorsport.openmotorsport import Session, Channel, Metadata, Lap
from openmotorsport.utils import *

class UtilsTests(unittest.TestCase):

  def testLapDifference(self):
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertEquals(lap_difference(session, session.laps[0]), None)
    self.assertEquals(lap_difference(session, session.laps[1]), 10.0)
    self.assertEquals(lap_difference(session, session.laps[2]), -20.0)
    self.assertEquals(lap_difference(session, session.laps[2]), session.laps[2].difference)
    self.assertEquals(lap_difference(session, session.laps[1]), session.laps[1].difference)
    self.assertEquals(lap_difference(session, session.laps[0]), session.laps[0].difference)

  def testFastestLapTime(self):
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertEquals(fastest_lap_time(session), 20.0)

    # no markers at all
    session = Session()
    session.num_sectors = 2
    session.markers = []
    self.assertEquals(fastest_lap_time(session), None)

    # no complete laps
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0]
    self.assertEquals(fastest_lap_time(session), None)

  def testFastestLap(self):
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertEquals(fastest_lap(session), session.laps[2])
    self.assertTrue(is_fastest_lap(session, session.laps[2]))

    # no markers at all
    session = Session()
    session.num_sectors = 2
    session.markers = []
    self.assertEquals(fastest_lap(session), None)

    # no complete laps
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0]
    self.assertEquals(fastest_lap(session), None)

  def testFastestSector(self):
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertEquals(fastest_sector(session, 1), 5.0)
    self.assertEquals(fastest_sector(session, 2), 5.0)

    # no markers at all
    session = Session()
    session.num_sectors = 2
    session.markers = []
    self.assertEquals(fastest_sector(session, 1), None)

    # no complete laps
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0]
    self.assertEquals(fastest_sector(session, 2), 10.0)

  def testIsFastestSector(self):
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertTrue(is_fastest_sector(session, 1, 5.0))
    self.assertTrue(is_fastest_sector(session, 2, 5.0))

    # no markers at all
    session = Session()
    session.num_sectors = 2
    session.markers = []
    self.assertEquals(fastest_sector(session, 1), None)

    # no complete laps
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0]
    self.assertEquals(fastest_sector(session, 2), 10.0)