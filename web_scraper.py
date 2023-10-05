import requests
from bs4 import BeautifulSoup

def scrape_table(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'live today'})
        return table
    except Exception as e:
        print("Error:", str(e))