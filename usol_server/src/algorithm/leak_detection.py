# 필요함수 import
import joblib
import numpy as np
import pandas as pd
from config import settings
from sklearn.preprocessing import StandardScaler


##########데이터전처리
# 정규화함수
def calc_harmony_freq_value(fft_org, target_harmony: float):
    harmony_freq_org_1 = int(target_harmony)
    harmony_freq_org_2 = harmony_freq_org_1 + 1
    harmony_value_org_1 = fft_org[harmony_freq_org_1]
    harmony_value_org_2 = fft_org[harmony_freq_org_2]
    target_harmony_value = harmony_value_org_1 * (
        harmony_freq_org_2 - target_harmony
    ) + harmony_value_org_2 * (target_harmony - harmony_freq_org_1)
    return target_harmony_value


def normalize_fft(fft_org: np.array, harmony_interval: float = 0.1) -> np.array:
    max_freq_org = len(fft_org)
    freq_1X = fft_org.argmax()
    cnt_harmony = int(max_freq_org / freq_1X) - 1
    unit_freq = freq_1X * harmony_interval
    freqs = [unit_freq * i for i in range(int((cnt_harmony) / harmony_interval))]
    harmony_values = [calc_harmony_freq_value(fft_org, _freq) for _freq in freqs]
    return freqs, np.array(harmony_values)


# FFT -> (3200,N)스케일링
# DBscaling으로 1x대역 맞추기
def fft_data(data) -> pd.DataFrame:
    data_fft = pd.DataFrame(data)
    index = data_fft.index
    result_log = []

    for _, row in data_fft.iterrows():
        v = np.array(row)
        v_log = np.log10(v - (min(v) - 1))
        freq, fft_normalized = normalize_fft(v_log, 0.005)
        result_log.append(fft_normalized)

    data_log = pd.DataFrame(result_log)
    data_log = data_log.drop(data_log.columns[3200:], axis=1)
    data_log.index = index
    return data_log


##########분류기 만들기
# 첨도분류기
def kurt_cal(x):
    index = x.index
    data = np.power(10, x)
    scaler = StandardScaler()
    df_data = pd.DataFrame(scaler.fit_transform(data.transpose())).transpose()
    df_data["kurt"] = df_data.iloc[:, 100:300].kurtosis(axis=1)
    df_data.index = index
    return df_data


