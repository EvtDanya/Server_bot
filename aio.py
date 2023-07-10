from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher.filters import IDFilter
import logging
import subprocess
import asyncio
import os

#bot configuration
bot = Bot('///')
dp = Dispatcher(bot)
user_id = 123
chat_id = 123

#services info
services = {'bot-tg.service':'Tg-bot Omega', 'bot-pentester.service':'PocketPentester', 'apache2':'Apache', 'server.service':'Server-app', 'proxy.service':'Proxy-server', 'nodejs.service':'Node.js'}
servicesEnabledChecker = {'Tg-bot Omega':True, 'PocketPentester':True, 'Apache':True, 'Server-app':True, 'Proxy-server':True, 'Node.js':True}

#Inline keyboard for services
inline_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=4)
for service in services:
    inline_keyboard.add(types.InlineKeyboardButton(text=services[service], callback_data=service))

#Inline keyboard for pushes
inline_keyboard_push = types.InlineKeyboardMarkup()
key_start = types.InlineKeyboardButton(text='Start', callback_data='start')
key_stop = types.InlineKeyboardButton(text='Stop', callback_data='stop')
key_edit = types.InlineKeyboardButton(text='Edit config', callback_data='edit')
inline_keyboard_push.add(key_start, key_stop, key_edit)

#for pushes
is_push = False

#main keyboard
markup_main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
markup_main_menu.add(types.KeyboardButton("/push"))
markup_main_menu.add(types.KeyboardButton("/start"))
markup_main_menu.add(types.KeyboardButton("/stop"))
markup_main_menu.add(types.KeyboardButton("/status"))

#logging into file
logging.basicConfig(level=logging.INFO, filename="/root/logs/server-bot.log", filemode="a")

async def is_server_up(service_name):
    process = subprocess.run(['systemctl', 'status', service_name], capture_output=True)
    output = process.stdout.decode()
    return 'Active: active (running)' in output

async def check_services():
    while (is_push):        
        for service in services:
            if not await is_server_up(service) and servicesEnabledChecker[services[service]]:
                message = '💔💔💔  ' + services[service] + ' is not running!'
                await bot.send_message(chat_id=chat_id, text=message)
        await asyncio.sleep(300)

@dp.message_handler(IDFilter(user_id), commands='push')
async def push(message: types.Message):
    if is_push: 
        sticker = '🟢'
    else:
        sticker = '🔴'
    await bot.send_message(message.chat.id, f'{sticker} Push notifications state: {is_push}\nWhat to do?', reply_markup=inline_keyboard_push, parse_mode='HTML')    
        
@dp.message_handler(IDFilter(user_id), commands='start')
async def start(message: types.Message):
    global serviceCheckState 
    serviceCheckState = 'start'
    await bot.send_message(message.chat.id, 'Choose service', reply_markup=inline_keyboard)     

@dp.message_handler(IDFilter(user_id), commands='stop')
async def stop(message: types.Message):
    global serviceCheckState
    serviceCheckState = 'stop'
    await bot.send_message(message.chat.id, 'Choose service', reply_markup=inline_keyboard)

@dp.message_handler(IDFilter(user_id), commands='status')
async def status(message: types.Message):
    global serviceCheckState
    serviceCheckState = 'status'
    await bot.send_message(message.chat.id, 'Choose service', reply_markup=inline_keyboard)

@dp.callback_query_handler(IDFilter(user_id), lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    global is_push
    global servicesEnabledChecker
    if (callback_query.data == 'start' and not is_push):
        is_push = True
        loop = asyncio.get_event_loop()
        task = loop.create_task(check_services())
            
    elif (callback_query.data == 'stop'):
        is_push = False
            
    elif (callback_query.data == 'edit'):
        message = ''
        for service in services:
            if servicesEnabledChecker[services[service]]:
                message += '✅ '
            else:
                message += '❌ '
            message += services[service] + '\n'
        await bot.send_message(callback_query.from_user.id, message, reply_markup=inline_keyboard)
        global serviceCheckState
        serviceCheckState = 'cancel'
    elif serviceCheckState == 'cancel': 
        servicesEnabledChecker[services[callback_query.data]] = not servicesEnabledChecker[services[callback_query.data]]
            
    else:
        global selectedService
        selectedService = callback_query.data
        try:
            result = subprocess.run(['systemctl', serviceCheckState, selectedService], capture_output=True)
            await bot.send_message(callback_query.from_user.id, result.stdout.decode())
        except subprocess.CalledProcessError:
            await bot.send_message(callback_query.from_user.id, 'Invalid input')

@dp.message_handler(IDFilter(user_id), commands=['send'])
async def send_file(message: types.Message):
    
    command_args = message.get_args()
    if not command_args:
        await message.reply("Please specify the filename after the /send command.")
        return

    path, filename = os.path.split(command_args.strip())

    file_path = os.path.join(path, filename)
    if not os.path.isfile(file_path):
        await message.reply(f"The file '{filename}' does not exist.")
        return

    with open(file_path, 'rb') as file:
        await bot.send_document(message.chat.id, file)

@dp.message_handler(IDFilter(user_id), content_types=['text'])
async def main(message: types.Message):
    command = message.text
    try:
        if command.startswith('cd'):
            path2move = command.strip('cd ')
            
            if os.path.exists(path2move):
                os.chdir(path2move)
                await bot.send_message(message.chat.id, 'Directory changed to'+path2move)
            else:
                await bot.send_message(message.chat.id, 'Cant change directory to'+path2move)
        else:        
            result = subprocess.run(command.split(' '), capture_output=True)
            if result.stdout:
                await bot.send_message(message.chat.id, result.stdout.decode())
            else:
                await bot.send_message(message.chat.id, 'Command executed successfully.')
    except Exception as e:
        await bot.send_message(message.chat.id, str(e))

    await bot.send_message(message.chat.id, 'Choose command', reply_markup=markup_main_menu)


@dp.message_handler(IDFilter(user_id), content_types=['document'])
async def handle_document(message: types.Message):
    file_id = message.document.file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    downloaded_file = await bot.download_file(file_path)

    filename = message.document.file_name

    if os.path.exists(filename):
        confirm_msg = f"File '{filename}' already exists. Do you want to replace it?"
        confirm_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        confirm_buttons = [types.KeyboardButton('Yes'), types.KeyboardButton('No')]
        confirm_keyboard.add(*confirm_buttons)
        await bot.send_message(message.chat.id, confirm_msg, reply_markup=confirm_keyboard)

        
        response = await bot.wait_for('message', chat_id=message.chat.id)
        if response.text.lower() != 'yes':
            await bot.send_message(message.chat.id, 'File was not replaced.')
            return

    with open(filename, 'wb') as file:
        file.write(downloaded_file.read())

    await bot.send_message(message.chat.id, f'File {filename} has been saved.')



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
