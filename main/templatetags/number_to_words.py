# main/templatetags/number_to_words.py
from django import template

register = template.Library()

def number_to_words(num):
    try:
        num = float(num)
    except (ValueError, TypeError):
        return "ZERO"
    
    ones = ['', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE',
            'TEN', 'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN',
            'SEVENTEEN', 'EIGHTEEN', 'NINETEEN']
    tens = ['', '', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY', 'SIXTY', 'SEVENTY', 'EIGHTY', 'NINETY']
    
    def convert(n):
        if n < 20:
            return ones[int(n)]
        elif n < 100:
            return tens[int(n // 10)] + (' ' + ones[int(n % 10)] if n % 10 != 0 else '')
        elif n < 1000:
            return ones[int(n // 100)] + ' HUNDRED' + (' ' + convert(n % 100) if n % 100 != 0 else '')
        elif n < 1000000:
            return convert(n // 1000) + ' THOUSAND' + (' ' + convert(n % 1000) if n % 1000 != 0 else '')
        else:
            return convert(n // 1000000) + ' MILLION' + (' ' + convert(n % 1000000) if n % 1000000 != 0 else '')
    
    pesos = int(num)
    centavos = int(round((num - pesos) * 100))
    
    result = convert(pesos) + ' PESOS'
    if centavos > 0:
        result += ' AND ' + convert(centavos) + ' CENTAVOS'
    
    return result

@register.filter
def amount_in_words(value):
    return number_to_words(value)
