import json
import requests
from enum import Enum

BASE_URL = 'https://api.guap.ru/rasp/v1'

DAYS = [
    'Понедельник',
    'Вторник',
    'Среда',
    'Четверг',
    'Пятница',
    'Суббота'
]

class Week(Enum):
    ALL = 1
    ONE = 2
    TWO = 3

class Lesson(object):
    def __init__(
        self, 
        id: str, 
        number: int, 
        week: Week, 
        begin: str, 
        end: str, 
        api_type: str, 
        disc: str, 
        chairId: str, 
        groupsAisIds: list[str], 
        prepsAisIds: list[str], 
        roomsIds: list[str],
        is_exist: bool = False
    ):
        self.id = id
        self.number = number
        self.week = week
        self.api_type  = api_type
        self.disc = disc
        self.chairId = chairId
        self.groupsAisIds = groupsAisIds
        self.prepsAisIds = prepsAisIds
        self.roomsIds = roomsIds
        self.begin = begin
        self.end = end
        self.is_exist = is_exist

    def __str__(self):
        return (
            f"Lesson(\n"
            f"  id={self.id},\n"
            f"  number={self.number},\n"
            f"  week={self.week},\n"
            f"  begin={self.begin},\n"
            f"  end={self.end},\n"
            f"  api_type={self.api_type},\n"
            f"  disc={self.disc},\n"
            f"  chairId={self.chairId},\n"
            f"  groupsAisIds={self.groupsAisIds},\n"
            f"  prepsAisIds={self.prepsAisIds},\n"
            f"  roomsIds={self.roomsIds}\n"
            f")"
        )

class Day(object):
    def __init__(self, id: str, title: str, lessons: list[Lesson]):
        self.id: str = id
        self.title: str = title
        self.lessons: list[Lesson] = lessons

    def get_lessons_by_week(self, week: Week):
        return [el for el in self.lessons if el.week == week]

    def __str__(self):
        return (
            f"Day(\n"
            f"  id={self.id},\n"
            f"  title={self.title},\n"
            f"  lessons=[\n    " +
            ",\n    ".join(str(lesson) for lesson in self.lessons) +
            "\n  ]\n)"
        )

class Room(object):
    def __init__(self, id, title):
        self.id = id
        self.title = title
        self.loaded: bool = False
        self.days: list[Day] = []

    def __str__(self):
        return (
            f"Room(\n"
            f"  id={self.id},\n"
            f"  title={self.title},\n"
            f"  loaded={self.loaded},\n"
            f"  days=[\n    " +
            ",\n    ".join(str(day) for day in self.days) +
            "\n  ]\n)"
        )

    def serilize(self):
        result = requests.get(
            f'{BASE_URL}/get-rasp-full?groupAisId=0&prepAisId=0&chairId=0&roomId={self.id}'
        ).json()

        for day in result['days']:
            lessons_by_number: dict[int, list[Lesson]] = {}
            for lesson in day['lessons']:
                lesson_number = lesson['less']
                begin_time = lesson['begin']
                end_time = lesson['end']

                week_mapping = {
                    'weekAll': Week.ALL,
                    'week1': Week.ONE,
                    'week2': Week.TWO
                }

                for week_key, week_type in week_mapping.items():
                    if week_key in lesson:
                        week_data = lesson[week_key]
                        for week_item in week_data:
                            new_lesson = Lesson(
                                id=week_item['id'],
                                number=lesson_number,
                                week=week_type,
                                begin=begin_time,
                                end=end_time,
                                api_type=week_item['type'],
                                disc=week_item['dics'],
                                chairId=week_item['chairId'],
                                groupsAisIds=week_item['groupsAisIds'],
                                prepsAisIds=week_item['prepsAisIds'],
                                roomsIds=week_item['roomsIds'],
                                is_exist=True
                            )
                            if lesson_number not in lessons_by_number:
                                lessons_by_number[lesson_number] = []
                            lessons_by_number[lesson_number].append(new_lesson)

            lessons_serilized = []
            for lesson_group in lessons_by_number.values():
                lessons_serilized.extend(lesson_group)

            self.days.append(Day(day['day'], day['title'], lessons_serilized))

        self.loaded = True

class Building(object):
    def __init__(self, id, title, rooms):
        self.id: str = id
        self.title: str = title
        self.rooms: list[Room] = rooms

    def __str__(self):
        return (
            f"Building(\n"
            f"  id={self.id},\n"
            f"  title={self.title},\n"
            f"  rooms=[\n    " +
            ",\n    ".join(str(room) for room in self.rooms) +
            "\n  ]\n)"
        )

    def get_room_by_id(self, id) -> Room:
        return next((room for room in self.rooms if room.id == id), None)

    def get_room_by_title(self, title) -> Room:
        return next((room for room in self.rooms if room.title == title), None)

class Schedule(object):
    def __init__(self):
        self.buildings: list[Building] = []
        self.loaded: bool = False

    def __str__(self):
        return (
            f"Schedule(\n"
            f"  loaded={self.loaded},\n"
            f"  buildings=[\n    " +
            ",\n    ".join(str(building) for building in self.buildings) +
            "\n  ]\n)"
        )

    def serilize(self):
        buildings = requests.get(f'{BASE_URL}/get-buildings').json()
        for building in buildings:
            rooms = [Room(room['id'], room['title']) for room in building['rooms']]
            self.buildings.append(Building(building['id'], building['title'], rooms))
        self.loaded = True

    def get_building_by_id(self, id) -> Building:
        return next((b for b in self.buildings if b.id == id), None)

    def get_building_by_title(self, title) -> Building:
        return next((b for b in self.buildings if b.title == title), None)

class Search(object):
    def __init__(self):
        self.schedule: Schedule = Schedule()
        self.building: Building = None
        self.room: Room = None
        self.day: Day = None
        self.lessons: list[Lesson] = []

    def get_building(self, building_title: str):
        self.schedule.serilize()
        self.building = self.schedule.get_building_by_title(building_title)
        print(f'Выбрано здание: {self.building.title}')
        return self

    def get_room(self, room_title: str):
        self.room = self.building.get_room_by_title(room_title)
        self.room.serilize()
        print(f'Выбрана аудитория: {self.room.title}')
        return self

    def get_day(self, day_title):
        if day_title in DAYS:
            for day in self.room.days:
                if day.title == day_title:
                    self.day = day
                    print(f'Выбран день: {day_title}')
                    return self
        print("Не удалось выбрать день")
        return self

    def get_lesson(self, number):
        self.lessons = [lesson for lesson in self.day.lessons if lesson.number == number]
        print(f'Выбрана пара № {number}')
        return self

    def get_is_free(self):
        if not self.lessons:
            print('Аудитория свободна')
        else:
            for lesson in self.lessons:
                if lesson.week == Week.ALL:
                    print('Аудитория всегда занята')
                elif lesson.week == Week.ONE:
                    print('Аудитория занята на верхней неделе')
                elif lesson.week == Week.TWO:
                    print('Аудитория занята на нижней неделе')
        return self

s = Search()
s.get_building('Ленсовета 14').get_room('14-09').get_day('Понедельник')
for i in range(1, 7):
    s.get_lesson(i).get_is_free()