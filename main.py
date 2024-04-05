import requests

from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List
import csv
import time as t
import json
import datetime
import discord
from discord.ext import tasks
from secret_key import get_token, get_channel


@dataclass
class Car:
    link: str
    full_name: str
    description: str
    year: str
    mileage_km: str
    fuel_type: str
    price_pln: str
    Raiting: int

    def __str__(self) -> str:
        return f"{self.full_name} - {self.price_pln} PLN - {self.Raiting} points link: {self.link}"

    def __repr__(self) -> str:
        return f"{self.full_name} - {self.price_pln} PLN - {self.Raiting} points link: {self.link}"


global_car_list = []


class OtomotoScraper:
    def __init__(self, car_make: str) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.11 (KHTML, like Gecko) "
            "Chrome/23.0.1271.64 Safari/537.11",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
            "Accept-Encoding": "none",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
        }
        self.car_make = car_make

        self.website = "https://www.otomoto.pl/osobowe"

        self.attributes = {
            "max_price": 60000,
            "max_odometer": 120000,
        }

    # Prep for next stage

    def autoscraper(self, max_pages: int) -> List[Car]:
        pass

    @staticmethod
    def create_url(self, current_page: int) -> str:
        return f"{self.website}/audi--bmw--ford--mercedes-benz--suzuki--toyota--volkswagen--volvo/od-2015/katowice?search%5Bdist%5D=300&search%5Bfilter_enum_android_auto%5D=1&search%5Bprivate_business%5D=business&search&search%5Bfilter_enum_damaged%5D=0&search%5Bfilter_enum_fuel_type%5D%5B0%5D=petrol&search%5Bfilter_enum_fuel_type%5D%5B1%5D=hybrid&search%5Bfilter_float_engine_capacity%3Afrom%5D=1300&search%5Bfilter_float_mileage%3Ato%5D=130000&search%5Bfilter_float_price%3Ato%5D={self.attributes['max_price']}&search%5Badvanced_search_expanded%5D=false&page={i}"
        pass

    @staticmethod
    def parse_tag_to_car(tag_element_content):
        pass

    def scrape_pages(self, number_of_pages: int) -> List[Car]:
        cars = []
        for i in range(1, number_of_pages + 1):
            print(i)
            # /{self.car_make}osobowe?search%5Bfilter_enum_no_accident%5D=1   od-2015?search%5Bfilter_enum_no_accident%5D=1&search%5Bfilter_float_price%3Ato%5D=80000&page=2
            current_website = f"{
                self.website}/audi--bmw--ford--mercedes-benz--suzuki--toyota--volkswagen--volvo/od-2015/katowice?search%5Bdist%5D=300&search%5Bfilter_enum_android_auto%5D=1&search%5Bprivate_business%5D=business&search&search%5Bfilter_enum_damaged%5D=0&search%5Bfilter_enum_fuel_type%5D%5B0%5D=petrol&search%5Bfilter_enum_fuel_type%5D%5B1%5D=hybrid&search%5Bfilter_float_engine_capacity%3Afrom%5D=1300&search%5Bfilter_float_mileage%3Ato%5D=130000&search%5Bfilter_float_price%3Ato%5D=60000&search%5Badvanced_search_expanded%5D=false&page={i}"
            t.sleep(0.1)
            new_cars = self.scrape_cars_from_current_page(current_website)
            if new_cars:
                cars += new_cars
        return cars

    def scrape_cars_from_current_page(self, current_website: str) -> List[Car]:
        try:
            response = requests.get(current_website, headers=self.headers).text
            soup = BeautifulSoup(response, "html.parser")
            cars = self.extract_cars_from_page(soup)
            return cars
        except Exception as e:
            print(
                f"Problem with scraping website: {current_website}, reason: {e}")
            return []

    def extract_cars_from_page(self, soup: BeautifulSoup) -> List[Car]:
        offers_table = soup.find(class_="ooa-r53y0q ezh3mkl11")
        # fix find all
        # print(offers_table)
        cars = offers_table.find_all("article", class_="ooa-yca59n emjt7sh0"
                                     )
        list_of_cars = []
        is_listing = True
        for car in cars:
            if not "sprzedawca" in car.text:
                is_listing = False
            try:
                link = car.find(
                    "h1").find('a', href=True).get('href')
                print("a")
                full_name = car.find(
                    "h1").find('a', href=True).text
                print("b")
                description = car.find(
                    "p", class_="emjt7sh10 ooa-1tku07r er34gjf0").text
                year = car.find("dd", {"data-parameter": "year"}).text
                mileage_km = car.find("dd", {"data-parameter": "mileage"}).text
                fuel_type = car.find(
                    "dd", {"data-parameter": "fuel_type"}).text
                price_pln = car.find(
                    "h3").text
                points: int = 0
                helpyear = int(year)
                currentDateTime = datetime.datetime.now()
                current_year = currentDateTime.date().year
                if ((current_year-helpyear) <= 3):
                    points += 5
                elif ((current_year-helpyear) <= 5):
                    points += 4
                elif ((current_year-helpyear) <= 6):
                    points += 3
                elif ((current_year-helpyear) <= 10):
                    points += 2
                elif ((current_year-helpyear) <= 12):
                    points += 1
                helpmileage_km: int = int(mileage_km[:-2].replace(" ", ""))
                if (helpmileage_km <= 50000):
                    points += 5
                elif (helpmileage_km <= 60, 000):
                    points += 4
                elif (helpmileage_km <= 80, 000):
                    points += 3
                elif (helpmileage_km <= 100, 000):
                    points += 2
                elif (helpmileage_km <= 150, 000):
                    points += 2

                helpprice: int = int(price_pln[:-3].replace(" ", ""))
                if (price_pln[-2] != 'U'):
                    if (helpprice <= 30, 000):
                        points += 5
                    elif (helpprice <= 40, 000):
                        points += 4
                    elif (helpprice <= 45, 000):
                        points += 3
                    elif (helpprice <= 50, 000):
                        points += 2
                    elif (helpprice <= 60, 000):
                        points += 1
                if (points > 10):
                    global_car_list.append(Car(
                        link=link,
                        full_name=full_name,
                        description=description,
                        year=int(year),
                        mileage_km=mileage_km,
                        fuel_type=fuel_type,
                        price_pln=int(price_pln.replace(" ", "")),
                        Raiting=points
                    ))

                list_of_cars.append(Car(
                    link=link,
                    full_name=full_name,
                    description=description,
                    year=int(year),
                    mileage_km=mileage_km,
                    fuel_type=fuel_type,
                    price_pln=int(price_pln.replace(" ", "")),
                    Raiting=points
                ))
            except Exception as e:
                print(car)
                print(f"Failed to gather car{e}")

        return list_of_cars

