#!/usr/bin/env python3
"""Generate a synthetic catalog for the prefix-search assignment."""
from __future__ import annotations

import argparse
import random
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from pathlib import Path

UNITS_DISPLAY = {
    "g": "г",
    "kg": "кг",
    "ml": "мл",
    "l": "л",
    "pcs": "шт",
    "packs": "уп.",
    "sachets": "саше",
    "caps": "капс.",
    "tabs": "табл.",
    "bag": "меш",
}

BASE_PRODUCTS = [
    {"base_name": "Масло сливочное", "category": "Молочные продукты", "brands": ["Alpine Meadow", "Nordic Farm", "Polar Valley", "Teos", "Северное поле"], "descriptors": ["традиционное 82%", "фермерское", "премиум", "безлактозное", "крестьянское"], "units": (("g", [180, 200, 225, 400, 450, 500]), ("kg", [1])), "keywords": ["масло", "сливочное", "butter"], "price": (249, 820), "package_sizes": [1, 2, 4]},
    {"base_name": "Молоко ультрапастеризованное", "category": "Молочные продукты", "brands": ["Morning Dew", "Blue Valley", "Домашний запас", "NordMilk", "FarmLab"], "descriptors": ["3.2%", "1%", "фермерское", "безлактозное", "Premium"], "units": (("ml", [500, 900, 950, 1000, 1400]), ("l", [1, 1.5])), "keywords": ["молоко", "ультрапастеризованное", "milk"], "price": (69, 210), "package_sizes": [1, 4, 6]},
    {"base_name": "Йогурт греческий", "category": "Молочные продукты", "brands": ["Blue Isles", "Teos", "Mediterran", "Ionian", "Mykonos"], "descriptors": ["натуральный", "без сахара", "персик", "черника", "protein"], "units": (("g", [140, 150, 170, 500, 900]),), "keywords": ["йогурт", "греческий", "greek"], "price": (59, 280), "package_sizes": [1, 4, 12]},
    {"base_name": "Творог зерненый", "category": "Молочные продукты", "brands": ["Белая ферма", "Nordic Farm", "Village Craft", "Alpine Meadow"], "descriptors": ["5%", "9%", "классический", "с пикантной солью", "органический"], "units": (("g", [200, 300, 400, 500]),), "keywords": ["творог", "зерненый", "cottage cheese"], "price": (99, 330), "package_sizes": [1, 2, 6]},
    {"base_name": "Масло подсолнечное", "category": "Бакалея", "brands": ["Golden Field", "Южное", "Rosa", "Helio", "ChefPro"], "descriptors": ["рафинированное", "нерафинированное", "premium", "organic", "для HoReCa"], "units": (("ml", [500, 900, 1000, 3000, 5000, 10000]),), "keywords": ["масло", "подсолнечное", "растительное", "sunflower", "10л"], "price": (110, 1800), "package_sizes": [1, 3, 6]},
    {"base_name": "Масло оливковое", "category": "Бакалея", "brands": ["La Toscana", "Mediterran", "Oro Verde", "Gusto", "ChefPro"], "descriptors": ["Extra Virgin", "Classico", "для салатов", "для жарки"], "units": (("ml", [250, 500, 750, 1000, 3000]),), "keywords": ["масло", "оливковое", "olive oil"], "price": (390, 3200), "package_sizes": [1, 2, 4]},
    {"base_name": "Мука пшеничная", "category": "Бакалея", "brands": ["Старый Мельник", "Alfa Mill", "BakeryPro", "Деревенская"], "descriptors": ["в/с", "цельнозерновая", "натуральная", "HoReCa 25 кг"], "units": (("g", [900, 2000]), ("kg", [5, 10, 25])), "keywords": ["мука", "пшеничная", "flour"], "price": (65, 2100), "package_sizes": [1, 5, 10]},
    {"base_name": "Крупа гречневая", "category": "Бакалея", "brands": ["Северные поля", "GrainLab", "EcoBag", "Русская крупа"], "descriptors": ["ядрица", "быстрого приготовления", "organic", "HoReCa"], "units": (("g", [800, 900, 1000]), ("kg", [5, 15])), "keywords": ["крупа", "гречка", "buckwheat"], "price": (79, 980), "package_sizes": [1, 4, 8]},
    {"base_name": "Макароны из твердых сортов", "category": "Бакалея", "brands": ["Pasta Nova", "La Linea", "Grano Duro", "Rustica"], "descriptors": ["спагетти", "перья", "ракушки", "fusilli", "penne"], "units": (("g", [400, 450, 500, 900]), ("kg", [5])), "keywords": ["макароны", "паста", "durum", "pasta"], "price": (69, 750), "package_sizes": [1, 5, 10]},
    {"base_name": "Минеральная вода", "category": "Напитки", "brands": ["San Pellegrino", "Aqua Pura", "Samokat Springs", "Arctic Light"], "descriptors": ["сильногазированная", "негазированная", "citrus", "premium glass"], "units": (("ml", [500, 750, 1000]), ("l", [1, 1.5])), "keywords": ["вода", "минеральная", "sanpellegrino", "sparkling"], "price": (49, 420), "package_sizes": [1, 6, 12]},
    {"base_name": "Газированный напиток", "category": "Напитки", "brands": ["Garage", "Citrico", "Fresh Bar", "Volt"], "descriptors": ["грейпфрут", "zero sugar", "berry", "ginger"], "units": (("ml", [330, 500, 1000]), ("l", [1.5])), "keywords": ["газировка", "drink", "garage", "fresh"], "price": (39, 220), "package_sizes": [1, 12, 24]},
    {"base_name": "Кофе в зёрнах", "category": "Кофе и чай", "brands": ["Ristretto Lab", "BaristaPro", "Nord Roast", "Arabica 24"], "descriptors": ["espresso", "medium roast", "dark roast", "ethiopia", "specialty"], "units": (("g", [200, 250, 500, 1000]),), "keywords": ["кофе", "зерновой", "coffee beans"], "price": (390, 2800), "package_sizes": [1, 2, 4]},
    {"base_name": "Чай листовой", "category": "Кофе и чай", "brands": ["Greenfield", "Ahmad", "Samokat", "Orient Leaf"], "descriptors": ["чёрный", "зелёный", "жасмин", "улун", "матча"], "units": (("g", [75, 90, 100, 250]),), "keywords": ["чай", "листовой", "tea", "xfq"], "price": (120, 760), "package_sizes": [1, 2, 6]},
    {"base_name": "Шоколад премиальный", "category": "Кондитерские изделия", "brands": ["Bon Paris", "Noir Artisan", "Lattea", "Nordic Choco"], "descriptors": ["70%", "молочный", "с карамелью", "с орехами", "без сахара"], "units": (("g", [80, 90, 100, 200]),), "keywords": ["шоколад", "bon paris", "chocolate"], "price": (79, 520), "package_sizes": [1, 3, 6]},
    {"base_name": "Мармелад жевательный", "category": "Кондитерские изделия", "brands": ["Bon Paris", "Happy Llama", "Fruity", "KidsBox"], "descriptors": ["ягодный", "кола", "sour", "mix", "витаминный"], "units": (("g", [75, 90, 150, 250]),), "keywords": ["мармелад", "bon paris", "gummies"], "price": (49, 240), "package_sizes": [1, 5, 12]},
    {"base_name": "Подгузники детские", "category": "Детские товары", "brands": ["BabySoft", "PampKids", "EcoBaby", "Huggsy"], "descriptors": ["размер 2", "размер 3", "ночные", "premium", "для чувствительной кожи"], "units": (("pcs", [26, 32, 40, 60, 96]),), "keywords": ["подгузники", "памперсы", "diapers"], "price": (390, 2200), "package_sizes": [1, 2, 4]},
    {"base_name": "Пюре фруктовое", "category": "Детские товары", "brands": ["FruitGo", "Little Spoon", "Фрутти", "Organic Kid"], "descriptors": ["яблоко-груша", "манго", "тыква", "без сахара", "злаки"], "units": (("g", [90, 100, 120]),), "keywords": ["пюре", "детское", "puree"], "price": (35, 140), "package_sizes": [1, 12, 24]},
    {"base_name": "Гель для душа", "category": "Косметика и гигиена", "brands": ["Nordic Care", "Daily Ritual", "AquaVera", "Sense"], "descriptors": ["увлажняющий", "цитрус", "men", "sensitive", "family pack"], "units": (("ml", [250, 400, 500, 750]),), "keywords": ["гель", "душ", "body wash"], "price": (99, 460), "package_sizes": [1, 3, 6]},
    {"base_name": "Крем для рук", "category": "Косметика и гигиена", "brands": ["Herbal Line", "Care&Go", "Nordic Care", "Atelier Skin"], "descriptors": ["питательный", "антибактериальный", "спа", "коллаген", "витамин Е"], "units": (("ml", [50, 75, 100, 150]),), "keywords": ["крем", "для рук", "hand cream"], "price": (79, 520), "package_sizes": [1, 4, 12]},
    {"base_name": "Средство для мытья посуды", "category": "Бытовая химия", "brands": ["Clean&Shine", "Crystal Drop", "BioClean", "AllDish"], "descriptors": ["лимон", "эко", "для детской посуды", "концентрат", "professional"], "units": (("ml", [450, 750, 1000, 1500]),), "keywords": ["моющее", "посуд", "dish", "посудомойка"], "price": (79, 360), "package_sizes": [1, 3, 6]},
    {"base_name": "Стиральный порошок", "category": "Бытовая химия", "brands": ["SoftClean", "NordWash", "ArielPro", "EcoSphere"], "descriptors": ["color", "белое", "для детей", "capsules", "professional"], "units": (("g", [400, 800, 3000]), ("ml", [1500, 3000])), "keywords": ["стирка", "порошок", "detergent"], "price": (150, 1900), "package_sizes": [1, 2, 4]},
    {"base_name": "Пакеты для мусора", "category": "Хозяйственные товары", "brands": ["CleanUp", "EcoBag", "StrongHold", "DailyFix"], "descriptors": ["30л", "60л", "120л", "с завязками", "прочные"], "units": (("pcs", [15, 20, 30, 50]),), "keywords": ["пакеты", "мусор", "trash bags"], "price": (49, 310), "package_sizes": [1, 3, 6]},
    {"base_name": "Полотенца бумажные", "category": "Хозяйственные товары", "brands": ["SoftRoll", "Clean&Go", "PureLine", "MaxiRoll"], "descriptors": ["двухслойные", "кухонные", "mega roll", "эко"], "units": (("pcs", [2, 4, 6, 8]),), "keywords": ["бумажные", "полотенца", "paper towels"], "price": (79, 420), "package_sizes": [1, 3, 6]},
    {"base_name": "Корм для кошек сухой", "category": "Зоотовары", "brands": ["FrisCat", "NordPet", "PerfectTail", "CatCraft"], "descriptors": ["adult", "sterilised", "lamb", "indoor", "hairball"], "units": (("g", [400, 1500]), ("kg", [5, 10])), "keywords": ["корм", "кошек", "cat food", "adult"], "price": (210, 4200), "package_sizes": [1, 2, 4]},
    {"base_name": "Корм для собак гипоаллергенный", "category": "Зоотовары", "brands": ["DogForce", "NordPet", "Happy Tail", "VetPro"], "descriptors": ["mini", "medium", "large", "salmon", "grain free"], "units": (("g", [800, 1500]), ("kg", [5, 12])), "keywords": ["корм", "собак", "dog food", "hypo"], "price": (390, 5200), "package_sizes": [1, 2, 4]},
    {"base_name": "Овощи замороженные", "category": "Заморозка", "brands": ["Polar Mix", "FreshFreezer", "VeggieBox", "NordHarvest"], "descriptors": ["овощная смесь", "брокколи", "цветная капуста", "со стручками", "для супа"], "units": (("g", [400, 450, 600, 1000]),), "keywords": ["замороженные", "овощи", "frozen veggies"], "price": (79, 520), "package_sizes": [1, 5, 10]},
    {"base_name": "Филе грудки индейки", "category": "Мясо и птица", "brands": ["Золотая птица", "FarmLine", "ProteinPro", "Chef's Choice"], "descriptors": ["охлажденное", "для стейков", "в маринаде", "HoReCa"], "units": (("g", [500, 700, 1000]), ("kg", [5])), "keywords": ["филе", "индейка", "turkey fillet"], "price": (230, 1800), "package_sizes": [1, 2, 5]},
    {"base_name": "Стейк лосося", "category": "Рыба и морепродукты", "brands": ["Polar Sea", "Nordic Fish", "AquaChef", "BlueWave"], "descriptors": ["шоковая заморозка", "охлажденный", "premium", "дикого лосося"], "units": (("g", [300, 400, 600]), ("kg", [5])), "keywords": ["лосось", "стейк", "salmon"], "price": (390, 3600), "package_sizes": [1, 2, 5]},
    {"base_name": "Сыр гауда", "category": "Сыры", "brands": ["Dutch Yard", "Cheese&Co", "Nordic Cheese", "ChefPro"], "descriptors": ["резаный", "кусок", "для сендвичей", "HoReCa 5кг", "выдержанный"], "units": (("g", [200, 300, 500]), ("kg", [1, 2, 5])), "keywords": ["сыр", "гауда", "gouda"], "price": (220, 2800), "package_sizes": [1, 2, 4]},
    {"base_name": "Сыр чеддер", "category": "Сыры", "brands": ["Cheddar Club", "Britmilk", "ChefPro", "Orange Field"], "descriptors": ["mature", "mild", "для бургера", "HoReCa 5кг"], "units": (("g", [200, 400]), ("kg", [2.5, 5])), "keywords": ["сыр", "чеддер", "cheddar", "5kg"], "price": (240, 3500), "package_sizes": [1, 2, 4]},
    {"base_name": "Вино игристое", "category": "Алкоголь", "brands": ["Prosecco Alto", "Rieslinghaus", "Mosel Craft", "Premium Cellar"], "descriptors": ["prosecco", "rose", "brut", "riesling mosel", "sanpellegrino spritz"], "units": (("ml", [750, 1500]),), "keywords": ["вино", "prosecco", "riesling", "premium"], "price": (790, 4200), "package_sizes": [1, 3, 6]},
    {"base_name": "Джин премиальный", "category": "Алкоголь", "brands": ["Nordic Gin", "Garage Barrel", "Juniper Lane", "Volt Spirit"], "descriptors": ["botanical", "citrus", "barrel aged", "grapefruit"], "units": (("ml", [500, 700, 1000]),), "keywords": ["джин", "gin", "garage", "grapefruit"], "price": (1290, 5200), "package_sizes": [1, 2, 3]},
    {"base_name": "Энергетический напиток", "category": "Напитки", "brands": ["Volt", "Litl Energy", "Power Node", "HyperFox"], "descriptors": ["classic", "zero", "berry mix", "citrus", "маракуйя"], "units": (("ml", [250, 330, 500]),), "keywords": ["energy", "литл", "энергетик"], "price": (55, 210), "package_sizes": [1, 6, 12]},
    {"base_name": "Витаминный комплекс", "category": "Аптека", "brands": ["VitaCore", "DailyVits", "Immuno+", "Nordic Health"], "descriptors": ["иммунитет", "женский", "мужской", "kids", "omega"], "units": (("tabs", [30, 60, 90]),), "keywords": ["витамины", "комплекс", "supplement"], "price": (190, 1800), "package_sizes": [1, 2, 4]},
    {"base_name": "Шампунь питательный", "category": "Косметика и гигиена", "brands": ["Herbal Line", "Nordic Care", "Pure Roots", "GlowUp"], "descriptors": ["для объема", "гладкость", "men", "color care"], "units": (("ml", [250, 400, 500, 750]),), "keywords": ["шампунь", "hair", "shampoo"], "price": (120, 540), "package_sizes": [1, 2, 6]},
    {"base_name": "Зубная паста", "category": "Косметика и гигиена", "brands": ["White Smile", "ProDent", "HerbalDent", "KidsDent"], "descriptors": ["отбеливающая", "sensitive", "fresh mint", "детская"], "units": (("ml", [75, 100, 125]),), "keywords": ["зубная", "паста", "toothpaste"], "price": (79, 380), "package_sizes": [1, 3, 6]},
    {"base_name": "Адаптер USB-C", "category": "Электроника", "brands": ["ChargeLab", "VoltEdge", "TechNode", "HyperPort"], "descriptors": ["65W", "35W", "dual port", "gan", "travel"], "units": (("pcs", [1]),), "keywords": ["adapter", "usb c", "type-c", "зарядное"], "price": (690, 3690), "package_sizes": [1, 2]},
    {"base_name": "Кабель USB-C", "category": "Электроника", "brands": ["ChargeLab", "VoltEdge", "FlexWire", "TechNode"], "descriptors": ["1м", "2м", "PD 100W", "textile", "magnetic"], "units": (("pcs", [1]),), "keywords": ["кабель", "usb", "type c", "adapter"], "price": (190, 890), "package_sizes": [1, 2, 3]},
    {"base_name": "Power Bank", "category": "Электроника", "brands": ["VoltEdge", "PowerStack", "HyperCell", "Minicore"], "descriptors": ["20000mAh", "10000mAh", "65W", "slim", "wireless"], "units": (("pcs", [1]),), "keywords": ["power bank", "20000", "быстрая зарядка"], "price": (1490, 6990), "package_sizes": [1]},
    {"base_name": "Лампа LED", "category": "Хозяйственные товары", "brands": ["BrightHome", "EcoLight", "Luma", "Volt"], "descriptors": ["E27", "E14", "теплый", "холодный", "smart"], "units": (("pcs", [1, 2, 4]),), "keywords": ["лампа", "led", "e27", "bulb"], "price": (89, 690), "package_sizes": [1, 3, 6]},
    {"base_name": "Батарейки AA", "category": "Хозяйственные товары", "brands": ["VoltEdge", "PowerMax", "EnergyGo", "UltraCell"], "descriptors": ["alkaline", "rechargeable", "eco", "pro"], "units": (("pcs", [2, 4, 8, 12]),), "keywords": ["батарейки", "aa", "lr6"], "price": (59, 720), "package_sizes": [1, 3, 6]},
    {"base_name": "Кофе капсулы", "category": "Кофе и чай", "brands": ["Ristretto Lab", "Caffitaly", "BaristaPro", "Arabica 24"], "descriptors": ["ristretto", "lungo", "decaf", "latte"], "units": (("caps", [10, 20, 30]),), "keywords": ["кофе", "капсулы", "capsules"], "price": (390, 1890), "package_sizes": [1, 2, 4]},
    {"base_name": "Лапша быстрого приготовления", "category": "Бакалея", "brands": ["StreetWok", "AsiaBox", "NoodleLab", "UrbanFood"], "descriptors": ["том ям", "курица", "говядина", "острая", "vegan"], "units": (("g", [75, 90, 100]),), "keywords": ["лапша", "инстант", "ramen"], "price": (35, 120), "package_sizes": [1, 12, 24]},
    {"base_name": "Салат готовый", "category": "Готовая еда", "brands": ["FreshBar", "CityLunch", "GreenMix", "Samokat Kitchen"], "descriptors": ["цезарь", "оливье", "витаминный", "vegan", "grain bowl"], "units": (("g", [180, 220, 300]),), "keywords": ["салат", "готовый", "salad"], "price": (150, 520), "package_sizes": [1]},
    {"base_name": "Мороженое пломбир", "category": "Мороженое", "brands": ["Polar Ice", "CreamLab", "SweetDay", "Gelato+"], "descriptors": ["ваниль", "клубника", "фисташка", "без сахара"], "units": (("g", [80, 90, 450, 900]),), "keywords": ["мороженое", "ice cream", "пломбир"], "price": (45, 480), "package_sizes": [1, 4, 12]},
    {"base_name": "Рыба минтай блок", "category": "Заморозка", "brands": ["Polar Sea", "HoReCaFish", "ChefPro", "OceanBlock"], "descriptors": ["филе", "блок 10кг", "HoReCa", "без глазури"], "units": (("kg", [5, 10]),), "keywords": ["рыба", "минтай", "block"], "price": (790, 4200), "package_sizes": [1]},
    {"base_name": "Сахар-песок", "category": "Бакалея", "brands": ["SweetLand", "Crystal", "SugarBox", "HoReCa"], "descriptors": ["1кг", "5кг", "меш 25кг", "рафинированный"], "units": (("g", [900, 1000]), ("kg", [5, 10, 25])), "keywords": ["сахар", "песок", "sugar"], "price": (59, 1500), "package_sizes": [1, 5]},
    {"base_name": "Перчатки одноразовые", "category": "Хозяйственные товары", "brands": ["SafeTouch", "CleanLab", "Medico", "ChefPro"], "descriptors": ["нитрил", "латекс", "винил", "s", "m", "l"], "units": (("pcs", [50, 100, 200]),), "keywords": ["перчатки", "одноразовые", "gloves"], "price": (190, 1200), "package_sizes": [1, 2, 4]},
    {"base_name": "Салфетки влажные", "category": "Косметика и гигиена", "brands": ["Clean&Care", "SoftTouch", "PureLine", "BabySoft"], "descriptors": ["детские", "антибактериальные", "аромат лаванды", "премиум"], "units": (("pcs", [40, 60, 120]),), "keywords": ["салфетки", "влажные", "wipes"], "price": (49, 290), "package_sizes": [1, 3, 6]},
    {"base_name": "Фольга алюминиевая", "category": "Хозяйственные товары", "brands": ["ChefPro", "DailyFix", "EcoWrap", "KitchenLine"], "descriptors": ["20м", "30м", "прочная", "professional"], "units": (("pcs", [1]),), "keywords": ["фольга", "aluminium", "foil"], "price": (79, 360), "package_sizes": [1, 3]},
    {"base_name": "Фиточай", "category": "Кофе и чай", "brands": ["HerbalMix", "Greenfield", "Orient Leaf", "Altai"], "descriptors": ["ромашка", "мята", "успокаивающий", "детокс"], "units": (("g", [50, 80, 120]), ("sachets", [20, 40])), "keywords": ["фиточай", "herbal", "tea"], "price": (89, 420), "package_sizes": [1, 2, 4]},
    {"base_name": "Протеиновый батончик", "category": "Здоровое питание", "brands": ["ProteinLab", "FitFuel", "SmartBar", "SuppNow"], "descriptors": ["20g protein", "шоколад", "арахис", "vegan", "без сахара"], "units": (("g", [40, 60, 90]),), "keywords": ["батончик", "protein", "протеиновый"], "price": (69, 260), "package_sizes": [1, 12, 24]},
]


