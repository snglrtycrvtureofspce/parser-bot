import asyncio
import json
import time

from aiogram.types import ParseMode
from bs4 import BeautifulSoup as bs
from config import session, OLX_TOKEN


async def get_advert(url):
    t = time.time()
    async with session.get(url) as resp:
        r = await resp.text()
    soup = bs(r, 'html.parser')
    title = soup.find('title').text.split('•')[0].rsplit(' ', 2)[0]
    try:
        adv = json.loads(str(soup).split('}}},"pageView":')[1].split("}');")[0])
    except IndexError:
        print(url, soup)
        adv = json.loads(
            str(soup).split('window.__PRERENDERED_STATE__= ')[1].split('window.__LANG_CONFIG__=')[0].replace(
                ',"cookies":{}};', '}'))
        price = adv['ad']['ad']['price']['regularPrice']['value']
        adv_id = adv['ad']['ad']['id']
        user_id = adv['ad']['ad']['user']['id']
    else:
        price = adv['ad_price']
        adv_id = adv['ad_id']
        user_id = adv['seller_id']
    async with session.post(f'https://www.olx.pl/api/v1/offers/{adv_id}/page-views/',
                            headers={'Authorization': OLX_TOKEN}) as resp:
        response = await resp.text()

    view = json.loads(response)['data']
    async with session.get(f'https://www.olx.pl/api/v1/offers/{adv_id}/phones/',
                           headers={'Authorization': OLX_TOKEN}) as resp:
        response = await resp.text()
    try:
        phone = f"48{json.loads(response)['data']['phones'][0].replace(' ', '')}"
    except IndexError:
        phone = None
    async with session.get('https://m.olx.pl/api/v1/offers/',
                           params={'offset': 0, 'limit': 50, 'user_id': int(user_id)},
                           headers={'Authorization': OLX_TOKEN}) as resp:
        response = await resp.text()
    advl = len(json.loads(response)['data'])
    async with session.get(f'https://m.olx.pl/api/v1/users/{user_id}/',
                           headers={'Authorization': OLX_TOKEN}) as resp:
        response = await resp.text()
    reg = json.loads(response)['data']['created'].split('-')[0]
    info = {'url': url, 'title': title, 'price': price, 'phone': phone, 'view': view, 'reg': reg, 'adv': advl,
            'id': user_id, 'sleep': time.time() - t}
    return info


async def arange(count, c):
    for i in range(count, c):
        yield (i)


async def get_adverts(url, min_price, max_price, city, bot):
    'glogow/?search[filter_float_price:from]={min_price}&search[filter_float_price:to]={max_price}&page={i}'
    try:
        ad_array = []
        # print((
        #        url + f'{city}/?search[filter_float_price:from]={min_price}&search[filter_float_price:to]={max_price}&page={1}'))
        async with session.get(url) as resp:
            pages = await resp.text()
        soup = bs(pages, 'html.parser')
        pages = int(soup.find_all('a', class_='block br3 brc8 large tdnone lheight24')[-1]['href'].split('=')[-1])
        if pages >= 4:
            pages = 3

        for i in range(1, pages + 1):
            async with session.get(
                    url + f'{city}/?search[filter_float_price:from]={min_price}&search[filter_float_price:to]={max_price}&page={i}') as resp:
                result = await resp.text()

            html_tree = bs(result, "html.parser")
            ads = html_tree.select('#offers_table tr.wrap table')

            for ad in ads:

                ad_url = ad.select('td')[0].select('a')[0]['href']
                if 'olx.pl' not in ad_url:
                    continue
                ad_array.append(ad_url)
        await bot[0].send_message(chat_id=bot[1], text=f'\n ☁️  <i>Найдено бъявлений:</i> <b>{len(ad_array)}</b>',
                                  parse_mode=ParseMode.HTML)
        for i in ad_array:
            try:
                advert = await get_advert(i)
            except:
                continue
            if not advert:
                continue
            if advert['sleep'] < 3:
                await asyncio.sleep(3 - advert['sleep'])

            await bot[0].send_message(chat_id=bot[1], text=f'<i>🔆 Название:</i> <b>{advert["title"]}</b>'
                                                           f'\n<i>🔗 Ссылка:</i> <b>{advert["url"]}</b>'
                                                           f'\n<i>💰 Цена:</i> <b>{advert["price"]}</b>'
                                                           f'\n<i>📞 Номер:</i> <b>+{advert["phone"]}</b>'
                                                           f'\n<i>👁 Просмотры:</i> <b>{advert["view"]}</b>'
                                                           f'\n<i>🕘 Год регистрации продавца:</i> <b>{advert["reg"]}</b>'
                                                           f'\n<i>📋 Объявлений у продавца:</i>  <b>{advert["adv"]}</b>'
                                                           f'\n<i>☎ WhatsUp:</i> https://api.whatsapp.com/send?phone={advert["phone"].replace("-", "")}',
                                      disable_web_page_preview=True,
                                      parse_mode=ParseMode.HTML)

        await bot[0].send_message(chat_id=bot[1], text='<i>🔧Парсинг окончен.</i>'
                                                       "<code>➡️ \nЧтобы начать парсинг снова, воспользуйся командой </code>/parse",
                                  parse_mode=ParseMode.HTML)
    except:
        await bot[0].send_message(chat_id=bot[1], text='<i>Произошла непредвиденная ошибка.</i>',
                                  parse_mode=ParseMode.HTML)

