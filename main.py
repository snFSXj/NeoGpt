#Copyright 2023 t.me/snfsx
#Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#http://www.apache.org/licenses/LICENSE-2.0
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

import aiogram, sys, logging, asyncio, aiohttp, json, datetime, sqlite3, random
from aiogram import Bot, Dispatcher, types, filters
from aiogram.filters.command import Command, CommandObject

admins_id = [айди админов]

conn = sqlite3.connect('alluser.db')

cursor = conn.cursor()

with open('data.json') as f:
    details = json.load(f)

bot_token= details['bottoken']

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token, parse_mode="HTML")

dp = Dispatcher()

start_time = datetime.datetime.now()

def user_exists(user_id):
    conn = sqlite3.connect('alluser.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    return result is not None

@dp.message(Command('register'))
async def registration(message: types.Message):
         cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY
                );''')
         id = message.from_user.id
         id = int(id)
         cursor.execute("SELECT * FROM users WHERE id =?",(id,))
         check = cursor.fetchone()
         if not check == None:
            await message.answer(f'Вы уже зарегистрированы в боте!')
         else:
            cursor.execute(f"INSERT INTO users (id) VALUES ({id});")
            conn.commit()
            await message.answer(f'Вы успешно зарегистрировались в боте! Ваш id = {id}')
            
@dp.message(Command('start'))
async def start(message: types.Message):
  await message.answer('Привет! Добро пожаловать в NeoGPT! \nЯ бот, который создан для использования ChatGPT в Telegram!\nПройдите регистрацию посредством команды /register для использования бота')

@dp.message(Command('uptime'))
async def cmd_uptime(message: types.Message, command: CommandObject):
  if message.from_user.id in admins_id:
     number = int(command.args)
     uptime = datetime.datetime.now() - start_time
     await message.reply(f"Время работы бота: {uptime}")
  else:
     await message.reply(f"У вас нету доступа к этой команде ")

@dp.message(Command('help'))
async def help(message: types.Message):
  await message.answer('Команды:\n/ask {запрос} - задать вопрос к ChatGPT.\n/help - получить список команд.')

@dp.message(Command('ask'))
async def ask(message: types.Message, command: CommandObject):
    id = message.from_user.id
    id = int(id)
    cursor.execute("SELECT * FROM users WHERE id =?",(id,))
    check = cursor.fetchone()
    if check == None:
        await message.answer("Вы не зарегистрированы, напишите /register для регистрации")
    else:
        if command.args is None:
           await message.reply("Ошибка! Не был задан промпт.")
        else:
            prompt = command.args

            msg = await message.reply("<i>Ожидайте ответа ИИ...</i>")

            async with aiohttp.ClientSession() as session:
                async with session.post(details['url'],      headers={"Authorization": f"{details['apichat']}",
       "Content-Type": "application/json"},json={"model": "gpt-3.5-turbo",
       "messages": [
           {"role": "user", "content": prompt}
       ],
       "max_tokens": 500}) as response:
                 if response.status == 200:
                    answer = await response.json()
                    result = answer['choices'][0]['message']['content']
                    await msg.edit_text(result, f"Ваш запрос: {prompt}")
                 else:
                     await msg.edit_text("Не удалось получить ответ от ИИ")

@dp.message(Command('picgen'))
async def picgen(message: types.Message, command: CommandObject):
    id = message.from_user.id
    id = int(id)
    cursor.execute("SELECT * FROM users WHERE id =?", (id,))
    check = cursor.fetchone()
    
    if check == None:
        await message.answer("Вы не зарегистрированы, напишите /register для регистрации")
    else:
        msg = await message.reply("<i>Ожидайте ответа ИИ...</i>")
        prompt = command.args
        url = details['prodiaurl']

        pars = {
            "new": "true",
            "prompt": prompt,
            "model": "anything-v4.5-pruned.ckpt [65745d25]",
            "steps": 10,
            "cfg": 8,
            "seed": random.randint(0, 1000000000),
            "sampler": "Euler a",
            "aspect_ratio": "square",
        }

        async with aiohttp.ClientSession() as s:
            async with s.get(f"{url}/generate", params=pars) as r:
                resp = await r.json()
                job_id = resp["job"]

                while True:
                    async with s.get(f"{url}/job/{job_id}") as r:
                        resp = await r.json()
                        if resp["status"] == "succeeded":
                            break
                        await asyncio.sleep(0.15)

        await msg.delete()
        await message.reply_photo(
            photo=f"https://images.prodia.xyz/{job_id}.png",
            caption=f"Ваше изображение готово!"
        )

@dp.message()
async def what(message):
  await message.answer('Я не понимаю вас, введите /help для вызова возможных команд.')

async def main():
  await dp.start_polling(bot)

if __name__ == '__main__':
  asyncio.run(main())
