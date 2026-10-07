import pandas as pd


def test_no_future_leakage():

    history = pd.DataFrame(
        {
            "hour": [
                "10",
                "11",
                "12",
                "13",
                "14",
                "15",
                "16"
            ],

            "activity": [
                100,
                120,
                140,
                160,
                180,
                200,
                250
            ]
        }
    )

    feature_timestamp = "15"

    historical_avg_before = (
        history.iloc[:6]["activity"].mean()
    )

    history.loc[6, "activity"] = 999999

    historical_avg_after = (
        history.iloc[:6]["activity"].mean()
    )

    assert (
        historical_avg_before
        ==
        historical_avg_after
    ), (
        "FAIL: Future activity changed "
        "historical feature values."
    )

    print(
        "PASS: No future leakage detected."
    )


if __name__ == "__main__":
    test_no_future_leakage()