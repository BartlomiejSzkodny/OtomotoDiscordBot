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
import logging


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
    image_url: str | None

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.full_name,
            description=self.description,
            color=0x00ff00,
            url=self.link,
        )

        embed.add_field(name="Year", value=self.year, inline=True)
        embed.add_field(name="Mileage", value=self.mileage_km, inline=True)
        embed.add_field(name="Fuel type", value=self.fuel_type, inline=True)
        embed.add_field(name="Price", value=self.price_pln, inline=True)
        embed.set_footer(text="Car rating: " + str(round(self.Raiting, 4)))
        if self.image_url is not None:
            embed.set_thumbnail(url=self.image_url)
        return embed

    def __str__(self) -> str:
        return f"**{self.full_name}** \nCena: {self.price_pln} PLN\nWynik: {round(self.Raiting, 4)}\nPrzebieg: {self.mileage_km} \nLink {self.link}"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(hash(self.full_name) + hash(self.price_pln) + hash(self.mileage_km))

    def __eq__(self, other) -> bool:
        return self.full_name == other.full_name and self.price_pln == other.price_pln and self.mileage_km == other.mileage_km


global_car_list = []


class OtomotoScraper:
    def __init__(self, attributes: dict | None = None) -> None:
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
        if attributes is not None:
            self.attributes = attributes

        self.website = "https://www.otomoto.pl/osobowe"

        self.attributes = {
            "max_price": 60000,
            "max_odometer": 120000,
            "min_year": 2015,
            "engine_capacity": 1300,
            "car_makes": [
                "audi",
                "bmw",
                "ford",
                "toyota",
                "mitsubishi",
                "volkswagen",
                "volvo",
                "suzuki",
                "mercedes-benz",
            ],
            "android_auto": False,
            # ""
        }

    # Prep for next stage

    def autoscraper(self, max_pages: int) -> List[Car]:
        logging.log(logging.INFO, "Starting to scrape pages")
        # print(current_page)
        num_pages = 1

        current_page_num = 0
        cars_parsed = []
        while (current_page_num < num_pages and current_page_num < max_pages):
            current_page = self.create_url(current_page_num)
            logging.log(logging.INFO, "")
            response = requests.get(current_page, headers=self.headers).text
            soupified_resp = BeautifulSoup(response, "html.parser")
            offers_table = soupified_resp.find(class_="ooa-r53y0q ezh3mkl11")
            print(current_page)
            cars = offers_table.find_all(
                "article", class_="ooa-yca59n emjt7sh0")
            try:
                num_pages = int(soupified_resp.find_all(  # IDK why this doesnt work
                    "a", class_="ooa-g4wbjr eezyyk50", recursive=True)[-1].find("span").text)
            except Exception as e:
                logging.log(logging.WARNING,
                            f"Failed to gather number of pages {e}")
                num_pages = 1
            for car in cars:
                car_parsed = self.parse_tag_to_car(car)
                car_obj = Car(
                    car_parsed["link"],
                    car_parsed["full_name"],
                    car_parsed["desc"],
                    car_parsed["year"],
                    car_parsed["mileage_km"],
                    car_parsed["fuel_type"],
                    car_parsed["price_pln"],
                    car_parsed["score"],
                    car_parsed["image_url"]
                )
                cars_parsed.append(car_obj)
            current_page_num += 1
        cars_parsed = list(set(cars_parsed))
        cars_parsed.sort(key=lambda x: x.Raiting, reverse=True)
        return cars_parsed

    def create_url(self, current_page: int) -> str:
        return f"{self.website}/{'--'.join(self.attributes["car_makes"])}/od-{self.attributes['min_year']}/katowice?search%5Bdist%5D=300{"&search%5Bfilter_enum_android_auto%5D=1" if self.attributes["android_auto"] else ""}&search%5Bprivate_business%5D=business&search&search%5Bfilter_enum_damaged%5D=0&search%5Bfilter_enum_fuel_type%5D%5B0%5D=petrol&search%5Bfilter_enum_fuel_type%5D%5B1%5D=hybrid&search%5Bfilter_float_engine_capacity%3Afrom%5D={self.attributes['engine_capacity']}&search%5Bfilter_float_mileage%3Ato%5D=130000&search%5Bfilter_float_price%3Ato%5D={self.attributes['max_price']}&search%5Badvanced_search_expanded%5D=false&page={current_page}"

    def parse_tag_to_car(self, tag_element_content):
        link = tag_element_content.find(
            "h1").find('a', href=True).get('href')
        full_name = tag_element_content.find(
            "h1").find('a', href=True).text
        description = tag_element_content.find(
            "p", class_="emjt7sh10 ooa-1tku07r er34gjf0").text
        year = int(tag_element_content.find(
            "dd", {"data-parameter": "year"}).text)
        mileage_km = int(tag_element_content.find(
            "dd", {"data-parameter": "mileage"}).text[:-2].replace(" ", ""))
        fuel_type = tag_element_content.find(
            "dd", {"data-parameter": "fuel_type"}).text
        price_pln = int(tag_element_content.find(
            "h3").text.replace(" ", ""))
        img_url = None
        try:
            img_url = tag_element_content.find(
                "img", class_="e17vhtca4 ooa-2zzg2s").get('src')
        except:
            logging.log(logging.WARNING, f"Failed to get image for car {link}")

        points: int = self.convert_attrs_to_score(year, mileage_km, price_pln)

        return {
            "link": link,
            "full_name": full_name,
            "desc": description,
            "year": int(year),
            "mileage_km": mileage_km,
            "fuel_type": fuel_type,
            "price_pln": price_pln,
            "image_url": img_url,
            "score": points,
        }

    def convert_attrs_to_score(self, year: int, mileage: int, price: int):
        score = 0
        score += (10*(datetime.datetime.now().year - year) /
                  (self.attributes["min_year"]-datetime.datetime.now().year) + 10)*2
        score += (-10*mileage /
                  (self.attributes["max_odometer"]) + 10)*0.2
        score += (-10*price /
                  (self.attributes["max_price"]) + 10)*1.5
        return score

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
                pass
            except Exception as e:
                print(car)
                print(f"Failed to gather car{e}")

        return list_of_cars

    def load_attrs(self, file: str):
        with open(file=file, mode="r") as f:
            self.attributes = json.load(f)

    def save_attrs(self, file: str):
        with open(file=file, mode="w") as f:
            json.dump(self.attributes, f)

# C:\Users\szkob\Desktop\HaveToDo\otomotonew


class MyClient(discord.Client):
    async def on_ready(self):
        self.max_pages = 100
        print(f'Logged on as {self.user}!')
        self.scraper = OtomotoScraper()
        self.scraper.load_attrs("settings.json")
        self.send_message.start()

    # @tasks.loop(hours=12)
    @tasks.loop(seconds=10)
    async def send_message(self):
        channel = self.get_channel(get_channel())  # channel ID goes here
        await channel.typing()
        cars = self.scraper.autoscraper(self.max_pages)
        await channel.send("**Nowy ranking aut**")
        await channel.send(embed=cars[0].create_embed())
        await channel.send(embed=cars[1].create_embed())
        await channel.send(embed=cars[2].create_embed())


if __name__ == "__main__":
    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(filename=f'otomoto-{datetime.datetime.now().strftime("%d-%m-%Y")}.log',
                        encoding='utf-8', level=logging.DEBUG, format=FORMAT, filemode='w')
    intents = discord.Intents.default()
    client = MyClient(intents=intents)

    client.run(get_token())
    # scrape_otomoto()
