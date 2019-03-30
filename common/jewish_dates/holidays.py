import datetime
from pyluach.dates import GregorianDate


def get_hag_and_shabbat(date):
    hebYear, hebMonth, hebDay = GregorianDate(date.year, date.month, date.day).to_heb().tuple()
    shabbat = 'Shabbat' if date.weekday() == 5 else ''          # 5 == Shabbat

    # Holidays in Nisan
    if hebDay == 15 and hebMonth == 1:
        return "Pesach"
    if hebDay == 21 and hebMonth == 1:
        return "Pesach"

    # Holidays in Sivan
    if hebDay == 6 and hebMonth == 3:
        return "Shavuot"

    # Holidays in Tishri
    if hebMonth == 7:
        if hebDay == 1 or hebDay == 2:
            return "RoshHashana"
        elif hebDay == 10:
            return "Yom Kippur"
        elif hebDay == 15:
            return "Sukkot"
        elif 15 < hebDay < 22 and shabbat:     # Treat Shabbat on Sukkot like Sukkot (so the blinds don't go down)
            return "Sukkot"
        elif hebDay == 22:
            return "SimchatTorah"

    return shabbat



# from common.date_utils_py2.times import today_sunrise_sunset
# location = 'Azriel_wiki'
# sunrise1, sunset1 = today_sunrise_sunset(location)
# print(sunrise1, sunset1)
