import akshare as ak
import json
async def gain_news_about_stock(update: Update, context: CallbackContext) -> int:
    stock_code = context.user_data.get('stock_code')[0:6]
    await update.message.reply_text(f"Please wait")

    try:
        def get_news_dataframe(stock_code):
            news_df = ak.stock_news_em(symbol=stock_code)
            object_cols = news_df.select_dtypes(include='object').columns
            news_df[object_cols] = news_df[object_cols].astype('string')
            news_df['发布时间'] = pd.to_datetime(news_df['发布时间'], errors='coerce') 
            return news_df
        
        news_df = get_news_dataframe(stock_code)
        news_df_copy = news_df

        def df_to_json_serializable(df, stock_symbol=None):
            #将DataFrame转换为DeepSeek所需的JSON格式
            news_list = []
            for _, row in df.iterrows():
                news_item = {
                    "title": str(row['新闻标题']),  
                    "content": str(row['新闻内容']),
                    "publish_time": row['发布时间'].strftime("%Y-%m-%d %H:%M:%S"),
                    "source": str(row['文章来源'])
                }
                news_list.append(news_item)
            
                input_data = {"news": news_list}
                if stock_symbol:
                    input_data["stock_symbol"] = str(stock_symbol)  
            return json.dumps(input_data, ensure_ascii=False) #返回JSON格式的字符串
        
        # 保存新闻数据到用户数据
        context.user_data['news_df'] = df_to_json_serializable(news_df, stock_code)

        # 分别发送前5条新闻
        for _, row in news_df.head().iterrows():
            await update.message.reply_text(f"Title: {row['新闻标题']}\n\nPublish Time: {row['发布时间']}\n\nSource: {row['文章来源']}\n\nLink: {row['新闻链接']}")



        # 下一步
        keyboard = [["👽News_Analysis"],["📈Trend","💰Finance"],["🧙🏻‍♀️Predict","✋🏻Another_Stock"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Please select the next step", reply_markup=reply_markup)
        return FURTHER_MORE
    except Exception as e:
        logger.error(f"获取新闻数据时出错: {e}")
        await update.message.reply_text("Failed to get news data, please try again later.")
        return ConversationHandler.END

async def get_finance(update: Update, context: CallbackContext) -> int:
    stock_code = context.user_data.get('stock_code')
    await update.message.reply_text(f"Please wait")
    try:
        f10_indicator = pro.fina_indicator(ts_code=stock_code)
        f10_indicator = f10_indicator.to_dict(orient='records')[0]
        mainbz = pro.fina_mainbz(ts_code=stock_code)
        mainbz = mainbz.to_dict(orient='records')[0]

        finance = {
            "Announcement Date": f10_indicator['ann_date'],
            "EPS": f10_indicator['eps'],
            "Net Profit": f10_indicator['roe'],
            "Current Ratio": f10_indicator['current_ratio'],
            "Quick Ratio": f10_indicator['quick_ratio'],
            "Revenue per Share": f10_indicator['revenue_ps'],
            "BPS": f10_indicator['bps'],
            "Debt to Assets": f10_indicator['debt_to_assets'],
            "BZ_Main": mainbz['bz_item'],
            "BZ_Sales": mainbz['bz_sales'],
            "BZ_Profit": mainbz['bz_profit'],
            "BZ_Cost": mainbz['bz_cost'],
        }

        reply_text = "\n".join([f"{k}: {v}" for k, v in finance.items()])
        await update.message.reply_text(reply_text)

        # 发送下一步指令
        keyboard = [["📈Trend","📰Gain_news_about_stock"],["🧙🏻‍♀️Predict","✋🏻Another_stock"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Select：", reply_markup=reply_markup)
        return FURTHER_MORE
    except Exception as e:
        logger.error(f"获取 F10 数据时出错: {e}")
        await update.message.reply_text("Failed to get F10 data, please try again later.")
        return ConversationHandler.END


# 处理 #Another_stock 指令
async def another_stock(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Now you can enter another stock code")
    keyboard = [["/Enter_stock_code"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Click /Enter_stock_code to start", reply_markup=reply_markup)
    return ENTER_STOCK_CODE