def build_catalog(total: int, output_path: Path, seed: int) -> None:
    random.seed(seed)
    root = ET.Element("catalog")

    for idx in range(1, total + 1):
        base = random.choice(BASE_PRODUCTS)
        brand = random.choice(base["brands"])
        descriptor = random.choice(base["descriptors"]).strip()
        unit, weights = random.choice(base["units"])
        weight = random.choice(weights)
        package_size = random.choice(base.get("package_sizes", [1]))
        price = round(random.uniform(*base["price"]), 2)

        keywords_source = base["keywords"] + [brand.lower(), descriptor.replace(" ", "").lower()]
        keywords_unique: list[str] = []
        for kw in keywords_source:
            kw_lower = kw.lower()
            if kw_lower not in keywords_unique:
                keywords_unique.append(kw_lower)
        keywords = " ".join(keywords_unique)

        name_parts = [base["base_name"]]
        if descriptor:
            name_parts.append(descriptor)
        name_parts.append(f"«{brand}»")
        name_parts.append(f"{weight}{UNITS_DISPLAY.get(unit, unit)}")
        name = " ".join(name_parts).replace("  ", " ")
        description = (
            f"{descriptor.capitalize()} {base['base_name'].lower()} бренда {brand} в категории {base['category'].lower()}."
        ).replace("  ", " ")

        product = ET.SubElement(root, "product", id=f"P{idx:04d}")
        ET.SubElement(product, "name").text = name
        ET.SubElement(product, "category").text = base["category"]
        ET.SubElement(product, "brand").text = brand
        weight_node = ET.SubElement(product, "weight", unit=unit)
        weight_node.text = str(weight)
        ET.SubElement(product, "package_size").text = str(package_size)
        ET.SubElement(product, "keywords").text = keywords
        ET.SubElement(product, "description").text = description
        price_node = ET.SubElement(product, "price", currency="RUB")
        price_node.text = f"{price:.2f}"
        ET.SubElement(product, "image_url").text = f"https://example.com/p/P{idx:04d}.jpg"

    rough = ET.tostring(root, encoding="utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ")
    output_path.write_text(pretty, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic catalog data")
    parser.add_argument("--output", default="data/catalog_products.xml", help="Where to write the XML file")
    parser.add_argument("--total", type=int, default=1000, help="How many products to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_catalog(args.total, output_path, args.seed)
    print(f"Catalog with {args.total} products written to {output_path}")


if __name__ == "__main__":
    main()
