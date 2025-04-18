async def get_stock_data(update: Update, context: CallbackContext) -> int:
    stock_code = update.message.text
    logger.info(f"The user has entered the stock code: {stock_code}")
    

    try:
        if stock_code.startswith("6"):
            stock_code += ".SH"
        elif stock_code.startswith("0") or stock_code.startswith("3"):
            stock_code += ".SZ"
        elif stock_code.startswith("9") or stock_code.startswith("8") or stock_code.startswith("4"):
            stock_code += ".BJ"
        else:
            await update.message.reply_text("Please enter a valid stock code.")
            return ENTER_STOCK_CODE
        
        context.user_data['stock_code'] = stock_code

        # 获取股票数据
        stock_info = pro.stock_basic(ts_code= stock_code, fields='ts_code,name,industry,list_date,market')
        if stock_info.empty:
            await update.message.reply_text("Cannot find the stock information, please enter a valid stock code.")
            keyboard = [["/Enter_stock_code"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("Click Enter_stock_code to start", reply_markup=reply_markup)
            return ENTER_STOCK_CODE

        # 发送最新股票数据
        def find_nearest_trade_date():
            today = datetime.datetime.now()
            if today.weekday() == 5: # 如果是周六，就取前一天
                today = today - datetime.timedelta(days=1)
            elif today.weekday() == 6: # 如果是周日，就取前两天
                today = today - datetime.timedelta(days=2)
            # 如果现在是下午北京时间3点之前，就取前一天
            if today.hour < 15:
                if today.weekday() == 0:
                    today = today - datetime.timedelta(days=3)
                else:
                    today = today - datetime.timedelta(days=1)
            return today.strftime('%Y%m%d')
        today_data = pro.daily(ts_code=stock_code, trade_date=find_nearest_trade_date())
        if today_data.empty:
            today_data = pro.daily(ts_code=stock_code).iloc[0]  # 获取最新数据
        else:
            today_data = today_data.iloc[0]

        reply_text = (
            f"Stock Code: {stock_info['ts_code'].values[0]}\n"
            f"Stock Name: {stock_info['name'].values[0]}\n"
            f"Industry: {stock_info['industry'].values[0]}\n"
            f"List Date: {stock_info['list_date'].values[0]}\n"
            f"Market: {stock_info['market'].values[0]}\n\n"
            f"The latest data:\n"
            f"Date: {today_data['trade_date']}\n"
            f"Open: {today_data['open']}\n"
            f"Close: {today_data['close']}\n"
            f"High: {today_data['high']}\n"
            f"Low: {today_data['low']}\n"
            f"Volume: {today_data['vol']}\n"
            f"Amount: {today_data['amount']}\n"
        )
        await update.message.reply_text(reply_text)
        # 发送下一步指令
        keyboard = [["📈Trend", "📰Gain_news_about_stock"], ["💰Finance", "🧙🏻‍♀️Predict"], ["✋🏻Another_stock","/End"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True,resize_keyboard = True)
        await update.message.reply_text("Select:", reply_markup=reply_markup)
        return FURTHER_MORE
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Failed to get stock data, please check the stock code.")
        return ConversationHandler.END