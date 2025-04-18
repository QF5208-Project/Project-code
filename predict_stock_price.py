#import akshare as ak
import json
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
#from datetime import datetime


async def predict_stock_price(update: Update, context: CallbackContext):
    stockcode = context.user_data.get('stock_code')[0:6]
    await update.message.reply_text(f"Please wait")
    if stockcode.startswith("6"):
        stockcode = "sh" + stockcode
    elif stockcode.startswith("0") or stockcode.startswith("3"):
        stockcode = "sz" + stockcode
    else:
        # stock_code.startswith("9") or stock_code.startswith("8") or stock_code.startswith("4"):
        stockcode = "sz" + stockcode

    """
    Use data from 20220101 to 20241231 to train the model;
    The training size and test size are 80% and 20% respectively.
    """
    #data for training
    stockdata = ak.stock_zh_a_hist_tx(symbol=stockcode, start_date="20220101", end_date="20241231", adjust="qfq")

    closedata = stockdata[['close']].values

    #normalization
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(closedata)


    #modeling
    def create_dataset(data, time_step=60):
        X, y = [], []
        for i in range(len(data) - time_step - 1):
            X.append(data[i:(i + time_step), 0])  # 假设只使用收盘价
            y.append(data[i + time_step, 0])
        return np.array(X), np.array(y)
    

    # Divide the data into training and testing sets
    train_size = int(len(scaled_data) * 0.8)
    test_size = len(scaled_data) - train_size
    train_data, test_data = scaled_data[0:train_size], scaled_data[train_size:]

    # create the dataset
    X_train, y_train = create_dataset(train_data, time_step=60)
    X_test, y_test = create_dataset(test_data, time_step=60)
    
    # The model is a 2-layer LSTM network
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))  # 预测一个值（收盘价）

    model.compile(optimizer='adam', loss='mean_squared_error')

    # reshape the data for LSTM
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))


    early_stop = EarlyStopping(monitor='val_loss', patience=10)

    # train the model
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_data=(X_test, y_test),
        verbose=1,
        callbacks=[early_stop] #使用早停法（EarlyStopping）防止过拟合
    )

    train_predict = model.predict(X_train)
    test_predict = model.predict(X_test)

    # 反归一化还原数据
    train_predict = scaler.inverse_transform(train_predict)
    y_train = scaler.inverse_transform([y_train])
    test_predict = scaler.inverse_transform(test_predict)
    y_test = scaler.inverse_transform([y_test])

    y_test = y_test.T

    #evaluate model
    rmse = np.sqrt(mean_squared_error(y_test, test_predict[:,0]))
    mae = mean_absolute_error(y_test, test_predict[:,0])
    relative_error = (mae / y_test.mean()) * 100


    """
    now we need to predict the next day price, using the lastest 60 days data,
    as well as the model we just trained.
    """
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
    
    def get_last_n_trading_days(n=60):
        # 获取交易日历并转换为字符串列表
        trade_date_df = ak.tool_trade_date_hist_sina()
        trade_dates = trade_date_df["trade_date"].astype(str).tolist()  # 强制转为字符串
        
        # 转换为统一的日期格式（新浪返回格式示例：2024-03-26 → 转为 20240326）
        trade_dates = [d.replace("-", "") for d in trade_dates]
        
        # 过滤未来日期并排序
        current_date_str = find_nearest_trade_date()
        
        valid_dates = [d for d in trade_dates if d <= current_date_str]
        valid_dates = sorted(valid_dates, reverse=True)[:n]  # 取最近N个
        
        return sorted(valid_dates)  # 按从早到晚排序

    def get_stock_data(symbol, n=60):
            trading_dates = get_last_n_trading_days(n)
            
            start_date = trading_dates[0]   # 起始日期（最早）
            end_date = trading_dates[-1]    # 结束日期（最晚）
            
            df = ak.stock_zh_a_hist_tx(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            return df

    new_data = get_stock_data(stockcode)
    close_new_data = new_data[['close']].values
    scaled_new_data = scaler.transform(close_new_data)

    await update.message.reply_text(f"The size of the data used to predict is {scaled_new_data.shape}")
    X_latest = scaled_new_data[-60:].reshape(1, 60, 1)  

    # 预测下一个时间步的价格（例如明天收盘价）
    predicted_scaled = model.predict(X_latest)

    # 逆归一化得到实际价格
    predicted_price = scaler.inverse_transform(predicted_scaled)
    print(f"Predicted by LTSM：{predicted_price[0][0]:.2f}")
            
    current_price = new_data['close'].values[-1]  # 当前最新价格
    predicted_price = predicted_price[0][0]

    if predicted_price > current_price * 1.02:  # 预测涨幅超过2%
        action = "Long"
    elif predicted_price < current_price * 0.98:  # 预测跌幅超过2%
        action = "Short"
    else:
        action = "Hold"  

    await update.message.reply_text(f"当前价格：{current_price:.2f}，预测价格：{predicted_price:.2f}，建议操作：{action}")


    keyboard = [["👽News_Analysis"],["📈Trend","💰Finance"],["/End","✋🏻Another_Stock"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Please select the next step", reply_markup=reply_markup)
    return FURTHER_MORE

