# %%
import logging
import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

import tushare as ts
ts.set_token('beabd2654861cfa0cc03518229c8f61e6b4069023ae1c1c5bd7c373f')
pro = ts.pro_api()

# logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# define states
ENTER_STOCK_CODE, GET_STOCK_DATA, FURTHER_MORE = range(3)

# connect to openai
from openai import OpenAI
client = OpenAI(api_key="sk-7e7baff036b24d77b131592b7501e2f7", base_url="https://api.deepseek.com")

def get_ss_and_sz():
    ss_df = pro.index_daily(ts_code='000001.SH')
    sz_df = pro.index_daily(ts_code='399001.SZ')
    ss_close = ss_df['close'].values[0]
    ss_open = ss_df['open'].values[0]
    sz_close = sz_df['close'].values[0]
    sz_open = sz_df['open'].values[0]
    ss_change = (ss_close - ss_open) / ss_open 
    sz_change = (sz_close - sz_open) / sz_open
    return {"SH":ss_close, "SZ":sz_close, "SH_change":ss_change, "SZ_change":sz_change}

async def handle_uninitialized(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    if "started" not in context.chat_data:
        context.chat_data["started"] = True
        await update.message.reply_text(f"Hello, Please click /start to begin.")
    # 发送 Start 按钮
        keyboard = [["/start"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    #await update.message.reply_text("Click /start to begin", reply_markup=reply_markup)

# 定义 /start 命令的处理函数
async def start(update: Update, context: CallbackContext) -> None:
    context.chat_data["started"] = True
    basic = get_ss_and_sz()
    await update.message.reply_text(f"Welcome to the our test Chatbot! \n\nThe current Shanghai Composite Index is {basic['SH']}, and the change is {basic['SH_change']:.2%}.\n\nThe current Shenzhen Composite Index is {basic['SZ']}, and the change is {basic['SZ_change']:.2%}.")
    # 设置超时任务
    # asyncio.create_task(end_conversation_after_timeout(update, context))
    keyboard = [["/Enter_stock_code"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Click /Enter_stock_code to start", reply_markup=reply_markup)
    return ENTER_STOCK_CODE



# 处理 #Enter_stock_code 指令
async def enter_stock_code(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Please enter the stock code you want to check. For instance, 000001 for Ping An, 600000 for ICBC.")
    return GET_STOCK_DATA



# 获取股票数据
import pandas as pd
with open('get_stock_data.py','r') as f: #r代表读取
    exec(f.read())

# 获取趋势
import matplotlib.pyplot as plt
import numpy as np
with open('trend.py','r') as f: #r代表读取
    exec(f.read())


with open('gain_info_about_stock.py','r') as f: #r代表读取
    exec(f.read())


with open('news_analysis.py','r') as f: #r代表读取
    exec(f.read())

with open('predict_stock_price.py','r') as f: #r代表读取
    exec(f.read())


# 定义错误处理函数
async def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'更新 {update} 导致错误 {context.error}')
async def end(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("The conversation has ended. If you have any more questions, please feel free to ask!")
    # 清除 chat_data
    context.chat_data.clear()
    return ConversationHandler.END




# 主函数
def main() -> None:
    token = "7864710114:AAFgK5Zx3jZtIS_f6iT23ckesYpIvzBK4GU"

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start),
                      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uninitialized)],
        states={
            ENTER_STOCK_CODE: [MessageHandler(filters.Regex("/Enter_stock_code"), enter_stock_code)],
            GET_STOCK_DATA: [MessageHandler(filters.TEXT& ~filters.COMMAND, get_stock_data)],
            FURTHER_MORE: [
                MessageHandler(filters.Regex("📈Trend"), get_trend),
                MessageHandler(filters.Regex("📰Gain_news_about_stock"), gain_news_about_stock),
                MessageHandler(filters.Regex("👽News_Analysis"), news_analysis),
                MessageHandler(filters.Regex("💰Finance"), get_finance),
                MessageHandler(filters.Regex("🧙🏻‍♀️Predict"), predict_stock_price),
                MessageHandler(filters.Regex("✋🏻Another_stock"), another_stock)
                ],
        },
        fallbacks=[  
            #MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uninitialized) # 未知消息处理函数
            CommandHandler("end", end)
            ] # 未知命令处理函数
    )



    # 注册命令和消息处理函数
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uninitialized))
    application.add_handler(conv_handler)
    application.add_error_handler(error)
    application.run_polling()

if __name__ == '__main__':
    main()




# %%
