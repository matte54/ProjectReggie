# allow woodhouse to give convertions of freedom units and metric

import re


class Converter:
    def __init__(self):
        pass

    async def check(self, message):
        txt = message.content

        # temperature
        m = re.search(r'(?:\s|^)(\-?\d+)( ?celcius| ?fahrenheit|c|f)\b', txt, flags=re.IGNORECASE)
        if m:
            number, unit = self.temp(int(m[1]), m[2])
            await self.reply_message(message, f'{number}{unit}', f'{m[1]}{m[2]}')

        # weight
        m = re.search(r'(?:\s|^)(\-?\d+)( ?pounds| ?kilograms|lbs|kg)\b', txt, flags=re.IGNORECASE)
        if m:
            number, unit = self.weight(int(m[1]), m[2])
            await self.reply_message(message, f'{number}{unit}', f'{m[1]}{m[2]}')

        # length
        m = re.search(r'(?:\s|^)(\-?\d+)( ?feet| ?meters|ft|m)\b', txt, flags=re.IGNORECASE)
        if m:
            number, unit = self.length(int(m[1]), m[2])
            await self.reply_message(message, f'{number}{unit}', f'{m[1]}{m[2]}')

        # distance
        m = re.search(r'(?:\s|^)(\-?\d+)( ?miles| ?kilometers|mi|km)\b', txt, flags=re.IGNORECASE)
        if m:
            number, unit = self.distance(int(m[1]), m[2])
            await self.reply_message(message, f'{number}{unit}', f'{m[1]}{m[2]}')

        # volume
        m = re.search(r'(?:\s|^)(\-?\d+)( ?gallons| ?liters|gal|l)\b', txt, flags=re.IGNORECASE)
        if m:
            number, unit = self.volume(int(m[1]), m[2])
            await self.reply_message(message, f'{number}{unit}', f'{m[1]}{m[2]}')

    def temp(self, number, unit):
        if unit.lower().startswith('c'):
            number = round(9.0 / 5.0 * number + 32)
            return number, "f"
        if unit.lower().startswith('f'):
            number = round((number - 32) * 5.0 / 9.0)
            return number, "c"

    def weight(self, number, unit):
        if unit.lower().startswith('p') or unit.lower().startswith('l'):
            # need to account for lbs and pounds starts with different letters
            number = round((number / 2.2042))
            return number, "kg"
        if unit.lower().startswith('k'):
            number = round((number * 2.2042))
            return number, "lbs"

    def length(self, number, unit):
        if unit.lower().startswith('f'):
            number = round((number / 3.28), 2)
            return number, "m"
        if unit.lower().startswith('m'):
            number = round((number * 3.28), 2)
            return number, "ft"

    def distance(self, number, unit):
        if unit.lower().startswith('k'):
            number = round((number * 0.62137), 2)
            return number, "mi"
        if unit.lower().startswith('m'):
            number = round((number / 0.62137), 2)
            return number, "km"

    def volume(self, number, unit):
        if unit.lower().startswith('g'):
            number = round((number * 3.7854), 2)
            return number, "l"
        if unit.lower().startswith('l'):
            number = round((number / 3.7854), 2)
            return number, "gal"

    async def reply_message(self, message, converted_str, original_str):
        await message.reply(f'{original_str} is also {converted_str}')