# 누수탐지 분류기
def leak_classifier(data) -> pd.DataFrame:
    # 필요 모델 불러오기
    lgb_model_g = joblib.load(settings.MODEL_PATH_1)
    lgb_model_j = joblib.load(settings.MODEL_PATH_2)
    lgb_model_o = joblib.load(settings.MODEL_PATH_3)
    lgb_model_a = joblib.load(settings.MODEL_PATH_4)

    # 필요 항목 데이터프레임 만들기
    data = pd.DataFrame(data)
    data_drop_idx = pd.DataFrame()
    data_use = pd.DataFrame()
    data_drop_kurt = pd.DataFrame()
    data_drop_kurt1 = pd.DataFrame()
    final_data = pd.DataFrame()
    data_drop0 = pd.DataFrame()
    data_drop1 = pd.DataFrame()
    data_drop0_0 = pd.DataFrame()
    data_drop0_1 = pd.DataFrame()
    data_drop0_0_0 = pd.DataFrame()
    data_drop0_0_1 = pd.DataFrame()
    data_drop0_0_0_0 = pd.DataFrame()
    data_drop0_0_0_1 = pd.DataFrame()

    # 1x대역 최고값으로 분류
    data_drop_idx = data.loc[data[data.idxmax(axis=1) > 70].index]
    data_drop_idx["leak_pred"] = 1
    data_use = data.loc[data[data.idxmax(axis=1) <= 70].index]

    if not data_use.empty:
        data_fft = fft_data(data_use)
        data_fft = data_fft.reindex(columns=range(3200), fill_value=np.nan)

        # 1x대역 첨도값으로 분류
        kurt_data = kurt_cal(data_fft)
        data_drop_kurt = data_fft.loc[kurt_data[kurt_data["kurt"] > 16].index]
        data_drop_kurt["leak_pred"] = 0
        data_drop_kurt1 = data_fft.loc[kurt_data[kurt_data["kurt"] < 1.55].index]
        data_drop_kurt1["leak_pred"] = 1
        final_data = data_fft.drop(
            kurt_data[(kurt_data["kurt"] > 16) | (kurt_data["kurt"] < 1.55)].index
        )

    if not final_data.empty:
        # 고주파대역 분류기
        scaler = StandardScaler()
        data_scaler0 = pd.DataFrame(
            scaler.fit_transform(final_data.transpose())
        ).transpose()
        g_pred = lgb_model_g.predict(data_scaler0)
        data_drop0 = final_data[g_pred == 0]
        data_drop1 = final_data[g_pred == 1]
        data_drop1["leak_pred"] = 1

    if not data_drop0.empty:
        # 조화성분 분류기
        scaler = StandardScaler()
        data_scaler0_0 = pd.DataFrame(
            scaler.fit_transform(data_drop0.transpose())
        ).transpose()
        j_pred = lgb_model_j.predict(data_scaler0_0)
        data_drop0_0 = data_drop0[j_pred == 0]
        data_drop0_1 = data_drop0[j_pred == 1]
        data_drop0_1["leak_pred"] = 0

    if not data_drop0_0.empty:
        # 파동성분 분류기
        scaler = StandardScaler()
        data_scaler0_0_0 = pd.DataFrame(
            scaler.fit_transform(data_drop0_0.transpose())
        ).transpose()
        o_pred = lgb_model_o.predict(data_scaler0_0_0)
        data_drop0_0_0 = data_drop0_0[o_pred == 0]
        data_drop0_0_1 = data_drop0_0[o_pred == 1]
        data_drop0_0_1["leak_pred"] = 1

    # 1x대역 분류기
    if not data_drop0_0_0.empty:
        data_final = np.power(10, data_drop0_0_0)
        scaler = StandardScaler()
        data_final = pd.DataFrame(
            scaler.fit_transform(data_final.transpose())
        ).transpose()
        data_final = data_final.iloc[:, 100:300]
        a_pred = lgb_model_a.predict(data_final)
        data_drop0_0_0_0 = data_drop0_0_0[a_pred == 0]
        data_drop0_0_0_1 = data_drop0_0_0[a_pred == 1]
        data_drop0_0_0_0["leak_pred"] = 0
        data_drop0_0_0_1["leak_pred"] = 1

    leak_result = pd.concat(
        [
            data_drop_idx,
            data_drop_kurt,
            data_drop_kurt1,
            data_drop1,
            data_drop0_1,
            data_drop0_0_1,
            data_drop0_0_0_0,
            data_drop0_0_0_1,
        ],
        axis=0,
    )
    leak_result = leak_result["leak_pred"].to_frame()
    # result.index.name = "name"
    return leak_result.sort_index()


###########################################################################################################
###########################################################################################################
###########################################################################################################


### 거리 분류기
def dist_classifier(leak_result, data) -> pd.DataFrame:
    data = pd.DataFrame(data)
    uncheck_dist = leak_result[leak_result["leak_pred"] == 0]
    uncheck_dist["dist_pred"] = "not_leak"
    check_dist = leak_result[leak_result["leak_pred"] == 1]
    check_dist_data = data.loc[check_dist.index]

    # 1x대역의 위치에 따른 1차 분류
    if not check_dist_data.empty:
        max_idx = check_dist_data[check_dist_data.idxmax(axis=1) > 70].index.tolist()
        drop_data = check_dist_data.drop(max_idx)
    else:
        max_idx = []
        drop_data = check_dist_data

    # 1x대역의 값으로 전체값을 나눈후 고주파구간 분류
    if not drop_data.empty:
        drop_data_normalize = fft_data(drop_data)
        scaler = StandardScaler()
        df_data = pd.DataFrame(
            scaler.fit_transform(drop_data_normalize.iloc[:, 1:].transpose())
        ).transpose()
        df_data.index = drop_data_normalize.index

        rr = []
        for _, row in df_data.iterrows():
            r = row / row[199]
            rr.append(r)
        df_new = pd.DataFrame(rr)
        x_idx = df_new[df_new.iloc[:, 1500:-2].max(axis=1) >= 0.38].index.tolist()
    else:
        x_idx = []

    check_dist["dist_pred"] = False
    check_dist.loc[max_idx + x_idx, "dist_pred"] = True
    dist_result = pd.concat([uncheck_dist, check_dist], axis=0)[
        ["leak_pred", "dist_pred"]
    ]
    return dist_result.sort_index()
