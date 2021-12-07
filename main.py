import datetime
import hashlib
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ContentTypes, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, InlineQuery, \
    InputTextMessageContent, InlineQueryResultArticle

import config
from core import db_map
from core.adverts import get_adverts
from core.categories import category, category_dict, subcategory
from core.db_map import engine, session_scope, UsersTable

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Params(StatesGroup):
    cat = State()
    subcat = State()
    min_price = State()
    max_price = State()
    city = State()


@dp.message_handler(commands='start', state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    with session_scope() as session:
        user = message.from_user
        slave = session.query(UsersTable).filter_by(id=user.id).first()
        session.query(UsersTable).filter_by(id=user.id).first()

        if slave is None:
            data = UsersTable(id=user.id,
                              sub=None)
            session.add(data)
            session.commit()
            await message.answer(
                f'🔒 <i>Привет, для доступа к парсеру нужно иметь подписку, можешь приобрести ее у {config.ADMIN_USERNAME}</i>',
                parse_mode=ParseMode.HTML)
            return
        if slave.sub is None:
            await message.answer(
                f'🔒 <i>Для доступа к парсеру нужно иметь подписку, можешь приобрести ее у {config.ADMIN_USERNAME}</i>',
                parse_mode=ParseMode.HTML)
            return
        sub_validate = False
        if slave.sub > datetime.datetime.now():
            sub_validate = True

        if sub_validate:

            await message.answer(
                f"🎈<i>Дней до окончания лицензии:</i> <b>{(slave.sub - datetime.datetime.now()).days}</b>\n"
                "\n"
                "<code>➡️ Чтобы начать парсинг, воспользуйся командой </code>/parse\n",
                parse_mode=ParseMode.HTML)
        else:
            await message.answer(
                f'🔒 <i>Для доступа к парсеру нужно иметь подписку, можешь приобрести ее у {config.ADMIN_USERNAME}</i>',
                parse_mode=ParseMode.HTML)

    await state.finish()


@dp.message_handler(commands='parse')
async def send_welcome(message: types.Message, state: FSMContext):
    sub_validate = False
    with session_scope() as session:

        slave = session.query(UsersTable).filter_by(id=message.from_user.id).first()

        if slave.sub > datetime.datetime.now():
            sub_validate = True

        if not sub_validate:
            await message.answer(
                f'🔒 <i>Для доступа к парсеру нужно иметь подписку, можешь приобрести ее у {config.ADMIN_USERNAME}</i>')
            return
    keyboard_list = []
    for i in category:
        keyboard_list.append(InlineKeyboardButton(category_dict[i], callback_data=f'cat:{i}'))
    keyboard = [keyboard_list[i:i + 2] for i in range(0, len(keyboard_list), 2)]

    await message.reply("📚 <code>Выбери категорию:</code>",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                        parse_mode=ParseMode.HTML
                        )

    await Params.cat.set()


@dp.callback_query_handler(state=Params.cat, text_contains='cat:')
async def send_welcome(query: types.CallbackQuery, state: FSMContext):
    cat = query.data.split(':')[1]
    async with state.proxy() as data:
        data['cat'] = cat
    keyboard_list = []
    subcat = subcategory[cat]
    for i in subcat:
        keyboard_list.append(InlineKeyboardButton(subcat[i], callback_data=f'subcat:{i}'))
    keyboard = [keyboard_list[i:i + 2] for i in range(0, len(keyboard_list), 2)]
    keyboard.append([InlineKeyboardButton('◀️ Назад', callback_data='back')])

    await query.message.reply("<code>📕 Выбери подкатегорию:</code>",
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                              parse_mode=ParseMode.HTML)

    await Params.subcat.set()


@dp.callback_query_handler(state='*', text_contains='back')
async def send_welcome(query: types.CallbackQuery, state: FSMContext):
    step = str(await state.get_state()).split(':')[1]
    if step == 'subcat':
        keyboard_list = []
        for i in category:
            keyboard_list.append(InlineKeyboardButton(category_dict[i], callback_data=f'cat:{i}'))
        keyboard = [keyboard_list[i:i + 2] for i in range(0, len(keyboard_list), 2)]

        await query.message.edit_text("Введи категорию",
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                                      parse_mode=ParseMode.HTML
                                      )

        await Params.subcat.set()
    if step == 'min_price':

        cat = await  state.get_data()
        keyboard_list = []
        subcat = subcategory[cat['cat']]
        for i in subcat:
            keyboard_list.append(InlineKeyboardButton(subcat[i], callback_data=f'subcat:{i}'))
        keyboard = [keyboard_list[i:i + 2] for i in range(0, len(keyboard_list), 2)]
        keyboard.append([InlineKeyboardButton('◀️ Назад', callback_data='back')])

        await query.message.edit_text("📚 <code>Выбери категорию:</code>",
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                                      parse_mode=ParseMode.HTML)

        await Params.min_price.set()
    if step == 'max_price':
        await query.message.edit_text("<code>🔽 Введи максимальную цену объявлений.</code>",
                                      reply_markup=InlineKeyboardMarkup(
                                          inline_keyboard=[[InlineKeyboardButton('◀️ Назад', callback_data='back')]]),
                                      parse_mode=ParseMode.HTML)
        await Params.max_price.set()
    if step == 'city':
        await query.message.edit_text("<code>🔽 Введи инимальную цену объявлений.</code>",
                                      reply_markup=InlineKeyboardMarkup(
                                          inline_keyboard=[[InlineKeyboardButton('◀️ Назад', callback_data='back')]]),
                                      parse_mode=ParseMode.HTML)
        await Params.city.set()
    await Params.previous()


@dp.callback_query_handler(state=Params.subcat, text_contains='subcat:')
async def send_welcome(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['subcat'] = query.data.split(':')[1]
    await query.message.reply("<code>🔽 Введи инимальную цену объявлений.</code>",
                              reply_markup=InlineKeyboardMarkup(
                                  inline_keyboard=[[InlineKeyboardButton('◀️ Назад', callback_data='back')]]),
                              parse_mode=ParseMode.HTML)
    await Params.min_price.set()


@dp.message_handler(state=Params.min_price)
async def send_welcome(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['min_price'] = message.text

    await message.reply("<code>🔽 Введи максимальную цену объявлений.</code>",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[[InlineKeyboardButton('◀️ Назад', callback_data='back')]]),
                        parse_mode=ParseMode.HTML)

    await Params.max_price.set()


@dp.message_handler(state=Params.max_price)
async def send_welcome(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['max_price'] = message.text
    await message.reply("<code>🏘 Введи город как на сайте, только англ. буквами</code>",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[[InlineKeyboardButton('◀️ Назад', callback_data='back')]]),
                        parse_mode=ParseMode.HTML)

    await Params.next()


@dp.message_handler(state=Params.city)
async def send_welcome(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['city'] = message.text
    await message.reply("🧿Парсинг начат!",
                        parse_mode=ParseMode.HTML)
    data = await state.get_data()
    await get_adverts(f'https://www.olx.pl/{data["cat"]}/{data["subcat"]}/', data["min_price"], data["max_price"],
                      data["city"],
                      (message.bot, message.from_user.id, message))
    await state.finish()


@dp.inline_handler()
async def inline_echo(inline_query: InlineQuery):
    if inline_query.from_user.id not in config.ADMINS:
        return
    if not inline_query.query.isdigit():
        text = '<b>❌ Неверно указано значение дня</b>'
        result_id: str = hashlib.md5(text.encode()).hexdigest()
        input_content = InputTextMessageContent(text, parse_mode=ParseMode.HTML)
        item = InlineQueryResultArticle(
            id=result_id,
            title='Укажи количество выдаваемых дней',
            input_message_content=input_content,

        )
    else:
        text = f'<i>Дней в подписке: {inline_query.query}</i>' \
               '\n<code>❇️Чтобы активировать подписку нажми на кнопку ниже:</code>'

        result_id: str = hashlib.md5(text.encode()).hexdigest()
        input_content = InputTextMessageContent(text, parse_mode=ParseMode.HTML)
        item = InlineQueryResultArticle(
            id=result_id,
            title=f'Выдать подписку на {inline_query.query} дней',
            input_message_content=input_content,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('🔑  Активировать',
                                                                                     callback_data=f'activate:{inline_query.query}')]])
        )

    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)


