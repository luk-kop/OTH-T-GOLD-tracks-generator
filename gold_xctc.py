import random
import string
from datetime import datetime
from typing import Optional

from ctc_data import CtcFlag, CtcType, CtcCategory


class IdGenerator:
    """
    Simple ID generator.
    """
    def __init__(self, start=1):
        self.id = start

    def __iter__(self):
        return self

    def __next__(self):
        current_id = self.id
        self.id += 1
        return current_id


class GoldCtc:
    """
    A class representing CTC OTG set.
    """
    name_id = IdGenerator()

    def __init__(self, name: str = 'TEST'):
        self.track_number = f'T{random.randrange(100, 99_999):05d}'
        self.class_name = f'UNEQUATED-{name}{next(GoldCtc.name_id)}'
        self.trademark = ''
        self.type = CtcType.get_random_name()
        self.category = CtcCategory.get_random_name()
        self.pennant_number = f'{random.choice(["D", "A", "M", "F", "P", ""])}{random.randrange(10, 9_999)}'
        self.flag = CtcFlag.get_random_name()
        self.sconum = ''
        self.selective_id = ''
        self.alert_code = random.choice(['', 'TGT', 'SUS', 'HIT', 'NSP'])
        while True:
            force_code = random.randrange(1, 58)
            # Exclude 33-37
            if force_code not in list(range(33, 38)):
                self.force_code = f'{force_code:02d}'
                break
        self.system_track_no = ''
        self.track_type = ''
        self.average_speed = f'{str(random.randint(0, 50))}'
        self.average_time_on_leg = ''
        self.discrete_id = ''
        self.uid = f'{random.choice(["ORP", "FGS", "LLL", "COM", "LAV", "PLN"])}' \
                   f'{random.randrange(1_000_000, 999_999_999):09d}'
        self.ircs = ''.join(random.sample(string.ascii_uppercase, 4))
        self.suspicion_code = random.choice([f'{random.randrange(1, 11):02d}', ''])
        self.emitter_voice_cs = ''

    def get_all_attr(self):
        return [value for value in self.__dict__.values()]

    def __str__(self):
        separator = '/'
        return f'CTC/{separator.join(self.get_all_attr())}'.rstrip(separator)


class GoldXpos:
    """
    A class representing XPOS OTG set.
    """
    def __init__(self, position: Optional[tuple] = None, date_time: Optional[datetime] = None):
        self.date_time_group = date_time
        self.month_year = f'{datetime.utcnow().strftime("%b").upper()}{datetime.utcnow().strftime("%y")}'
        self.position = position
        self.sensor_code = random.choice(['', 'RADAR', 'VISUAL', 'UNK', 'PHOTO', 'SRN25', 'IFF', 'IR'])
        self.bearing_of_major_axis = ''
        self.length_of_semi_major_axis = ''
        self.length_of_semi_minor_axis = ''
        self.course = f'{random.randint(0, 359):03d}.{random.randint(0, 9)}T'
        self.speed = f'{random.randint(0, 50)}KTS'
        self.altitude = ''
        self.depth = ''
        self.rdf_rf = ''
        self.source_code = random.choice(['', 'EST', 'NTDS', 'UNK'])
        self.seq_contact_id = ''
        self.photos = ''
        self.total_no_of_contacts = ''

    @property
    def date_time_group(self):
        """
        Returns date-time group in format - 15200228Z0
        """
        return self._date_time_group

    @date_time_group.setter
    def date_time_group(self, value):
        if not value:
            value = datetime.utcnow()
        date = f'{value.strftime("%d%H%M%S")}'
        self._date_time_group = f'{date}Z{self._check_sum(date)}'

    def date_time_group_datetime(self):
        """
        Returns date and time of position (month_year and date_time_group attrs) as a datetime object.
        """
        return datetime.strptime(f"{self.month_year}{self.date_time_group[:-2]}", "%b%y%d%H%M%S")

    @property
    def position(self):
        """
        Returns position in format - LL:552521N0-0163311E5
        """
        return self._position

    @position.setter
    def position(self, value: tuple):
        if not value:
            # Random position
            latitude = f'{random.randrange(0, 90):02d}{random.randrange(0, 60):02d}{random.randrange(0, 60):02d}'
            longitude = f'{random.randrange(0, 180):03d}{random.randrange(0, 60):02d}{random.randrange(0, 60):02d}'
            latitude_dir = random.choice(['N', 'S'])
            longitude_dir = random.choice(['E', 'W'])
            position = f'LL:{latitude}{latitude_dir}{self._check_sum(latitude)}-' \
                       f'{longitude}{longitude_dir}{self._check_sum(longitude)}'
        else:
            # The position specified by the user
            latitude, latitude_dir, longitude, longitude_dir = value
            position = f'LL:{latitude}{latitude_dir}{self._check_sum(latitude)}-' \
                       f'{longitude}{longitude_dir}{self._check_sum(longitude)}'
        self._position = position

    @staticmethod
    def _check_sum(value: str):
        """
        Calculate checksum
        """
        return sum([int(num) for num in value]) % 10

    def get_all_attr(self):
        return [value for value in self.__dict__.values()]

    def __str__(self):
        separator = '/'
        return f'XPOS/{separator.join(self.get_all_attr())}'.rstrip(separator)


class GoldTrack:
    """
    A class representing a single track
    """
    def __init__(self, position: Optional[tuple] = None):
        self.ctc = GoldCtc()
        self.xpos = GoldXpos(position)
        # True if data in CTC or XPOS has been changed
        self.changed = True

    def __str__(self):
        return f'{self.ctc}\n{self.xpos}\n'
