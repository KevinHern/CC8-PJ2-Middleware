import telepot
token = '123456'
TelegramBot = telepot.Bot(token)
print(TelegramBot.getMe())