@dp.callback_query_handler(text_contains='activate:')
async def send_welcome(query: types.CallbackQuery):
    days = query.data.split(':')[1]
    await query.answer('Супер!')
    await query.bot.send_message(chat_id=query.from_user.id,
                                 text='<i>🔓 Подписка активирована!. Напиши мне </i>/start',
                                 parse_mode=ParseMode.HTML)
    await query.bot.edit_message_text(inline_message_id=query.inline_message_id,

                                      text='✅ <i>Подписка активирована. Загляни в бота</i>',
                                      parse_mode=ParseMode.HTML)

    with session_scope() as session:

        slave = session.query(UsersTable).filter_by(id=query.from_user.id).first()
        if slave.sub is None:
            session.query(UsersTable).filter_by(id=query.from_user.id) \
                .update({UsersTable.sub: datetime.datetime.now() + datetime.timedelta(days=int(days))})
        else:
            print(slave.sub + datetime.timedelta(days=int(days)))

            session.query(UsersTable).filter_by(id=query.from_user.id) \
                .update({UsersTable.sub: slave.sub + datetime.timedelta(days=int(days))})
        session.commit()


def main():
    # db_map.Base.metadata.drop_all(db_map.engine)
    db_map.Base.metadata.create_all(engine)

    print('[+]: BOT STARTED')

    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    main()