# C:\Users\szkob\Desktop\HaveToDo\otomotonew


def write_to_csv(cars: List[Car]) -> None:
    with open("cars.csv", mode="w") as f:
        fieldnames = [
            "link",
            "full_name",
            "description",
            "year",
            "mileage_km",
            "fuel_type",
            "price_pln",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for car in cars:
            writer.writerow(asdict(car))


def write_to_json(cars: List[Car]) -> None:
    with open("cars.json", mode="w") as f:
        json.dump([asdict(car) for car in cars], f)


def scrape_otomoto() -> tuple[List[Car], Car]:
    make = "polonez"
    scraper = OtomotoScraper(make)
    cars = scraper.scrape_pages(2)
    write_to_json(cars)
    # Get the car with the highest rating
    best_car = max(cars, key=lambda car: car.Raiting)
    print(best_car)
    return cars, best_car


class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.send_message.start()

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

    # @tasks.loop(hours=12)
    @tasks.loop(seconds=10)
    async def send_message(self):
        channel = self.get_channel(get_channel())  # channel ID goes here
        cars, best_car = scrape_otomoto()
        await channel.send(best_car)


if __name__ == "__main__":
    intents = discord.Intents.default()
    client = MyClient(intents=intents)

    client.run(get_token())
    # scrape_otomoto()
