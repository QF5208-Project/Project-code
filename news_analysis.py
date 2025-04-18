import json

async def news_analysis(update: Update, context: CallbackContext) -> int:
    
    stock_code = context.user_data['stock_code'][0:6]
    try:
        news_df = context.user_data.get('news_df')

        
        def generate_report(news_df): 
            input_json = news_df
                    
            # 构造专业Prompt
            system_prompt = """你是一名顶级金融分析师，需要结合NLP技术和市场知识，对股票新闻进行深度分析。要求：
            1. 分析新闻主题、情感倾向、影响力
            2. 进行三级情绪分析（整体/短期/长期）
            3. 生成量化影响矩阵
            4. 提供多策略投资建议"""

                
            # 调用DeepSeek API
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input_json}
                ],
                temperature=0.2,
                max_tokens=2000
                )
                
            return response.choices[0].message.content


        await update.message.reply_text("Analyzing...")
        # 以 Markdown 格式发送
        report = generate_report(news_df)
        await update.message.reply_text(report,parse_mode="Markdown")
        keyboard = [["📈Trend","💰Finance"],["🧙🏻‍♀️Predict","✋🏻Another_Stock"],["/End"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Please select the next step", reply_markup=reply_markup)
        return FURTHER_MORE

    except Exception as e:
        logger.error(f"分析出错: {e}")
        await update.message.reply_text("Failed to do the analysis, please try again later.")
        return ConversationHandler.END




