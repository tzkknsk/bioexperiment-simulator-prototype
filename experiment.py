import pandas as pd
import torch

from botorch.test_functions import Ackley
from botorch.utils.transforms import normalize, unnormalize

# 両タブ共通の列名
CONTROL_COLUMN = "control"
NOTE_COLUMN = "note"

# design タブ
ID_COLUMN = "ID"
NO_PARAMS_DESIGN = [ID_COLUMN, CONTROL_COLUMN, NOTE_COLUMN]

# result タブ
ROUND_COLUMN = "round"
NO_PARAMS_EVAL_RESULT = [ROUND_COLUMN, CONTROL_COLUMN, NOTE_COLUMN]


def generate_experimental_result(
    df_design,
    df_result,
    Function = Ackley,
    negate = True,
    noise_std = 0.05,
    decimals = 3
):

    df_param_with_bounds = df_design.drop(columns=NO_PARAMS_DESIGN)
    df_param = df_param_with_bounds[2:]
    df_result_new = df_param.copy(deep=True)

    bounds = torch.tensor(df_param_with_bounds[:2].to_numpy())
    X = torch.tensor(df_param.to_numpy()).float()

    # 変域のチェック
    for i, (xs, bound) in enumerate(zip(X.T, bounds.T)):

        if not torch.all((xs >= bound[0]) & (xs <= bound[1])):
            raise ValueError("Not all values are within the specified bound.")

    # param_columns = df_param.columns

    # パラメータの次元数
    dim = X.shape[1]

    # round 数
    if  df_result[ROUND_COLUMN].empty:
        num_round = 1
    else:
        num_round = df_result[ROUND_COLUMN].max() + 1

    # 目的変数名
    evaluation = df_result.drop(columns=df_param.columns.to_list()+NO_PARAMS_EVAL_RESULT).columns[0]

    # 目的関数の定義
    f = Function(dim=dim, negate=negate, noise_std=noise_std)

    # ユーザ入力の変域 -> [0,1]正規化 -> Ackley の変域に変換
    X_norm = normalize(X=X, bounds=bounds)
    X_ackely_bounds = unnormalize(X_norm, bounds=f.bounds)

    _Y = f(X_ackely_bounds).unsqueeze(-1) + 30.  # それっぽい値にするために30を足す

    factor = 10 ** decimals
    Y = torch.round(_Y * factor) / factor

    df_result_new.insert(0, ROUND_COLUMN, num_round)
    df_result_new[evaluation] = Y
    df_result_new[CONTROL_COLUMN] = df_design[2:][CONTROL_COLUMN]
    df_result_new[NOTE_COLUMN] = df_design[2:][NOTE_COLUMN]

    df_result_concat = pd.concat([df_result, df_result_new]).reset_index(drop=True)
    df_result_concat[CONTROL_COLUMN] = df_result_concat[CONTROL_COLUMN].apply(
        lambda x: True if x == 1 else None
    )

    # design から control=True 以外の行を削除
    df_design_new = pd.concat([df_design[:2], df_design.iloc[2:].loc[df_design[CONTROL_COLUMN] == True]]).reset_index(drop=True)
    df_design_new[CONTROL_COLUMN] = df_design_new[CONTROL_COLUMN].apply(
        lambda x: True if x == 1 else None
    )

    return df_design_new, df_result_concat
