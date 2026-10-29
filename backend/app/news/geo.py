"""
Simple keyword-based geo detection for news events.
Maps country mentions to lat/lng coordinates.
"""
from typing import Tuple, Optional

COUNTRY_GEO = {
    "israel": ("Israel", 31.5, 34.75),
    "palestine": ("Palestine", 31.9, 35.2),
    "gaza": ("Gaza", 31.35, 34.3),
    "west bank": ("West Bank", 31.9, 35.2),
    "lebanon": ("Lebanon", 33.85, 35.86),
    "hezbollah": ("Lebanon", 33.85, 35.86),
    "hamas": ("Gaza", 31.35, 34.3),
    "ukraine": ("Ukraine", 48.37, 31.16),
    "russia": ("Russia", 61.52, 105.31),
    "putin": ("Russia", 61.52, 105.31),
    "zelensky": ("Ukraine", 48.37, 31.16),
    "china": ("China", 35.86, 104.19),
    "xi jinping": ("China", 35.86, 104.19),
    "taiwan": ("Taiwan", 23.69, 120.96),
    "beijing": ("China", 39.90, 116.40),
    "usa": ("USA", 37.09, -95.71),
    "united states": ("USA", 37.09, -95.71),
    "washington": ("USA", 38.89, -77.03),
    "trump": ("USA", 37.09, -95.71),
    "biden": ("USA", 37.09, -95.71),
    "america": ("USA", 37.09, -95.71),
    "uk": ("UK", 55.37, -3.43),
    "britain": ("UK", 55.37, -3.43),
    "london": ("UK", 51.50, -0.12),
    "india": ("India", 20.59, 78.96),
    "modi": ("India", 20.59, 78.96),
    "pakistan": ("Pakistan", 30.37, 69.34),
    "iran": ("Iran", 32.42, 53.68),
    "tehran": ("Iran", 35.68, 51.38),
    "north korea": ("North Korea", 40.33, 127.51),
    "kim jong": ("North Korea", 40.33, 127.51),
    "south korea": ("South Korea", 35.90, 127.76),
    "japan": ("Japan", 36.20, 138.25),
    "tokyo": ("Japan", 35.68, 139.69),
    "france": ("France", 46.22, 2.21),
    "paris": ("France", 48.85, 2.35),
    "macron": ("France", 46.22, 2.21),
    "germany": ("Germany", 51.16, 10.45),
    "brazil": ("Brazil", -14.23, -51.92),
    "lula": ("Brazil", -14.23, -51.92),
    "mexico": ("Mexico", 23.63, -102.55),
    "canada": ("Canada", 56.13, -106.34),
    "australia": ("Australia", -25.27, 133.77),
    "africa": ("Africa", 8.78, 34.50),
    "nigeria": ("Nigeria", 9.08, 8.67),
    "ethiopia": ("Ethiopia", 9.14, 40.48),
    "egypt": ("Egypt", 26.82, 30.80),
    "saudi": ("Saudi Arabia", 23.88, 45.07),
    "turkey": ("Turkey", 38.96, 35.24),
    "erdogan": ("Turkey", 38.96, 35.24),
    "syria": ("Syria", 34.80, 38.99),
    "iraq": ("Iraq", 33.22, 43.67),
    "afghanistan": ("Afghanistan", 33.93, 67.70),
    "myanmar": ("Myanmar", 21.91, 95.95),
    "venezuela": ("Venezuela", 6.42, -66.58),
    "cuba": ("Cuba", 21.52, -77.78),
    "sudan": ("Sudan", 12.86, 30.21),
    "yemen": ("Yemen", 15.55, 48.51),
    "houthi": ("Yemen", 15.55, 48.51),
    "europe": ("Europe", 54.52, 15.25),
    "nato": ("Europe", 54.52, 15.25),
    "asia": ("Asia", 34.04, 100.61),
    "middle east": ("Middle East", 29.31, 42.45),
}


def detect_geo(text: str) -> Tuple[Optional[str], float, float]:
    """Returns (country, lat, lng) from text. Defaults to (None, 0, 0)."""
    text_lower = text.lower()
    for keyword, (country, lat, lng) in COUNTRY_GEO.items():
        if keyword in text_lower:
            return country, lat, lng
    return None, 0.0, 0.0
