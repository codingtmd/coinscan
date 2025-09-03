我在基于xgboost做一个对于虚拟货币价格进行预测的AI模型，用于日内交易，开盘买入，收盘卖出，每日挑选出最可能涨的股票用于交易。在研发ai模型的过程中，需要发掘面对日内交易形态有价值的特征因子。为了更好的理解当前的虚拟货币交易市场，我想对于binance上现在的现货交易币对，进行统计分析，从中找出规律。

我的实验方法如下：
1. 获取binance上的所有以usdt结尾的交易币对列表，假设该列表命名为 full_coin_list
2. 通过binance的api，获取full_coin_list中每一个coin的过去n天的交易信息，在day的维度即可， 相关的信息保存在内存里，可以是一个dict， key是symbol， value是一个data frame。n默认等于1，即过去一天。
3. 对于full_coin_list中的每一个coin，从coinmarketcap获取最新的市值信息，包括Unlocked Mkt Cap， Circulating supply/Total supply， Vol/Mkt Cap (24h)， 以及其他有价值的维度信息，etc.， 相关信息也保存到恰当的数据结构里面
4. 我们按照Unlocked Mkt Cap，视觉展示去分布结构。然后按照统计规律，决定分解值，将所有的symbol分为三组， top， mid， low。
5. 然后在每一组上，你需要用合适的方式来展示出，每一组上从binance获取的交易信息的统计特征，并发现相关性，告诉我。

你需要生成代码，并将实验结构数据输出到一个固定目录中去，然后生成实验报告。