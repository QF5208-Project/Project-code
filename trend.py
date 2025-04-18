
async def get_trend(update:Update, context:CallbackContext) -> int:
    import io
    stock_code = context.user_data.get('stock_code')
    if not stock_code:
        await update.message.reply_text("Please enter the stock code first.")
        return ENTER_STOCK_CODE
    weekly_trend = pro.weekly(ts_code=stock_code,start_date='20240301',end_date=datetime.datetime.now().strftime('%Y%m%d'))
    weekly_trend = weekly_trend.sort_values('trade_date',ascending=True)
    monthly_trend = pro.monthly(ts_code=stock_code,start_date='20240301',end_date=datetime.datetime.now().strftime('%Y%m%d'))
    monthly_trend = monthly_trend.sort_values('trade_date',ascending=True)


    def plot_trend(data,title_here):
        # 使用 GGplot 风格
        plt.style.use('ggplot')
        plt.figure(figsize=(10,6),facecolor='white')
        plt.plot(data['trade_date'],data['close'],label='Close Price')

        # 标注出最高点和最低点的日期和价格
        plt.scatter(data['trade_date'][data['close'].idxmax()],data['close'].max(),label='Highest Point',color='r')
        plt.scatter(data['trade_date'][data['close'].idxmin()],data['close'].min(),label='Lowest Point',color='g')

        plt.xlabel('Date')
        plt.ylabel('Close Price')
        plt.title(title_here)
        plt.xticks(rotation=45)
        plt.tight_layout() # 自动调整子图参数，使之填充整个图像区域
        plt.legend()

        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        #plt.close()
        return buf
    
    buf1 = plot_trend(weekly_trend,'Weekly Trend of '+stock_code)
    #plt.show()
    buf2 = plot_trend(monthly_trend,'Monthly Trend of '+stock_code)
    #plt.show()
    await update.message.reply_photo(photo=buf1, caption="Weekly Trend")
    await update.message.reply_photo(photo=buf2, caption="Monthly Trend")

    # 发送下一步指令
    keyboard = [["📰Gain_news_about_stock", "💰Finance"], ["🧙🏻‍♀️Predict", "✋🏻Another_stock","/End"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Select:", reply_markup=reply_markup)
    return FURTHER_MORE