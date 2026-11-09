# XGBoost回归与模型融合

## 技术实现

回归模型从车辆特征学习价格，验证集用于早停和误差计算。融合脚本对两个模型的同一SaleID结果加权平均。

## 应用思路

预测能力可作为应用的数据服务基础；当前项目仅提供离线训练和预测，不补写Agent工具封装。

## 代码解析

### 训练配置

[二手车价格预测与模型融合](../../应用侧/模型与服务示例/二手车价格预测与模型融合/案例说明.md) · [train_xgboost.py，36–50行](../../应用侧/模型与服务示例/二手车价格预测与模型融合/train_xgboost.py#L36-L50)

```python
params = {
    'objective': 'reg:squarederror',
    'learning_rate': 0.01,  # 降低学习率
    'max_depth': 6,
    'min_child_weight': 1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'n_estimators': 8000,  # 增加树的数量
    'random_state': 42,
    'eval_metric': 'mae',
    'early_stopping_rounds': 100  # 添加早停机制
}

# 创建模型
model = xgb.XGBRegressor(**params)
```

learning_rate控制每轮贡献，max_depth限制树深，subsample与colsample_bytree控制抽样，early_stopping_rounds配合验证集选择最佳迭代。

### 预测结果融合

[二手车价格预测与模型融合](../../应用侧/模型与服务示例/二手车价格预测与模型融合/案例说明.md) · [model_ensemble.py，35–56行](../../应用侧/模型与服务示例/二手车价格预测与模型融合/model_ensemble.py#L35-L56)

```python
def ensemble_predictions(xgb_pred, lgb_pred, weights=(0.5, 0.5)):
    """
    对两个模型的预测结果进行加权平均
    """
    print("\n开始模型融合...")
    print(f"XGBoost权重: {weights[0]}")
    print(f"LightGBM权重: {weights[1]}")

    # 确保权重和为1
    if abs(sum(weights) - 1.0) > 1e-6:
        raise ValueError("权重之和必须为1！")

    # 计算加权平均
    ensemble_pred = pd.DataFrame({
        'SaleID': xgb_pred['SaleID'],
        'price': weights[0] * xgb_pred['price'] + weights[1] * lgb_pred['price']
    })

    return ensemble_pred

def analyze_predictions(xgb_pred, lgb_pred, ensemble_pred):
    """
```

先检查权重和为1，再对price加权；load_predictions中先核对SaleID顺序，防止将不同车辆结果相加。

