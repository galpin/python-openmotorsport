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
    session.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0, 100.0, 110.0, 115.0]
    self.assertEquals(fastest_lap(session), session.laps[2])
    self.assertTrue(is_fastest_lap(session, session.laps[2]))

    # test the next fastest lap
    self.assertEquals(fastest_or_next_fastest_lap(fastest_lap(session)), session.laps[3])
    self.assertEquals(fastest_or_next_fastest_lap(session.laps[1]), fastest_lap(session))
    self.assertEquals(fastest_or_next_fastest_lap(session.laps[0]), fastest_lap(session))


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

  def testSlowestLap(self):
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0, 100.0, 110.0, 115.0]
    self.assertEquals(fastest_lap(session), session.laps[2])
    self.assertTrue(is_fastest_lap(session, session.laps[2]))

    # test the slowest lap
    self.assertEquals(slowest_lap(session), session.laps[1])

    # test the next slowest lap
    self.assertEquals(slowest_or_next_slowest_lap(slowest_lap(session)), session.laps[3])
    self.assertEquals(slowest_or_next_slowest_lap(session.laps[1]), session.laps[0])
    self.assertEquals(slowest_or_next_slowest_lap(session.laps[2]), slowest_lap(session))

  def testNextPrevious(self):
    session = Session()
    session.num_sectors = 2
    session.markers = [10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 75.0, 80.0, 90.0]
    self.assertEquals(fastest_lap(session), session.laps[2])
    self.assertTrue(is_fastest_lap(session, session.laps[2]))

    # test the next lap
    self.assertEquals(next_lap(session.laps[0]), session.laps[1])
    self.assertEquals(next_lap(session.laps[1]), session.laps[2])
    self.assertEquals(next_lap(session.laps[2]), None)

    # test the previous lap
    self.assertEquals(previous_lap(session.laps[0]), None)
    self.assertEquals(previous_lap(session.laps[1]), session.laps[0])
    self.assertEquals(previous_lap(session.laps[2]), session.laps[1])

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