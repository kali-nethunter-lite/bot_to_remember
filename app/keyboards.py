from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton)

menu = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text='По телефону', callback_data='search_number'),
                InlineKeyboardButton(text='По ПІБ', callback_data='search_fio')]])

admin_menu = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text='По телефону', callback_data='search_number'),
                InlineKeyboardButton(text='По ПІБ', callback_data='search_fio')],
                [InlineKeyboardButton(text='Панель адміністратора', callback_data='admin_panel')]])

admin_panel = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Додати інформацію', callback_data='add_user')],
                [InlineKeyboardButton(text='Блокування', callback_data='ban_user'),
                InlineKeyboardButton(text='Розблокування', callback_data='unban_user')],
                [InlineKeyboardButton(text='Назад', callback_data='back_to_main')]])

back_to_admin_menu = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Назад', callback_data='admin_panel')]])

back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]])
